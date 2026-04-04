from datetime import UTC, datetime
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from src.models.billing import Plan, PlanPrice, Subscription, WebhookEvent
from src.repositories.base import SQLResourceRepository, TenantScopedRepository

# pylint: disable=too-few-public-methods


class PlanRepository(SQLResourceRepository[Plan]):
    def __init__(self, db):  # type: ignore[no-untyped-def]
        super().__init__(Plan, db)

    async def get_by_external_product_id(self, external_id: str) -> Plan | None:
        rs = await self.filter_by(external_product_id=external_id)
        return rs[0] if rs else None

    async def get_active_plans(self) -> Sequence[Plan]:
        stmt = select(self.model).filter(
            self.model.is_active.is_(True),
            self.model.deleted_at.is_(None),
        )
        rs = await self.db.execute(stmt)
        return rs.unique().scalars().all()


class PlanPriceRepository(SQLResourceRepository[PlanPrice]):
    def __init__(self, db):  # type: ignore[no-untyped-def]
        super().__init__(PlanPrice, db)

    async def get_by_plan(self, plan_id: int) -> Sequence[PlanPrice]:
        return await self.filter_by(plan_id=plan_id)

    async def get_by_external_price_id(self, external_id: str) -> PlanPrice | None:
        rs = await self.filter_by(external_price_id=external_id)
        return rs[0] if rs else None

    async def get_free_price(self) -> PlanPrice | None:
        stmt = (
            select(self.model)
            .filter(
                self.model.amount == 0,
                self.model.is_active.is_(True),
                self.model.external_price_id.isnot(None),
                self.model.deleted_at.is_(None),
            )
            .limit(1)
        )
        rs = await self.db.execute(stmt)
        return rs.unique().scalar_one_or_none()

    async def get_active_by_plan(self, plan_id: int) -> Sequence[PlanPrice]:
        stmt = select(self.model).filter(
            self.model.plan_id == plan_id,
            self.model.is_active.is_(True),
            self.model.deleted_at.is_(None),
        )
        rs = await self.db.execute(stmt)
        return rs.unique().scalars().all()


class SubscriptionRepository(TenantScopedRepository[Subscription]):
    def __init__(self, db):  # type: ignore[no-untyped-def]
        super().__init__(Subscription, db)

    async def get_active_for_tenant(self, tenant_id: int) -> Subscription | None:
        stmt = (
            select(self.model)
            .filter(
                self.model.tenant_id == tenant_id,
                self.model.status.in_(["active", "trialing", "past_due", "incomplete"]),
                self.model.deleted_at.is_(None),
            )
            .order_by(self.model.id.desc())
            .limit(1)
        )
        rs = await self.db.execute(stmt)
        return rs.unique().scalar_one_or_none()

    async def get_active_for_tenant_locked(self, tenant_id: int) -> Subscription | None:
        """Same as get_active_for_tenant but acquires a row lock (SELECT FOR UPDATE).
        Use this before any write that depends on the subscription not changing concurrently."""
        stmt = (
            select(self.model)
            .filter(
                self.model.tenant_id == tenant_id,
                self.model.status.in_(["active", "trialing", "past_due", "incomplete"]),
                self.model.deleted_at.is_(None),
            )
            .order_by(self.model.id.desc())
            .limit(1)
            .with_for_update()
        )
        rs = await self.db.execute(stmt)
        return rs.unique().scalar_one_or_none()

    async def get_by_external_subscription_id(
        self, external_id: str
    ) -> Subscription | None:
        # Intentionally bypasses tenant scope - needed in webhook handler
        stmt = select(self.model).filter(
            self.model.external_subscription_id == external_id,
            self.model.deleted_at.is_(None),
        )
        rs = await self.db.execute(stmt)
        return rs.unique().scalar_one_or_none()

    async def get_by_external_customer_id(
        self, external_customer_id: str
    ) -> Subscription | None:
        # Intentionally bypasses tenant scope - needed in webhook handler
        stmt = (
            select(self.model)
            .filter(
                self.model.external_customer_id == external_customer_id,
                self.model.deleted_at.is_(None),
            )
            .order_by(self.model.id.desc())
            .limit(1)
        )
        rs = await self.db.execute(stmt)
        return rs.unique().scalar_one_or_none()

    async def get_any_external_customer_id(self, tenant_id: int) -> str | None:
        """Return the first known Stripe customer ID for this tenant, regardless of status.
        Used to avoid creating duplicate Stripe customers via the eventually-consistent
        Stripe Search API."""
        stmt = (
            select(self.model.external_customer_id)
            .filter(
                self.model.tenant_id == tenant_id,
                self.model.external_customer_id.isnot(None),
                self.model.deleted_at.is_(None),
            )
            .order_by(self.model.id.desc())
            .limit(1)
        )
        rs = await self.db.execute(stmt)
        return rs.scalar_one_or_none()


class WebhookEventRepository(SQLResourceRepository[WebhookEvent]):
    def __init__(self, db):  # type: ignore[no-untyped-def]
        super().__init__(WebhookEvent, db)

    async def get_by_external_event_id(
        self, external_event_id: str
    ) -> WebhookEvent | None:
        stmt = select(self.model).filter(
            self.model.external_event_id == external_event_id
        )
        rs = await self.db.execute(stmt)
        return rs.unique().scalar_one_or_none()

    async def get_or_create_received(
        self, external_event_id: str, event_type: str
    ) -> tuple[WebhookEvent, bool]:
        """
        Atomically ensure a webhook event record exists.
        Returns (record, should_process) where should_process=False means
        the event was already processed and can be skipped.
        Uses INSERT ON CONFLICT DO NOTHING to avoid TOCTOU races under
        concurrent Stripe delivery of the same event ID.
        """
        now = datetime.now(UTC)
        stmt = (
            pg_insert(WebhookEvent)
            .values(
                external_event_id=external_event_id,
                event_type=event_type,
                status="received",
                created_at=now,
                updated_at=now,
            )
            .on_conflict_do_nothing(index_elements=["external_event_id"])
        )
        await self.db.execute(stmt)
        await self.db.flush()

        record = await self.get_by_external_event_id(external_event_id)
        should_process = record is not None and record.status != "processed"
        return record, should_process  # type: ignore[return-value]

    async def mark_processed(self, event: WebhookEvent) -> WebhookEvent:
        return await self.update(event, status="processed")

    async def mark_failed(self, event: WebhookEvent, error: str) -> WebhookEvent:
        return await self.update(event, status="failed", error=error)
