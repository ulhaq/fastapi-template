# pylint: disable=too-many-lines
import asyncio
import logging
import math
from datetime import UTC, datetime, timedelta
from typing import Annotated, Any

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
from src.enums import ErrorCode, Permission
from src.models.billing import PlanPrice, Subscription
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
from src.services.utils import send_email

log = logging.getLogger(__name__)

# pylint: disable=too-many-arguments,too-many-positional-arguments

_CHECKOUT_LOCK_NS = 0x62696C6C  # "bill" in ASCII d- namespaces checkout advisory locks


def _ts(ts: int | None) -> datetime | None:
    return datetime.fromtimestamp(ts, tz=UTC) if ts else None


def _period(obj: dict, field: str) -> int | None:
    val = obj.get(field)
    if val:
        return val
    items = obj.get("items", {}).get("data", [])
    return items[0].get(field) if items else None


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
        if existing and existing.status in ("active", "trialing", "past_due", "paused"):
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
            {"tid": self.current_user.tenant_id ^ _CHECKOUT_LOCK_NS},
        )

        # Re-check after acquiring the lock - a concurrent request may have inserted a
        # subscription row between our initial check and the lock acquisition.
        existing = await self.repos.subscription.get_active_for_tenant_locked(
            self.current_user.tenant_id
        )
        if existing and existing.status in ("active", "trialing", "past_due", "paused"):
            raise AlreadyExistsException(
                "Tenant already has an active subscription.",
                error_code=ErrorCode.SUBSCRIPTION_ALREADY_ACTIVE,
            )

        external_customer_id = tenant.external_customer_id
        if not external_customer_id:
            external_customer_id = await self.provider.get_or_create_customer(
                tenant_id=self.current_user.tenant_id,
                tenant_name=tenant.name,
                email=self.current_user.email,
            )
            await self.repos.tenant.update(
                tenant, external_customer_id=external_customer_id
            )

        metadata = {
            "tenant_id": str(self.current_user.tenant_id),
            "plan_price_id": str(price.id),
        }
        trial_days = price.trial_period_days

        result = await self.provider.create_checkout_session(
            external_customer_id=external_customer_id,
            external_price_id=price.external_price_id,
            amount=price.amount,
            success_url=settings.billing_success_url,
            cancel_url=settings.billing_cancel_url,
            metadata=metadata,
            trial_period_days=trial_days,
        )

        # Upsert subscription row
        if existing:
            await self.repos.subscription.update(
                existing,
                plan_price_id=price.id,
                status="incomplete",
            )
        else:
            try:
                await self.repos.subscription.create(
                    tenant_id=self.current_user.tenant_id,
                    plan_price_id=price.id,
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
        result = SubscriptionOut.model_validate(sub)
        tenant = await self.repos.tenant.get(self.current_user.tenant_id)
        if tenant:
            result.has_payment_method = tenant.has_payment_method
        return result

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
            cancel_at=ext_sub.cancel_at,
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
            cancel_at=ext_sub.cancel_at,
            status=ext_sub.status,
        )
        return SubscriptionOut.model_validate(sub)

    async def switch_plan(
        self, schema_in: SwitchPlanIn
    ) -> SubscriptionOut | CheckoutOut:
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
            tenant = await self.repos.tenant.get(self.current_user.tenant_id)
            if not tenant or not tenant.external_customer_id:
                raise ValidationException("No billing customer found for this tenant.")

            # Carry over any remaining trial days from the original trial.
            # The trial is granted at registration, not per-plan, so switching to
            # the free tier and back should not forfeit unused trial time.
            trial_days: int | None = None
            if sub.trial_end:
                # Normalize to UTC-aware in case the DB driver returns a naive datetime
                trial_end = sub.trial_end
                if trial_end.tzinfo is None:
                    trial_end = trial_end.replace(tzinfo=UTC)
                now = datetime.now(UTC)
                if trial_end > now:
                    remaining = math.ceil((trial_end - now).total_seconds() / 86400)
                    if remaining > 0:
                        trial_days = remaining

            metadata = {
                "tenant_id": str(self.current_user.tenant_id),
                "plan_price_id": str(price.id),
                "old_subscription_id": sub.external_subscription_id or "",
            }
            result = await self.provider.create_checkout_session(
                external_customer_id=tenant.external_customer_id,
                external_price_id=price.external_price_id,
                amount=price.amount,
                success_url=settings.billing_success_url,
                cancel_url=settings.billing_cancel_url,
                metadata=metadata,
                trial_period_days=trial_days,
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
            new_amount=price.amount,
        )
        sub = await self.repos.subscription.update(
            sub,
            plan_price_id=price.id,
            status=ext_sub.status,
        )
        return SubscriptionOut.model_validate(sub)

    async def get_customer_portal_url(self) -> CustomerPortalOut:
        tenant = await self.repos.tenant.get(self.current_user.tenant_id)
        if not tenant or not tenant.external_customer_id:
            raise ValidationException("No billing customer found for this tenant.")

        result = await self.provider.get_customer_portal_url(
            external_customer_id=tenant.external_customer_id,
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

        log.debug("Webhook!: %s", webhook)

        (
            event_record,
            should_process,
        ) = await self.repos.webhook_event.get_or_create_received(
            webhook.external_event_id,
            webhook.event_type,
        )

        if not should_process or event_record is None:
            return True

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
            "customer.subscription.created": self._handle_subscription_created,
            "customer.subscription.updated": self._handle_subscription_updated,
            "customer.subscription.deleted": self._handle_subscription_deleted,
            "customer.subscription.trial_will_end": (
                self._handle_subscription_trial_will_end
            ),
            "customer.subscription.paused": self._handle_subscription_paused,
            "customer.subscription.resumed": self._handle_subscription_resumed,
            "invoice.payment_failed": self._handle_invoice_payment_failed,
            "invoice.payment_succeeded": self._handle_invoice_payment_succeeded,
            "invoice.payment_action_required": (
                self._handle_invoice_payment_action_required
            ),
            "invoice.marked_uncollectible": self._handle_invoice_marked_uncollectible,
            "payment_method.attached": self._handle_payment_method_attached,
            "payment_method.detached": self._handle_payment_method_detached,
            "product.created": self._handle_product_created,
            "product.updated": self._handle_product_updated,
            "price.created": self._handle_price_created,
            "price.updated": self._handle_price_updated,
        }
        handler = handlers.get(event_type)
        if handler:
            await handler(raw)

    async def _notify_payment_failed(self, sub: Subscription) -> None:
        tenant = await self.repos.tenant.get(sub.tenant_id)
        if not tenant:
            return

        for user in tenant.users:
            if not any(
                p.name == Permission.MANAGE_SUBSCRIPTION
                for role in user.roles
                for p in role.permissions
            ):
                continue

            await asyncio.to_thread(
                send_email,
                address=user.email,
                user_name=user.name,
                subject=f"Payment failed for your {settings.app_name} account",
                email_template="payment-failed",
                data={"billing_url": f"{settings.frontend_url}/settings/billing"},
            )

    async def _handle_checkout_completed(self, raw: dict) -> None:
        obj = raw["data"]["object"]
        subscription_id: str | None = obj.get("subscription")
        customer_id: str | None = obj.get("customer")
        metadata: dict = obj.get("metadata", {})

        if not subscription_id or not customer_id:
            return

        # Try to find existing subscription row by customer or metadata tenant_id
        tenant = await self.repos.tenant.get_by_external_customer_id_locked(customer_id)
        if not tenant:
            tenant_id_str = metadata.get("tenant_id")
            if tenant_id_str:
                try:
                    tenant = await self.repos.tenant.get(int(tenant_id_str))
                except ValueError:
                    log.warning(
                        "Invalid tenant_id in checkout metadata, skipping "
                        "[value=%r sub_id=%s]",
                        tenant_id_str,
                        subscription_id,
                    )

        if not tenant:
            return

        # If we fell back to the metadata lookup the tenant has no external_customer_id
        # yet. Stamp it now so future webhook events can find the tenant by customer ID.
        if not tenant.external_customer_id:
            await self.repos.tenant.update(tenant, external_customer_id=customer_id)

        sub = await self.repos.subscription.get_active_for_tenant_locked(tenant.id)
        if not sub:
            return

        plan_price_id_str = metadata.get("plan_price_id")
        old_external_subscription_id = (
            metadata.get("old_subscription_id") or sub.external_subscription_id
        )
        updates: dict = {
            "external_subscription_id": subscription_id,
        }
        if plan_price_id_str:
            try:
                updates["plan_price_id"] = int(plan_price_id_str)
            except ValueError:
                log.warning(
                    "Invalid plan_price_id in checkout metadata, skipping "
                    "[value=%r sub_id=%s]",
                    plan_price_id_str,
                    subscription_id,
                )

        await self.repos.subscription.update(sub, **updates)

        # If this checkout replaced a free plan subscription, cancel the old Stripe
        # subscription immediately so it doesn't linger as an orphaned 0 subscription.
        if (
            old_external_subscription_id
            and old_external_subscription_id != subscription_id
        ):
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

        updates: dict = {
            "status": obj.get("status", sub.status),
            "current_period_start": _ts(_period(obj, "current_period_start")),
            "current_period_end": _ts(_period(obj, "current_period_end")),
            "canceled_at": _ts(obj.get("canceled_at")),
            "cancel_at": _ts(obj.get("cancel_at")),
            "trial_end": _ts(obj.get("trial_end")),
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

    async def _handle_payment_method_attached(self, raw: dict) -> None:
        customer_id: str | None = raw["data"]["object"].get("customer")
        if not customer_id:
            return
        tenant = await self.repos.tenant.get_by_external_customer_id_locked(customer_id)
        if tenant:
            await self.repos.tenant.update(tenant, has_payment_method=True)

    async def _handle_payment_method_detached(self, raw: dict) -> None:
        # payment_method.detached clears the customer field, so we get it from
        # the previous attributes snapshot Stripe includes in the event.
        prev = raw["data"].get("previous_attributes", {})
        customer_id: str | None = raw["data"]["object"].get("customer") or prev.get(
            "customer"
        )
        if not customer_id:
            return
        tenant = await self.repos.tenant.get_by_external_customer_id_locked(customer_id)
        if tenant and tenant.has_payment_method:
            has_more = await self.provider.has_payment_method(customer_id)
            await self.repos.tenant.update(tenant, has_payment_method=has_more)

    async def _get_subscription_from_invoice(self, obj: dict) -> Subscription | None:
        parent = obj.get("parent") or {}
        sub_details = parent.get("subscription_details") or {}
        sub_id: str | None = sub_details.get("subscription") or obj.get("subscription")
        if sub_id:
            return await self.repos.subscription.get_by_external_subscription_id_locked(
                sub_id
            )
        customer_id: str | None = obj.get("customer")
        if customer_id:
            tenant = await self.repos.tenant.get_by_external_customer_id_locked(
                customer_id
            )
            if tenant:
                return await self.repos.subscription.get_active_for_tenant_locked(
                    tenant.id
                )
        return None

    async def _handle_invoice_payment_failed(self, raw: dict) -> None:
        obj = raw["data"]["object"]
        sub = await self._get_subscription_from_invoice(obj)
        if not sub:
            return
        await self._notify_payment_failed(sub)

    async def _handle_invoice_payment_succeeded(self, raw: dict) -> None:
        obj = raw["data"]["object"]
        sub = await self._get_subscription_from_invoice(obj)
        if not sub:
            return
        if sub.status in ("past_due", "incomplete"):
            await self.repos.subscription.update(sub, status="active")

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
                tenant = await self.repos.tenant.get_by_external_customer_id_locked(
                    customer_id
                )
                if tenant:
                    sub = await self.repos.subscription.get_active_for_tenant_locked(
                        tenant.id
                    )
        if not sub:
            return

        updates: dict = {
            "external_subscription_id": sub_id,
            "status": obj.get("status", sub.status),
            "cancel_at_period_end": obj.get("cancel_at_period_end", False),
            "current_period_start": _ts(_period(obj, "current_period_start")),
            "current_period_end": _ts(_period(obj, "current_period_end")),
            "canceled_at": _ts(obj.get("canceled_at")),
            "cancel_at": _ts(obj.get("cancel_at")),
            "trial_end": _ts(obj.get("trial_end")),
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
        tenant = None
        if customer_id:
            tenant = await self.repos.tenant.get_by_external_customer_id_locked(
                customer_id
            )
        if not tenant:
            tenant_id_str = metadata.get("tenant_id")
            if tenant_id_str:
                try:
                    tenant = await self.repos.tenant.get(int(tenant_id_str))
                except ValueError:
                    log.warning(
                        "Invalid tenant_id in checkout session expired metadata "
                        "[value=%r]",
                        tenant_id_str,
                    )
        if tenant:
            sub = await self.repos.subscription.get_active_for_tenant_locked(tenant.id)

        if not sub or sub.status != "incomplete":
            return

        await self.repos.subscription.update(
            sub, status="canceled", canceled_at=datetime.now(UTC)
        )

    async def _handle_invoice_payment_action_required(self, raw: dict) -> None:
        obj = raw["data"]["object"]
        sub = await self._get_subscription_from_invoice(obj)
        if not sub:
            return

        tenant = await self.repos.tenant.get(sub.tenant_id)
        if not tenant:
            return

        for user in tenant.users:
            if not any(
                p.name == Permission.MANAGE_SUBSCRIPTION
                for role in user.roles
                for p in role.permissions
            ):
                continue
            await asyncio.to_thread(
                send_email,
                address=user.email,
                user_name=user.name,
                subject=f"Complete your {settings.app_name} payment "
                "- authentication required",
                email_template="payment-action-required",
                data={"billing_url": f"{settings.frontend_url}/settings/billing"},
            )

    async def _downgrade_to_free(self, sub: Subscription) -> PlanPrice | None:
        """
        Switches the Stripe subscription to the free price and returns it.
        If no free price is configured, cancels the subscription and returns None.
        The caller is responsible for updating the local subscription record.
        """
        free_price = await self.repos.plan_price.get_free_price()
        if not free_price:
            log.error(
                "No free price configured; canceling subscription directly [sub_id=%s]",
                sub.external_subscription_id,
            )
            await self.repos.subscription.update(
                sub, status="canceled", canceled_at=datetime.now(UTC)
            )
            return None

        if free_price.external_price_id and sub.external_subscription_id:
            try:
                await self.provider.switch_subscription_price(
                    sub.external_subscription_id,
                    free_price.external_price_id,
                    skip_proration=True,
                    new_amount=0,
                )
            except BillingProviderException as exc:
                log.warning(
                    "Failed to downgrade subscription to free plan [sub_id=%s]: %s",
                    sub.external_subscription_id,
                    exc,
                )
                raise

        return free_price

    async def _handle_invoice_marked_uncollectible(self, raw: dict) -> None:
        obj = raw["data"]["object"]
        sub = await self._get_subscription_from_invoice(obj)
        if not sub:
            return

        free_price = await self._downgrade_to_free(sub)
        if free_price:
            await self.repos.subscription.update(sub, plan_price_id=free_price.id)

        await self._notify_payment_failed(sub)

    async def _handle_subscription_trial_will_end(self, raw: dict) -> None:
        obj = raw["data"]["object"]
        sub_id: str = obj["id"]
        trial_end_ts: int | None = obj.get("trial_end")

        sub = await self.repos.subscription.get_by_external_subscription_id_locked(
            sub_id
        )
        if not sub:
            return

        if trial_end_ts:
            await self.repos.subscription.update(
                sub,
                trial_end=datetime.fromtimestamp(trial_end_ts, tz=UTC),
            )

        tenant = await self.repos.tenant.get(sub.tenant_id)
        if not tenant:
            return

        trial_end_date = (
            datetime.fromtimestamp(trial_end_ts, tz=UTC).strftime("%B %d, %Y")
            if trial_end_ts
            else "soon"
        )

        for user in tenant.users:
            if not any(
                p.name == Permission.MANAGE_SUBSCRIPTION
                for role in user.roles
                for p in role.permissions
            ):
                continue
            if tenant.has_payment_method:
                subject = (
                    f"Your {settings.app_name} trial ends on {trial_end_date}"
                    " - your card will be charged"
                )
            else:
                subject = (
                    f"Your {settings.app_name} trial ends on {trial_end_date}"
                    " - add a payment method to continue"
                )
            await asyncio.to_thread(
                send_email,
                address=user.email,
                user_name=user.name,
                subject=subject,
                email_template="trial-ending",
                data={
                    "trial_end_date": trial_end_date,
                    "billing_url": f"{settings.frontend_url}/settings/billing",
                    "has_payment_method": tenant.has_payment_method,
                },
            )

    async def _handle_subscription_paused(self, raw: dict) -> None:
        obj = raw["data"]["object"]
        sub_id: str = obj["id"]

        sub = await self.repos.subscription.get_by_external_subscription_id_locked(
            sub_id
        )
        if not sub:
            return

        # pause_collection is set for explicit manual pauses;
        # trial-end pauses leave it null
        is_trial_end_pause = not obj.get("pause_collection")

        if not is_trial_end_pause:
            await self.repos.subscription.update(sub, status="paused")
            tenant = await self.repos.tenant.get(sub.tenant_id)
            if not tenant:
                return
            for user in tenant.users:
                if not any(
                    p.name == Permission.MANAGE_SUBSCRIPTION
                    for role in user.roles
                    for p in role.permissions
                ):
                    continue
                await asyncio.to_thread(
                    send_email,
                    address=user.email,
                    user_name=user.name,
                    subject=f"Your {settings.app_name} subscription has been paused",
                    email_template="subscription-paused",
                    data={"billing_url": f"{settings.frontend_url}/settings/billing"},
                )
            return

        # Trial ended without payment method - downgrade to free immediately
        free_price = await self._downgrade_to_free(sub)
        if not free_price:
            return

        await self.repos.subscription.update(
            sub, plan_price_id=free_price.id, status="active"
        )

        tenant = await self.repos.tenant.get(sub.tenant_id)
        if not tenant:
            return

        for user in tenant.users:
            if not any(
                p.name == Permission.MANAGE_SUBSCRIPTION
                for role in user.roles
                for p in role.permissions
            ):
                continue
            await asyncio.to_thread(
                send_email,
                address=user.email,
                user_name=user.name,
                subject=f"Your {settings.app_name} trial has ended",
                email_template="trial-ended",
                data={"billing_url": f"{settings.frontend_url}/settings/billing"},
            )

    async def _handle_subscription_resumed(self, raw: dict) -> None:
        await self._handle_subscription_updated(raw)

    async def _handle_product_created(self, raw: dict) -> None:
        obj = raw["data"]["object"]
        external_product_id: str = obj["id"]

        plan = await self.repos.plan.get_by_external_product_id(external_product_id)
        if plan:
            return

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
            return

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
            currency=obj.get("currency", "dkk"),
            interval=recurring.get("interval", "month"),
            interval_count=recurring.get("interval_count", 1),
            external_price_id=external_price_id,
            trial_period_days=settings.billing_trial_period_days,
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
        log.info("Marking %d stale incomplete subscription(s) as canceled", len(stale))
        for sub in stale:
            log.debug(
                "Canceling stale subscription [id=%s tenant_id=%s]",
                sub.id,
                sub.tenant_id,
            )
            await self.repos.subscription.update(
                sub, status="canceled", canceled_at=datetime.now(UTC)
            )
        return len(stale)


async def run_stale_checkout_cleanup_loop(
    session_factory: Any, billing_provider: Any
) -> None:
    """
    Background loop that calls cleanup_stale_checkouts once every 24 hours.
    Intended to be launched as an asyncio task from the application lifespan.
    """
    while True:
        await asyncio.sleep(24 * 60 * 60)
        try:
            async with session_factory() as session:
                async with session.begin():
                    service = WebhookService.__new__(WebhookService)
                    service.repos = RepositoryManager(session)
                    service.provider = billing_provider
                    count = await service.cleanup_stale_checkouts()
                    log.info(
                        "Stale checkout cleanup: %d subscription(s) canceled",
                        count,
                    )
        except Exception as exc:  # pylint: disable=broad-except
            log.error("Stale checkout cleanup loop error: %s", exc, exc_info=True)
