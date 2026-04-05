import logging
from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import Depends
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from src.billing.dependencies import BillingProviderDep
from src.core.config import settings
from src.core.dependencies import authenticate
from src.core.exceptions import (
    AlreadyExistsException,
    BillingProviderException,
    NotFoundException,
    ValidationException,
)
from src.core.security import Auth
from src.enums import ErrorCode
from src.models.billing import Subscription
from src.repositories.repository_manager import RepositoryManager
from src.schemas.billing import (
    CheckoutIn,
    CheckoutOut,
    CustomerPortalOut,
    PlanOut,
    SubscriptionOut,
    SwitchPlanIn,
)
from src.services.base import BaseService

# pylint: disable=too-many-arguments,too-many-positional-arguments


class PlanService(BaseService):
    def __init__(
        self,
        repos: Annotated[RepositoryManager, Depends()],
        provider: BillingProviderDep,
    ) -> None:
        self.provider = provider
        super().__init__(repos)

    async def get_plan(self, plan_id: int) -> PlanOut:
        plan = await self.repos.plan.get(plan_id)
        if not plan:
            raise NotFoundException(f"Plan not found. [plan_id={plan_id}]")
        return PlanOut.model_validate(plan)

    async def get_all_plans(self) -> list[PlanOut]:
        plans = await self.repos.plan.get_active_plans()
        return [PlanOut.model_validate(p) for p in plans]


class SubscriptionService(BaseService):
    def __init__(
        self,
        repos: Annotated[RepositoryManager, Depends()],
        provider: BillingProviderDep,
        current_user: Annotated[Auth, Depends(authenticate)],
    ) -> None:
        self.provider = provider
        self.current_user = current_user
        super().__init__(repos)
        self.repos.subscription.set_tenant_scope(current_user.tenant_id)

    async def start_checkout(self, schema_in: CheckoutIn) -> CheckoutOut:
        price = await self.repos.plan_price.get(schema_in.plan_price_id)
        if not price or not price.is_active:
            raise NotFoundException(
                f"Plan price not found or inactive. [id={schema_in.plan_price_id}]"
            )
        if not price.external_price_id:
            raise NotFoundException("Plan price is not synced with billing provider.")

        existing = await self.repos.subscription.get_active_for_tenant_locked(
            self.current_user.tenant_id
        )
        if existing and existing.status in ("active", "trialing"):
            raise AlreadyExistsException(
                "Tenant already has an active subscription.",
                error_code=ErrorCode.SUBSCRIPTION_ALREADY_ACTIVE,
            )

        # Get or create provider customer
        tenant = await self.repos.tenant.get(self.current_user.tenant_id)
        if not tenant:
            raise NotFoundException("Tenant not found.")

        # Acquire a transaction-scoped advisory lock keyed on tenant_id to prevent
        # two concurrent first-time checkouts from creating duplicate Stripe customers.
        # The lock is automatically released when the transaction commits or rolls back.
        await self.repos.subscription.db.execute(
            text("SELECT pg_advisory_xact_lock(:tid)"),
            {"tid": self.current_user.tenant_id},
        )

        # Re-check after acquiring the lock - a concurrent request may have inserted a
        # subscription row between our initial check and the lock acquisition.
        existing = await self.repos.subscription.get_active_for_tenant_locked(
            self.current_user.tenant_id
        )
        if existing and existing.status in ("active", "trialing"):
            raise AlreadyExistsException(
                "Tenant already has an active subscription.",
                error_code=ErrorCode.SUBSCRIPTION_ALREADY_ACTIVE,
            )

        external_customer_id: str | None = None
        if existing and existing.external_customer_id:
            external_customer_id = existing.external_customer_id
        else:
            # Check all subscriptions for this tenant (including canceled) before
            # calling Stripe Search, which is eventually consistent and can create
            # duplicate customers under concurrent requests.
            external_customer_id = (
                await self.repos.subscription.get_any_external_customer_id(
                    self.current_user.tenant_id
                )
            )
            if not external_customer_id:
                external_customer_id = await self.provider.get_or_create_customer(
                    tenant_id=self.current_user.tenant_id,
                    tenant_name=tenant.name,
                    email=self.current_user.email,
                )

        metadata = {
            "tenant_id": str(self.current_user.tenant_id),
            "plan_price_id": str(price.id),
        }
        result = await self.provider.create_checkout_session(
            external_customer_id=external_customer_id,
            external_price_id=price.external_price_id,
            amount=price.amount,
            success_url=settings.billing_success_url,
            cancel_url=settings.billing_cancel_url,
            metadata=metadata,
        )

        # Upsert subscription row
        if existing:
            await self.repos.subscription.update(
                existing,
                plan_price_id=price.id,
                external_customer_id=external_customer_id,
                status="incomplete",
            )
        else:
            try:
                await self.repos.subscription.create(
                    tenant_id=self.current_user.tenant_id,
                    plan_price_id=price.id,
                    external_customer_id=external_customer_id,
                    status="incomplete",
                )
            except IntegrityError as exc:
                raise AlreadyExistsException(
                    "Tenant already has an active subscription.",
                    error_code=ErrorCode.SUBSCRIPTION_ALREADY_ACTIVE,
                ) from exc

        return CheckoutOut(
            checkout_url=result.checkout_url,
            external_session_id=result.external_session_id,
        )

    async def get_current_subscription(self) -> SubscriptionOut:
        sub = await self.repos.subscription.get_active_for_tenant(
            self.current_user.tenant_id
        )
        if not sub:
            raise NotFoundException(
                "No active subscription found for this tenant.",
                error_code=ErrorCode.SUBSCRIPTION_NOT_FOUND,
            )
        return SubscriptionOut.model_validate(sub)

    async def cancel_subscription(self) -> SubscriptionOut:
        sub = await self._get_active_subscription()
        if not sub.external_subscription_id:
            # Checkout was never completed - cancel locally, nothing to do in Stripe
            sub = await self.repos.subscription.update(
                sub,
                status="canceled",
                canceled_at=datetime.now(UTC),
            )
            return SubscriptionOut.model_validate(sub)

        ext_sub = await self.provider.cancel_subscription(sub.external_subscription_id)
        sub = await self.repos.subscription.update(
            sub,
            cancel_at_period_end=ext_sub.cancel_at_period_end,
            status=ext_sub.status,
        )
        return SubscriptionOut.model_validate(sub)

    async def resume_subscription(self) -> SubscriptionOut:
        sub = await self._get_active_subscription()
        if not sub.cancel_at_period_end:
            raise ValidationException("Subscription is not scheduled for cancellation.")
        if not sub.external_subscription_id:
            raise ValidationException(
                "Subscription is not yet active in billing provider."
            )

        ext_sub = await self.provider.resume_subscription(sub.external_subscription_id)
        sub = await self.repos.subscription.update(
            sub,
            cancel_at_period_end=ext_sub.cancel_at_period_end,
            status=ext_sub.status,
        )
        return SubscriptionOut.model_validate(sub)

    async def switch_plan(self, schema_in: SwitchPlanIn) -> SubscriptionOut | CheckoutOut:
        sub = await self._get_active_subscription()
        if not sub.external_subscription_id:
            raise ValidationException(
                "Your previous checkout is still pending. "
                "Please cancel it before switching plans."
            )

        price = await self.repos.plan_price.get(schema_in.plan_price_id)
        if not price or not price.is_active:
            raise NotFoundException(
                f"Plan price not found or inactive. [id={schema_in.plan_price_id}]"
            )
        if not price.external_price_id:
            raise NotFoundException("Plan price is not synced with billing provider.")

        if sub.plan_price_id == price.id:
            raise ValidationException("Subscription is already on this plan.")

        old_amount = sub.plan_price.amount if sub.plan_price else 0

        # Upgrading from a free plan to a paid plan requires collecting payment details.
        # Route through the checkout flow so the user can enter their credit card.
        if old_amount == 0 and price.amount > 0:
            if not sub.external_customer_id:
                raise ValidationException("No billing customer found for this tenant.")

            metadata = {
                "tenant_id": str(self.current_user.tenant_id),
                "plan_price_id": str(price.id),
            }
            result = await self.provider.create_checkout_session(
                external_customer_id=sub.external_customer_id,
                external_price_id=price.external_price_id,
                amount=price.amount,
                success_url=settings.billing_success_url,
                cancel_url=settings.billing_cancel_url,
                metadata=metadata,
            )
            await self.repos.subscription.update(
                sub,
                plan_price_id=price.id,
                status="incomplete",
            )
            return CheckoutOut(
                checkout_url=result.checkout_url,
                external_session_id=result.external_session_id,
            )

        skip_proration = price.amount == 0
        ext_sub = await self.provider.switch_subscription_price(
            sub.external_subscription_id,
            price.external_price_id,
            skip_proration=skip_proration,
        )
        sub = await self.repos.subscription.update(
            sub,
            plan_price_id=price.id,
            status=ext_sub.status,
        )
        return SubscriptionOut.model_validate(sub)

    async def get_customer_portal_url(self) -> CustomerPortalOut:
        sub = await self._get_active_subscription()
        if not sub.external_customer_id:
            raise ValidationException("No billing customer found for this tenant.")

        result = await self.provider.get_customer_portal_url(
            external_customer_id=sub.external_customer_id,
            return_url=settings.billing_portal_return_url,
        )
        return CustomerPortalOut(portal_url=result.portal_url)

    async def _get_active_subscription(self) -> Subscription:
        sub = await self.repos.subscription.get_active_for_tenant_locked(
            self.current_user.tenant_id
        )
        if not sub:
            raise NotFoundException(
                "No active subscription found for this tenant.",
                error_code=ErrorCode.SUBSCRIPTION_NOT_FOUND,
            )
        return sub


class WebhookService:  # pylint: disable=too-few-public-methods
    def __init__(
        self,
        repos: Annotated[RepositoryManager, Depends()],
        provider: BillingProviderDep,
    ) -> None:
        self.repos = repos
        self.provider = provider

    async def process_webhook(self, payload: bytes, sig_header: str) -> bool:
        webhook = self.provider.construct_webhook_event(payload, sig_header)

        (
            event_record,
            should_process,
        ) = await self.repos.webhook_event.get_or_create_received(
            webhook.external_event_id, webhook.event_type
        )
        if not should_process:
            return True

        if event_record is None:
            return True
        log = logging.getLogger(__name__)

        try:
            await self._dispatch(webhook.event_type, webhook.raw)
        except BillingProviderException as exc:
            # Transient provider error - let Stripe retry
            await self.repos.webhook_event.mark_failed(event_record, str(exc))
            return False
        except Exception as exc:  # pylint: disable=broad-except
            # Permanent error (bug, unexpected data)
            # log and ack to stop infinite retries
            log.error(
                "Permanent webhook handler failure [event_id=%s event_type=%s]: %s",
                webhook.external_event_id,
                webhook.event_type,
                exc,
                exc_info=True,
            )
            await self.repos.webhook_event.mark_failed(
                event_record, f"permanent: {exc}"
            )
            return True

        await self.repos.webhook_event.mark_processed(event_record)
        return True

    async def _dispatch(self, event_type: str, raw: dict) -> None:
        handlers = {
            "checkout.session.completed": self._handle_checkout_completed,
            "checkout.session.expired": self._handle_checkout_session_expired,
            "subscription.created": self._handle_subscription_created,
            "subscription.updated": self._handle_subscription_updated,
            "subscription.deleted": self._handle_subscription_deleted,
            "invoice.payment_failed": self._handle_invoice_payment_failed,
            "invoice.payment_succeeded": self._handle_invoice_payment_succeeded,
            "invoice.payment_action_required": self._handle_invoice_payment_action_required,  # pylint: disable=line-too-long
            "invoice.marked_uncollectible": self._handle_invoice_marked_uncollectible,
            "product.created": self._handle_product_created,
            "product.updated": self._handle_product_updated,
            "price.created": self._handle_price_created,
            "price.updated": self._handle_price_updated,
        }
        handler = handlers.get(event_type)
        if handler:
            await handler(raw)

    async def _handle_checkout_completed(self, raw: dict) -> None:
        obj = raw["data"]["object"]
        subscription_id: str | None = obj.get("subscription")
        customer_id: str | None = obj.get("customer")
        metadata: dict = obj.get("metadata", {})

        if not subscription_id or not customer_id:
            return

        # Try to find existing subscription row by customer or metadata tenant_id
        sub = await self.repos.subscription.get_by_external_customer_id_locked(
            customer_id
        )
        if not sub:
            tenant_id_str = metadata.get("tenant_id")
            if tenant_id_str:
                sub = await self.repos.subscription.get_active_for_tenant_locked(
                    int(tenant_id_str)
                )

        if not sub:
            return

        plan_price_id_str = metadata.get("plan_price_id")
        old_external_subscription_id = sub.external_subscription_id
        updates: dict = {
            "external_subscription_id": subscription_id,
            "external_customer_id": customer_id,
        }
        if sub.status == "incomplete":
            updates["status"] = "active"
        if plan_price_id_str:
            updates["plan_price_id"] = int(plan_price_id_str)

        await self.repos.subscription.update(sub, **updates)

        # If this checkout replaced a free plan subscription, cancel the old Stripe
        # subscription immediately so it doesn't linger as an orphaned $0 subscription.
        if (
            old_external_subscription_id
            and old_external_subscription_id != subscription_id
        ):
            log = logging.getLogger(__name__)
            try:
                await self.provider.delete_subscription(old_external_subscription_id)
            except BillingProviderException as exc:
                log.warning(
                    "Failed to cancel old subscription after checkout [old_sub=%s]: %s",
                    old_external_subscription_id,
                    exc,
                )

    async def _handle_subscription_updated(self, raw: dict) -> None:
        obj = raw["data"]["object"]
        sub_id: str = obj["id"]

        sub = await self.repos.subscription.get_by_external_subscription_id_locked(
            sub_id
        )
        if not sub:
            return

        def _ts(ts: int | None):  # type: ignore[no-untyped-def]
            return datetime.fromtimestamp(ts, tz=UTC) if ts else None

        def _period(field: str) -> int | None:
            val = obj.get(field)
            if val:
                return val  # type: ignore[no-any-return]
            items = obj.get("items", {}).get("data", [])
            return items[0].get(field) if items else None

        updates: dict = {
            "status": obj.get("status", sub.status),
            "current_period_start": _ts(_period("current_period_start")),
            "current_period_end": _ts(_period("current_period_end")),
            "canceled_at": _ts(obj.get("canceled_at")),
        }
        # Only update cancel_at_period_end when explicitly present in the event
        # defaulting to False would silently un-schedule pending cancellations.
        if "cancel_at_period_end" in obj:
            updates["cancel_at_period_end"] = obj["cancel_at_period_end"]

        # Check if price changed (e.g. plan upgrade via portal)
        items = obj.get("items", {}).get("data", [])
        if items:
            new_price_id: str | None = (items[0].get("price") or {}).get("id")
            if (
                new_price_id
                and sub.plan_price
                and sub.plan_price.external_price_id != new_price_id
            ):
                new_price = await self.repos.plan_price.get_by_external_price_id(
                    new_price_id
                )
                if new_price:
                    updates["plan_price_id"] = new_price.id

        await self.repos.subscription.update(sub, **updates)

    async def _handle_subscription_deleted(self, raw: dict) -> None:
        obj = raw["data"]["object"]
        sub_id: str = obj["id"]

        sub = await self.repos.subscription.get_by_external_subscription_id_locked(
            sub_id
        )
        if not sub:
            return

        canceled_at_ts = obj.get("canceled_at")
        updates: dict = {"status": "canceled"}
        if canceled_at_ts:
            updates["canceled_at"] = datetime.fromtimestamp(canceled_at_ts, tz=UTC)
        elif not sub.canceled_at:
            # Stripe omitted the timestamp - fall back to now rather than nulling it
            updates["canceled_at"] = datetime.now(UTC)
        await self.repos.subscription.update(sub, **updates)

    async def _handle_invoice_payment_failed(self, raw: dict) -> None:
        obj = raw["data"]["object"]
        sub_id: str | None = obj.get("subscription")
        if not sub_id:
            return

        sub = await self.repos.subscription.get_by_external_subscription_id_locked(
            sub_id
        )
        if not sub:
            return

        await self.repos.subscription.update(sub, status="past_due")

    async def _handle_invoice_payment_succeeded(self, raw: dict) -> None:
        obj = raw["data"]["object"]
        sub_id: str | None = obj.get("subscription")
        if not sub_id:
            return

        sub = await self.repos.subscription.get_by_external_subscription_id_locked(
            sub_id
        )
        if not sub:
            return

        # Refresh period dates from the subscription lines if available
        lines = obj.get("lines", {}).get("data", [])
        updates: dict = {}
        if sub.status not in ("canceled",):
            updates["status"] = "active"
        if lines:
            period = lines[0].get("period", {})
            if period.get("start"):
                updates["current_period_start"] = datetime.fromtimestamp(
                    period["start"], tz=UTC
                )
            if period.get("end"):
                updates["current_period_end"] = datetime.fromtimestamp(
                    period["end"], tz=UTC
                )

        await self.repos.subscription.update(sub, **updates)

    async def _handle_subscription_created(self, raw: dict) -> None:
        obj = raw["data"]["object"]
        sub_id: str = obj["id"]

        sub = await self.repos.subscription.get_by_external_subscription_id_locked(
            sub_id
        )
        if not sub:
            # subscription.created fires before checkout.session.completed, so
            # external_subscription_id is not yet set - fall back to customer lookup
            customer_id: str | None = obj.get("customer")
            if customer_id:
                sub = await self.repos.subscription.get_by_external_customer_id_locked(
                    customer_id
                )
        if not sub:
            return

        def _ts(ts: int | None) -> datetime | None:
            return datetime.fromtimestamp(ts, tz=UTC) if ts else None

        def _period(field: str) -> int | None:
            val = obj.get(field)
            if val:
                return val
            items = obj.get("items", {}).get("data", [])
            return items[0].get(field) if items else None

        updates: dict = {
            "external_subscription_id": sub_id,
            "status": obj.get("status", sub.status),
            "cancel_at_period_end": obj.get("cancel_at_period_end", False),
            "current_period_start": _ts(_period("current_period_start")),
            "current_period_end": _ts(_period("current_period_end")),
            "canceled_at": _ts(obj.get("canceled_at")),
        }

        items = obj.get("items", {}).get("data", [])
        if items:
            new_price_id: str | None = (items[0].get("price") or {}).get("id")
            if new_price_id:
                new_price = await self.repos.plan_price.get_by_external_price_id(
                    new_price_id
                )
                if new_price:
                    updates["plan_price_id"] = new_price.id

        await self.repos.subscription.update(sub, **updates)

    async def _handle_checkout_session_expired(self, raw: dict) -> None:
        obj = raw["data"]["object"]
        customer_id: str | None = obj.get("customer")
        metadata: dict = obj.get("metadata", {})

        sub = None
        if customer_id:
            sub = await self.repos.subscription.get_by_external_customer_id_locked(
                customer_id
            )
        if not sub:
            tenant_id_str = metadata.get("tenant_id")
            if tenant_id_str:
                sub = await self.repos.subscription.get_active_for_tenant_locked(
                    int(tenant_id_str)
                )

        if not sub or sub.status != "incomplete":
            return

        await self.repos.subscription.update(
            sub, status="canceled", canceled_at=datetime.now(UTC)
        )

    async def _handle_invoice_payment_action_required(self, raw: dict) -> None:
        obj = raw["data"]["object"]
        sub_id: str | None = obj.get("subscription")
        if not sub_id:
            return

        sub = await self.repos.subscription.get_by_external_subscription_id_locked(
            sub_id
        )
        if not sub:
            return

        await self.repos.subscription.update(sub, status="incomplete")

    async def _handle_invoice_marked_uncollectible(self, raw: dict) -> None:
        obj = raw["data"]["object"]
        sub_id: str | None = obj.get("subscription")
        if not sub_id:
            return

        sub = await self.repos.subscription.get_by_external_subscription_id_locked(
            sub_id
        )
        if not sub:
            return

        await self.repos.subscription.update(
            sub, status="canceled", canceled_at=datetime.now(UTC)
        )

    async def _handle_product_created(self, raw: dict) -> None:
        obj = raw["data"]["object"]
        external_product_id: str = obj["id"]

        plan = await self.repos.plan.get_by_external_product_id(external_product_id)
        if plan:
            return  # already tracked locally

        await self.repos.plan.create(
            name=obj.get("name", external_product_id),
            description=obj.get("description"),
            external_product_id=external_product_id,
        )

    async def _handle_product_updated(self, raw: dict) -> None:
        obj = raw["data"]["object"]
        external_product_id: str = obj["id"]

        plan = await self.repos.plan.get_by_external_product_id(external_product_id)
        if not plan:
            return

        updates: dict = {}
        if "name" in obj:
            updates["name"] = obj["name"]
        if "description" in obj:
            updates["description"] = obj.get("description")
        if "active" in obj:
            updates["is_active"] = obj["active"]
        if updates:
            await self.repos.plan.update(plan, **updates)

    async def _handle_price_created(self, raw: dict) -> None:
        obj = raw["data"]["object"]
        external_price_id: str = obj["id"]

        existing = await self.repos.plan_price.get_by_external_price_id(
            external_price_id
        )
        if existing:
            return  # already tracked locally

        external_product_id: str | None = obj.get("product")
        if not external_product_id:
            return

        plan = await self.repos.plan.get_by_external_product_id(external_product_id)
        if not plan:
            return

        recurring: dict = obj.get("recurring") or {}
        await self.repos.plan_price.create(
            plan_id=plan.id,
            amount=obj.get("unit_amount", 0),
            currency=obj.get("currency", "usd"),
            interval=recurring.get("interval", "month"),
            interval_count=recurring.get("interval_count", 1),
            external_price_id=external_price_id,
        )

    async def _handle_price_updated(self, raw: dict) -> None:
        obj = raw["data"]["object"]
        external_price_id: str = obj["id"]

        price = await self.repos.plan_price.get_by_external_price_id(external_price_id)
        if not price:
            return

        if "active" in obj:
            await self.repos.plan_price.update(price, is_active=obj["active"])

    async def cleanup_stale_checkouts(self, max_age_hours: int = 48) -> int:
        """
        Marks stale incomplete subscriptions as canceled.

        Targets rows that have no external_subscription_id (checkout was never
        completed) and are older than max_age_hours. This handles the case where
        the checkout.session.expired webhook permanently failed and the row was
        never cleaned up by the normal event flow.

        Safe to call repeatedly - rows are only updated once (incomplete → canceled).
        Intended to be called from a scheduled job, e.g. daily with max_age_hours=48.
        """
        threshold = datetime.now(UTC) - timedelta(hours=max_age_hours)
        stale = await self.repos.subscription.get_stale_incomplete_subscriptions(
            threshold
        )
        for sub in stale:
            await self.repos.subscription.update(
                sub, status="canceled", canceled_at=datetime.now(UTC)
            )
        return len(stale)
