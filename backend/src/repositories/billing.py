from datetime import UTC, datetime
from typing import Sequence

from sqlalchemy import exists, select, text, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.billing import Plan, PlanFeature, PlanPrice, Subscription, WebhookEvent
from src.repositories.base import OrganizationScopedRepository, SQLResourceRepository

_CHECKOUT_LOCK_NS = 0x62696C6C  # "bill" in ASCII - namespaces checkout advisory locks

# pylint: disable=too-few-public-methods


class PlanRepository(SQLResourceRepository[Plan]):
    def __init__(self, db: AsyncSession) -> None:
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
    def __init__(self, db: AsyncSession) -> None:
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
                self.model.deleted_at.is_(None),
            )
            .limit(1)
        )
        rs = await self.db.execute(stmt)
        return rs.unique().scalar_one_or_none()

    async def get_highest_price(self) -> PlanPrice | None:
        """
        Return the active price with the highest amount that has a Stripe price ID.
        Ties are broken by taking the earliest created price (lowest id).
        """
        stmt = (
            select(self.model)
            .filter(
                self.model.is_active.is_(True),
                self.model.external_price_id.isnot(None),
                self.model.deleted_at.is_(None),
            )
            .order_by(self.model.amount.desc(), self.model.id.asc())
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

    async def has_active_subscriptions(self, plan_price_id: int) -> bool:
        """
        Returns True if any active subscription references this price.
        Any future deletion method MUST call this first and raise ValidationException
        if it returns True, to prevent orphaning active subscriptions.
        """
        stmt = select(
            exists().where(
                Subscription.plan_price_id == plan_price_id,
                Subscription.status.in_(
                    ["active", "trialing", "past_due", "incomplete"]
                ),
                Subscription.deleted_at.is_(None),
            )
        )
        rs = await self.db.execute(stmt)
        return bool(rs.scalar_one())


class PlanFeatureRepository(SQLResourceRepository[PlanFeature]):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(PlanFeature, db)

    async def get_features_for_organization(self, organization_id: int) -> set[str]:
        stmt = (
            select(PlanFeature.feature)
            .join(Plan, Plan.id == PlanFeature.plan_id)
            .join(PlanPrice, PlanPrice.plan_id == Plan.id)
            .join(Subscription, Subscription.plan_price_id == PlanPrice.id)
            .where(
                Subscription.organization_id == organization_id,
                Subscription.status.in_(["active", "trialing", "past_due", "paused"]),
                Subscription.deleted_at.is_(None),
            )
        )
        rs = await self.db.execute(stmt)
        return set(rs.scalars().all())


class SubscriptionRepository(OrganizationScopedRepository[Subscription]):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(Subscription, db)

    async def get_active_for_organization(
        self, organization_id: int
    ) -> Subscription | None:
        stmt = (
            select(self.model)
            .filter(
                self.model.organization_id == organization_id,
                self.model.status.in_(
                    ["active", "trialing", "past_due", "incomplete", "paused"]
                ),
                self.model.deleted_at.is_(None),
            )
            .order_by(self.model.id.desc())
            .limit(1)
        )
        rs = await self.db.execute(stmt)
        return rs.unique().scalar_one_or_none()

    async def get_active_for_organization_locked(
        self, organization_id: int
    ) -> Subscription | None:
        """
        Same as get_active_for_organization but acquires a row lock (SELECT FOR UPDATE)
        Use this before any write that depends on
        the subscription not changing concurrently
        """
        stmt = (
            select(self.model)
            .filter(
                self.model.organization_id == organization_id,
                self.model.status.in_(
                    ["active", "trialing", "past_due", "incomplete", "paused"]
                ),
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
        # Intentionally bypasses organization scope - needed in webhook handler
        stmt = select(self.model).filter(
            self.model.external_subscription_id == external_id,
            self.model.deleted_at.is_(None),
        )
        rs = await self.db.execute(stmt)
        return rs.unique().scalar_one_or_none()

    async def get_by_external_subscription_id_locked(
        self, external_id: str
    ) -> Subscription | None:
        """
        Like get_by_external_subscription_id but acquires a row lock (SELECT FOR UPDATE)
        Use in webhook handlers to prevent concurrent event processing on the same row
        """
        stmt = (
            select(self.model)
            .filter(
                self.model.external_subscription_id == external_id,
                self.model.deleted_at.is_(None),
            )
            .with_for_update()
        )
        rs = await self.db.execute(stmt)
        return rs.unique().scalar_one_or_none()

    async def get_stale_incomplete_subscriptions(
        self, older_than: datetime
    ) -> Sequence[Subscription]:
        """
        Returns incomplete subscriptions with no external_subscription_id that are
        older than the given threshold. These are checkout sessions that were never
        completed and whose expiry webhook was missed or permanently failed.
        """
        stmt = select(self.model).filter(
            self.model.status == "incomplete",
            self.model.external_subscription_id.is_(None),
            self.model.created_at < older_than,
            self.model.deleted_at.is_(None),
        )
        rs = await self.db.execute(stmt)
        return rs.unique().scalars().all()

    async def bulk_cancel_stale_incomplete(self, older_than: datetime) -> int:
        stmt = (
            update(self.model)
            .where(
                self.model.status == "incomplete",
                self.model.external_subscription_id.is_(None),
                self.model.created_at < older_than,
                self.model.deleted_at.is_(None),
            )
            .values(status="canceled", canceled_at=datetime.now(UTC))
        )
        rs = await self.db.execute(stmt)
        return rs.rowcount  # type: ignore[attr-defined]

    async def acquire_checkout_lock(self, organization_id: int) -> None:
        await self.db.execute(
            text("SELECT pg_advisory_xact_lock(:tid)"),
            {"tid": organization_id ^ _CHECKOUT_LOCK_NS},
        )

    async def create_or_get_active(
        self,
        organization_id: int,
        plan_price_id: int | None,
        status: str,
    ) -> Subscription | None:
        try:
            async with self.db.begin_nested():
                return await self.create(
                    organization_id=organization_id,
                    plan_price_id=plan_price_id,
                    status=status,
                )
        except IntegrityError:
            return await self.get_active_for_organization_locked(organization_id)


class WebhookEventRepository(SQLResourceRepository[WebhookEvent]):
    def __init__(self, db: AsyncSession) -> None:
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
        self,
        external_event_id: str,
        event_type: str,
    ) -> tuple[WebhookEvent | None, bool]:
        """
        Atomically ensure a webhook event record exists, then claim it for
        processing. Returns (record, should_process).

        should_process=False means either the event was already processed/processing
        by another worker and this request should skip it.

        Uses INSERT ON CONFLICT DO NOTHING to create the row, then an atomic
        UPDATE … SET status='processing' RETURNING * to claim it. Only the worker
        whose UPDATE affects a row will proceed; concurrent workers get 0 rows back
        and skip processing entirely.
        """
        now = datetime.now(UTC)

        # 1. Ensure the row exists (idempotent)
        insert_stmt = (
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
        await self.db.execute(insert_stmt)
        await self.db.flush()

        # 2. Atomically claim the event - only one worker wins this UPDATE
        claim_stmt = (
            update(WebhookEvent)
            .where(
                WebhookEvent.external_event_id == external_event_id,
                WebhookEvent.status.in_(["received", "failed"]),
            )
            .values(status="processing", updated_at=now)
            .returning(WebhookEvent)
            .execution_options(synchronize_session=False)
        )
        result = await self.db.execute(claim_stmt)
        await self.db.flush()
        claimed = result.unique().scalar_one_or_none()

        if claimed is None:
            # Row is already "processing" or "processed" - another worker has it
            existing = await self.get_by_external_event_id(external_event_id)
            return existing, False

        return claimed, True

    async def mark_processed(self, event: WebhookEvent) -> WebhookEvent:
        return await self.update(
            event,
            status="processed",
            processed_at=datetime.now(UTC),
        )

    async def mark_failed(self, event: WebhookEvent, error: str) -> WebhookEvent:
        return await self.update(event, status="failed", error=error)
