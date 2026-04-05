import hashlib
from datetime import UTC, datetime
from typing import Literal

import stripe

from src.billing.abc import BillingProviderABC
from src.billing.types import (
    CheckoutResult,
    CustomerPortalResult,
    ExternalPrice,
    ExternalProduct,
    ExternalSubscription,
    WebhookPayload,
)
from src.core.exceptions import BillingProviderException, BillingWebhookException

# Stripe event type > normalized internal key
_EVENT_TYPE_MAP: dict[str, str] = {
    "checkout.session.completed": "checkout.session.completed",
    "checkout.session.expired": "checkout.session.expired",
    "customer.subscription.created": "subscription.created",
    "customer.subscription.updated": "subscription.updated",
    "customer.subscription.deleted": "subscription.deleted",
    "invoice.payment_failed": "invoice.payment_failed",
    "invoice.payment_succeeded": "invoice.payment_succeeded",
    "invoice.payment_action_required": "invoice.payment_action_required",
    "invoice.marked_uncollectible": "invoice.marked_uncollectible",
    "product.created": "product.created",
    "product.updated": "product.updated",
    "price.created": "price.created",
    "price.updated": "price.updated",
}


def _ts_to_dt(ts: int | None) -> datetime | None:
    if ts is None:
        return None
    return datetime.fromtimestamp(ts, tz=UTC)


class StripeProvider(BillingProviderABC):
    def __init__(self, api_key: str, webhook_secret: str) -> None:
        self._api_key = api_key
        self._webhook_secret = webhook_secret

    @staticmethod
    def _idempotency_key(*parts: str) -> str:
        raw = ":".join(parts)
        return hashlib.sha256(raw.encode()).hexdigest()[:40]

    async def create_product(
        self, name: str, description: str | None
    ) -> ExternalProduct:
        try:
            params: dict = {"name": name}
            if description:
                params["description"] = description
            product = await stripe.Product.create_async(
                **params,
                idempotency_key=self._idempotency_key("product-create", name),
                api_key=self._api_key,
            )
            return ExternalProduct(external_id=product.id)
        except stripe.StripeError as exc:
            raise BillingProviderException(str(exc)) from exc

    async def update_product(
        self, external_product_id: str, name: str, description: str | None
    ) -> ExternalProduct:
        try:
            params: dict = {"name": name}
            if description is not None:
                params["description"] = description
            product = await stripe.Product.modify_async(
                external_product_id,
                **params,
                idempotency_key=self._idempotency_key(
                    "product-update", external_product_id
                ),
                api_key=self._api_key,
            )
            return ExternalProduct(external_id=product.id)
        except stripe.StripeError as exc:
            raise BillingProviderException(str(exc)) from exc

    async def archive_product(self, external_product_id: str) -> None:
        try:
            await stripe.Product.modify_async(
                external_product_id,
                active=False,
                idempotency_key=self._idempotency_key(
                    "product-archive", external_product_id
                ),
                api_key=self._api_key,
            )
        except stripe.StripeError as exc:
            raise BillingProviderException(str(exc)) from exc

    async def create_price(  # pylint: disable=too-many-arguments,too-many-positional-arguments
        self,
        external_product_id: str,
        amount: int,
        currency: str,
        interval: str,
        interval_count: int,
    ) -> ExternalPrice:
        try:
            price = await stripe.Price.create_async(
                product=external_product_id,
                unit_amount=amount,
                currency=currency,
                recurring={
                    "interval": interval,  # type: ignore[typeddict-item]
                    "interval_count": interval_count,
                },
                idempotency_key=self._idempotency_key(
                    "price-create",
                    external_product_id,
                    str(amount),
                    currency,
                    interval,
                    str(interval_count),
                ),
                api_key=self._api_key,
            )
            return ExternalPrice(external_id=price.id)
        except stripe.StripeError as exc:
            raise BillingProviderException(str(exc)) from exc

    async def archive_price(self, external_price_id: str) -> None:
        try:
            await stripe.Price.modify_async(
                external_price_id,
                active=False,
                idempotency_key=self._idempotency_key(
                    "price-archive", external_price_id
                ),
                api_key=self._api_key,
            )
        except stripe.StripeError as exc:
            raise BillingProviderException(str(exc)) from exc

    async def get_or_create_customer(
        self, tenant_id: int, tenant_name: str, email: str | None = None
    ) -> str:
        try:
            existing = await stripe.Customer.search_async(
                query=f'metadata["tenant_id"]:"{tenant_id}"',
                api_key=self._api_key,
            )
            if existing.data:
                return existing.data[0].id

            params: dict = {
                "name": tenant_name,
                "metadata": {"tenant_id": str(tenant_id)},
            }
            if email:
                params["email"] = email
            customer = await stripe.Customer.create_async(
                **params, api_key=self._api_key
            )
            return customer.id
        except stripe.StripeError as exc:
            raise BillingProviderException(str(exc)) from exc

    async def update_customer(self, external_customer_id: str, email: str) -> None:
        try:
            await stripe.Customer.modify_async(
                external_customer_id,
                email=email,
                idempotency_key=self._idempotency_key(
                    "customer-update", external_customer_id, email
                ),
                api_key=self._api_key,
            )
        except stripe.StripeError as exc:
            raise BillingProviderException(str(exc)) from exc

    async def create_checkout_session(  # pylint: disable=too-many-arguments,too-many-positional-arguments
        self,
        external_customer_id: str | None,
        external_price_id: str,
        amount: int,
        success_url: str,
        cancel_url: str,
        metadata: dict,
    ) -> CheckoutResult:
        try:
            params: dict = {
                "mode": "subscription",
                "line_items": [{"price": external_price_id, "quantity": 1}],
                "success_url": success_url,
                "cancel_url": cancel_url,
                "metadata": {k: str(v) for k, v in metadata.items()},
            }
            if amount == 0:
                params["payment_method_collection"] = "if_required"
            if external_customer_id:
                params["customer"] = external_customer_id
            else:
                params["customer_creation"] = "always"

            session = await stripe.checkout.Session.create_async(
                **params,
                idempotency_key=self._idempotency_key(
                    "checkout-session",
                    str(metadata.get("tenant_id", "")),
                    str(metadata.get("plan_price_id", "")),
                ),
                api_key=self._api_key,
            )
            return CheckoutResult(
                checkout_url=session.url or "",
                external_session_id=session.id,
            )
        except stripe.StripeError as exc:
            raise BillingProviderException(str(exc)) from exc

    async def cancel_subscription(
        self, external_subscription_id: str
    ) -> ExternalSubscription:
        try:
            sub = await stripe.Subscription.modify_async(
                external_subscription_id,
                cancel_at_period_end=True,
                idempotency_key=self._idempotency_key(
                    "sub-cancel", external_subscription_id
                ),
                api_key=self._api_key,
            )
            return self._map_subscription(sub)
        except stripe.StripeError as exc:
            raise BillingProviderException(str(exc)) from exc

    async def resume_subscription(
        self, external_subscription_id: str
    ) -> ExternalSubscription:
        try:
            sub = await stripe.Subscription.modify_async(
                external_subscription_id,
                cancel_at_period_end=False,
                idempotency_key=self._idempotency_key(
                    "sub-resume", external_subscription_id
                ),
                api_key=self._api_key,
            )
            return self._map_subscription(sub)
        except stripe.StripeError as exc:
            raise BillingProviderException(str(exc)) from exc

    async def switch_subscription_price(
        self,
        external_subscription_id: str,
        new_external_price_id: str,
        skip_proration: bool = False,
    ) -> ExternalSubscription:
        try:
            sub = await stripe.Subscription.retrieve_async(
                external_subscription_id,
                api_key=self._api_key,
            )
            if not sub.items.data:
                raise BillingProviderException("Subscription has no items to update.")
            item_id: str = sub.items.data[0].id
            proration_behavior: Literal[
                "always_invoice", "create_prorations", "none"
            ] = "none" if skip_proration else "create_prorations"
            updated = await stripe.Subscription.modify_async(
                external_subscription_id,
                items=[{"id": item_id, "price": new_external_price_id}],
                proration_behavior=proration_behavior,
                idempotency_key=self._idempotency_key(
                    "sub-switch", external_subscription_id, new_external_price_id
                ),
                api_key=self._api_key,
            )
            return self._map_subscription(updated)
        except stripe.StripeError as exc:
            raise BillingProviderException(str(exc)) from exc

    async def create_subscription(
        self, external_customer_id: str, external_price_id: str
    ) -> ExternalSubscription:
        try:
            sub = await stripe.Subscription.create_async(
                customer=external_customer_id,
                items=[{"price": external_price_id}],
                idempotency_key=self._idempotency_key(
                    "sub-create", external_customer_id, external_price_id
                ),
                api_key=self._api_key,
            )
            return self._map_subscription(sub)
        except stripe.StripeError as exc:
            raise BillingProviderException(str(exc)) from exc

    async def get_customer_portal_url(
        self, external_customer_id: str, return_url: str
    ) -> CustomerPortalResult:
        try:
            session = await stripe.billing_portal.Session.create_async(
                customer=external_customer_id,
                return_url=return_url,
                api_key=self._api_key,
            )
            return CustomerPortalResult(portal_url=session.url)
        except stripe.StripeError as exc:
            raise BillingProviderException(str(exc)) from exc

    def construct_webhook_event(
        self, payload: bytes, sig_header: str
    ) -> WebhookPayload:
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, self._webhook_secret
            )
        except stripe.SignatureVerificationError as exc:
            raise BillingWebhookException("Invalid webhook signature") from exc
        except stripe.StripeError as exc:
            raise BillingProviderException(str(exc)) from exc

        raw = event.to_dict()
        stripe_event_type: str = event.type
        normalized = _EVENT_TYPE_MAP.get(stripe_event_type, stripe_event_type)

        return WebhookPayload(
            external_event_id=event.id,
            event_type=normalized,
            raw=raw,
        )

    @staticmethod
    def _map_subscription(sub: stripe.Subscription) -> ExternalSubscription:
        item = sub.items.data[0] if (sub.items and sub.items.data) else None

        canceled_at: datetime | None = None
        if sub.canceled_at:
            canceled_at = _ts_to_dt(sub.canceled_at)

        return ExternalSubscription(
            external_subscription_id=sub.id,
            external_customer_id=str(sub.customer)
            if isinstance(sub.customer, str)
            else sub.customer.id,
            status=sub.status,
            current_period_start=_ts_to_dt(item.current_period_start if item else None),
            current_period_end=_ts_to_dt(item.current_period_end if item else None),
            cancel_at_period_end=sub.cancel_at_period_end,
            canceled_at=canceled_at,
            external_price_id=item.price.id if item else None,
        )
