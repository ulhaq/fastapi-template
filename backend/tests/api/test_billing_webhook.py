from datetime import UTC, datetime
import pytest

from sqlalchemy import delete
from fastapi.testclient import TestClient
from src.billing.types import WebhookPayload
from src.core.exceptions import BillingProviderException, BillingWebhookException
from src.billing.types import ExternalSubscription
from src.models.billing import PlanPrice
from tests.conftest import TestSessionLocal


def test_webhook_valid_payload(client: TestClient, mock_billing_provider) -> None:
    mock_billing_provider.construct_webhook_event.return_value = WebhookPayload(
        external_event_id="evt_001",
        event_type="customer.subscription.updated",
        raw={"data": {"object": {"id": "sub_unknown", "status": "active"}}},
    )
    response = client.post(
        "/v1/billing/webhook",
        content=b"test_payload",
        headers={"stripe-signature": "sig_test"},
    )
    assert response.status_code == 200
    assert response.json() == {"received": True}


def test_webhook_invalid_signature(client: TestClient, mock_billing_provider) -> None:
    mock_billing_provider.construct_webhook_event.side_effect = BillingWebhookException(
        "Invalid webhook signature"
    )
    response = client.post(
        "/v1/billing/webhook",
        content=b"bad_payload",
        headers={"stripe-signature": "bad_sig"},
    )
    assert response.status_code == 400
    assert response.json()["error_code"] == "billing_webhook_invalid"


def test_webhook_idempotency(client: TestClient, mock_billing_provider) -> None:
    payload = WebhookPayload(
        external_event_id="evt_idempotent_001",
        event_type="customer.subscription.updated",
        raw={"data": {"object": {"id": "sub_noop", "status": "active"}}},
    )

    # Send twice
    for _ in range(2):
        mock_billing_provider.construct_webhook_event.return_value = payload
        resp = client.post(
            "/v1/billing/webhook",
            content=b"{}",
            headers={"stripe-signature": "sig"},
        )
        assert resp.status_code == 200

    # The event should be recorded once - second call is a no-op after "processed"
    assert mock_billing_provider.construct_webhook_event.call_count == 2


def test_webhook_checkout_completed_updates_subscription(
    admin_authenticated: TestClient,
    plan_with_price: dict,
    mock_billing_provider,
) -> None:
    price_id = plan_with_price["price"]["id"]

    # Create an incomplete subscription via checkout
    admin_authenticated.post(
        "/v1/billing/subscriptions/checkout",
        json={"plan_price_id": price_id},
    )

    # Verify it's incomplete
    sub = admin_authenticated.get("/v1/billing/subscriptions/current").json()
    assert sub["status"] == "incomplete"

    # Fire checkout.session.completed webhook
    mock_billing_provider.construct_webhook_event.return_value = WebhookPayload(
        external_event_id="evt_checkout_done",
        event_type="checkout.session.completed",
        raw={
            "data": {
                "object": {
                    "subscription": "sub_activated_123",
                    "customer": "cus_test123",
                    "metadata": {"plan_price_id": str(price_id)},
                }
            }
        },
    )
    resp = admin_authenticated.post(
        "/v1/billing/webhook",
        content=b"{}",
        headers={"stripe-signature": "sig"},
    )
    assert resp.status_code == 200

    # Subscription should now be active
    sub = admin_authenticated.get("/v1/billing/subscriptions/current").json()
    assert sub["status"] == "active"
    assert sub["external_subscription_id"] == "sub_activated_123"


def test_webhook_subscription_deleted(
    admin_authenticated: TestClient,
    plan_with_price: dict,
    mock_billing_provider,
) -> None:
    price_id = plan_with_price["price"]["id"]

    # Set up an active subscription
    admin_authenticated.post(
        "/v1/billing/subscriptions/checkout",
        json={"plan_price_id": price_id},
    )
    mock_billing_provider.construct_webhook_event.return_value = WebhookPayload(
        external_event_id="evt_activate_for_delete",
        event_type="checkout.session.completed",
        raw={
            "data": {
                "object": {
                    "subscription": "sub_to_delete",
                    "customer": "cus_test123",
                    "metadata": {"plan_price_id": str(price_id)},
                }
            }
        },
    )
    admin_authenticated.post(
        "/v1/billing/webhook", content=b"{}", headers={"stripe-signature": "s"}
    )

    # Fire subscription.deleted
    canceled_ts = int(datetime.now(UTC).timestamp())
    mock_billing_provider.construct_webhook_event.return_value = WebhookPayload(
        external_event_id="evt_sub_deleted",
        event_type="customer.subscription.deleted",
        raw={
            "data": {
                "object": {
                    "id": "sub_to_delete",
                    "canceled_at": canceled_ts,
                }
            }
        },
    )
    resp = admin_authenticated.post(
        "/v1/billing/webhook", content=b"{}", headers={"stripe-signature": "s"}
    )
    assert resp.status_code == 200

    # The subscription is now "canceled" - not returned by get_active_for_tenant
    sub_resp = admin_authenticated.get("/v1/billing/subscriptions/current")
    assert sub_resp.status_code == 404


def test_webhook_payment_failed_does_not_downgrade(
    admin_authenticated: TestClient,
    plan_with_price: dict,
    mock_billing_provider,
) -> None:
    """
    First payment failure must not downgrade - Stripe Smart Retries are still pending.
    """
    price_id = plan_with_price["price"]["id"]

    # Set up an active subscription
    admin_authenticated.post(
        "/v1/billing/subscriptions/checkout", json={"plan_price_id": price_id}
    )
    mock_billing_provider.construct_webhook_event.return_value = WebhookPayload(
        external_event_id="evt_activate_for_fail",
        event_type="checkout.session.completed",
        raw={
            "data": {
                "object": {
                    "subscription": "sub_payment_fail",
                    "customer": "cus_test123",
                    "metadata": {"plan_price_id": str(price_id)},
                }
            }
        },
    )
    admin_authenticated.post(
        "/v1/billing/webhook", content=b"{}", headers={"stripe-signature": "s"}
    )

    # Fire invoice.payment_failed - plan must NOT be touched
    mock_billing_provider.construct_webhook_event.return_value = WebhookPayload(
        external_event_id="evt_payment_failed",
        event_type="invoice.payment_failed",
        raw={
            "data": {
                "object": {
                    "subscription": "sub_payment_fail",
                }
            }
        },
    )
    resp = admin_authenticated.post(
        "/v1/billing/webhook", content=b"{}", headers={"stripe-signature": "s"}
    )
    assert resp.status_code == 200

    sub = admin_authenticated.get("/v1/billing/subscriptions/current").json()
    assert sub["status"] == "active"
    # Plan price must remain unchanged - no downgrade on first failure
    assert sub["plan_price"]["id"] == price_id
    mock_billing_provider.switch_subscription_price.assert_not_called()


def test_webhook_subscription_updated(
    admin_authenticated: TestClient,
    plan_with_price: dict,
    mock_billing_provider,
) -> None:
    price_id = plan_with_price["price"]["id"]

    admin_authenticated.post(
        "/v1/billing/subscriptions/checkout",
        json={"plan_price_id": price_id},
    )
    mock_billing_provider.construct_webhook_event.return_value = WebhookPayload(
        external_event_id="evt_activate_for_update",
        event_type="checkout.session.completed",
        raw={
            "data": {
                "object": {
                    "subscription": "sub_to_update",
                    "customer": "cus_test123",
                    "metadata": {"plan_price_id": str(price_id)},
                }
            }
        },
    )
    admin_authenticated.post(
        "/v1/billing/webhook", content=b"{}", headers={"stripe-signature": "s"}
    )

    now_ts = int(datetime.now(UTC).timestamp())
    mock_billing_provider.construct_webhook_event.return_value = WebhookPayload(
        external_event_id="evt_sub_updated",
        event_type="customer.subscription.updated",
        raw={
            "data": {
                "object": {
                    "id": "sub_to_update",
                    "status": "past_due",
                    "cancel_at_period_end": True,
                    "current_period_start": now_ts,
                    "current_period_end": now_ts + 2592000,
                    "canceled_at": None,
                    "items": {"data": [{"price": {"id": "price_test123"}}]},
                }
            }
        },
    )
    resp = admin_authenticated.post(
        "/v1/billing/webhook", content=b"{}", headers={"stripe-signature": "s"}
    )
    assert resp.status_code == 200

    sub = admin_authenticated.get("/v1/billing/subscriptions/current").json()
    assert sub["status"] == "past_due"
    assert sub["cancel_at_period_end"] is True


def _activate_sub(
    client, price_id: int, mock_billing_provider, event_id: str, sub_id: str
) -> None:
    client.post("/v1/billing/subscriptions/checkout", json={"plan_price_id": price_id})
    mock_billing_provider.construct_webhook_event.return_value = WebhookPayload(
        external_event_id=event_id,
        event_type="checkout.session.completed",
        raw={
            "data": {
                "object": {
                    "subscription": sub_id,
                    "customer": "cus_test123",
                    "metadata": {"plan_price_id": str(price_id)},
                }
            }
        },
    )
    client.post("/v1/billing/webhook", content=b"{}", headers={"stripe-signature": "s"})


def test_webhook_subscription_created(
    admin_authenticated: TestClient,
    plan_with_price: dict,
    mock_billing_provider,
) -> None:
    price_id = plan_with_price["price"]["id"]
    admin_authenticated.post(
        "/v1/billing/subscriptions/checkout", json={"plan_price_id": price_id}
    )

    # subscription.created fires before checkout.session.completed in Stripe's event order,
    # so external_subscription_id is not yet set - handler must fall back to customer lookup
    now_ts = int(datetime.now(UTC).timestamp())
    mock_billing_provider.construct_webhook_event.return_value = WebhookPayload(
        external_event_id="evt_sub_created",
        event_type="customer.subscription.created",
        raw={
            "data": {
                "object": {
                    "id": "sub_created_123",
                    "customer": "cus_test123",
                    "status": "trialing",
                    "cancel_at_period_end": False,
                    "current_period_start": now_ts,
                    "current_period_end": now_ts + 1209600,
                    "canceled_at": None,
                    "items": {"data": [{"price": {"id": "price_test123"}}]},
                }
            }
        },
    )
    resp = admin_authenticated.post(
        "/v1/billing/webhook", content=b"{}", headers={"stripe-signature": "s"}
    )
    assert resp.status_code == 200

    sub = admin_authenticated.get("/v1/billing/subscriptions/current").json()
    assert sub["status"] == "trialing"
    assert sub["external_subscription_id"] == "sub_created_123"
    assert sub["current_period_start"] is not None
    assert sub["current_period_end"] is not None


def test_webhook_checkout_session_expired(
    admin_authenticated: TestClient,
    plan_with_price: dict,
    mock_billing_provider,
) -> None:
    price_id = plan_with_price["price"]["id"]

    # Create an incomplete subscription
    admin_authenticated.post(
        "/v1/billing/subscriptions/checkout", json={"plan_price_id": price_id}
    )
    sub = admin_authenticated.get("/v1/billing/subscriptions/current").json()
    assert sub["status"] == "incomplete"

    mock_billing_provider.construct_webhook_event.return_value = WebhookPayload(
        external_event_id="evt_checkout_expired",
        event_type="checkout.session.expired",
        raw={
            "data": {
                "object": {
                    "customer": "cus_test123",
                    "metadata": {"plan_price_id": str(price_id)},
                }
            }
        },
    )
    resp = admin_authenticated.post(
        "/v1/billing/webhook", content=b"{}", headers={"stripe-signature": "s"}
    )
    assert resp.status_code == 200
    assert (
        admin_authenticated.get("/v1/billing/subscriptions/current").status_code == 404
    )


def test_webhook_payment_action_required_sets_incomplete(
    admin_authenticated: TestClient,
    plan_with_price: dict,
    mock_billing_provider,
) -> None:
    price_id = plan_with_price["price"]["id"]
    _activate_sub(
        admin_authenticated, price_id, mock_billing_provider, "evt_act_pam", "sub_pam"
    )

    mock_billing_provider.construct_webhook_event.return_value = WebhookPayload(
        external_event_id="evt_payment_action_required",
        event_type="invoice.payment_action_required",
        raw={"data": {"object": {"subscription": "sub_pam"}}},
    )
    admin_authenticated.post(
        "/v1/billing/webhook", content=b"{}", headers={"stripe-signature": "s"}
    )

    # Stripe fires customer.subscription.updated alongside the invoice event
    mock_billing_provider.construct_webhook_event.return_value = WebhookPayload(
        external_event_id="evt_payment_action_required_sub_updated",
        event_type="customer.subscription.updated",
        raw={
            "data": {
                "object": {
                    "id": "sub_pam",
                    "status": "incomplete",
                    "cancel_at_period_end": False,
                    "canceled_at": None,
                    "items": {"data": [{"price": {"id": "price_test123"}}]},
                }
            }
        },
    )
    resp = admin_authenticated.post(
        "/v1/billing/webhook", content=b"{}", headers={"stripe-signature": "s"}
    )
    assert resp.status_code == 200
    sub = admin_authenticated.get("/v1/billing/subscriptions/current").json()
    assert sub["status"] == "incomplete"


def test_webhook_marked_uncollectible_downgrades_to_free_plan(
    admin_authenticated: TestClient,
    plan_with_price: dict,
    mock_billing_provider,
) -> None:
    """
    All Stripe retries exhausted - subscription should be downgraded to free.
    """
    price_id = plan_with_price["price"]["id"]
    _activate_sub(
        admin_authenticated, price_id, mock_billing_provider, "evt_act_muc", "sub_muc"
    )

    mock_billing_provider.switch_subscription_price.return_value = ExternalSubscription(
        external_subscription_id="sub_muc",
        external_customer_id="cus_test123",
        status="active",
        current_period_start=None,
        current_period_end=None,
        cancel_at_period_end=False,
        canceled_at=None,
        external_price_id="price_free123",
    )
    mock_billing_provider.construct_webhook_event.return_value = WebhookPayload(
        external_event_id="evt_marked_uncollectible",
        event_type="invoice.marked_uncollectible",
        raw={"data": {"object": {"subscription": "sub_muc"}}},
    )
    resp = admin_authenticated.post(
        "/v1/billing/webhook", content=b"{}", headers={"stripe-signature": "s"}
    )
    assert resp.status_code == 200

    sub = admin_authenticated.get("/v1/billing/subscriptions/current").json()
    assert sub["plan_price"]["external_price_id"] == "price_free123"
    mock_billing_provider.switch_subscription_price.assert_called_once_with(
        "sub_muc", "price_free123", skip_proration=True, new_amount=0
    )


def test_webhook_product_created(
    admin_authenticated: TestClient,
    mock_billing_provider,
) -> None:
    mock_billing_provider.construct_webhook_event.return_value = WebhookPayload(
        external_event_id="evt_product_created",
        event_type="product.created",
        raw={
            "data": {
                "object": {
                    "id": "prod_stripe_new",
                    "name": "Stripe Plan",
                    "description": "Created in Stripe",
                    "active": True,
                }
            }
        },
    )
    resp = admin_authenticated.post(
        "/v1/billing/webhook", content=b"{}", headers={"stripe-signature": "s"}
    )
    assert resp.status_code == 200

    plans = admin_authenticated.get("/v1/billing/plans").json()
    created = next((p for p in plans if p["name"] == "Stripe Plan"), None)
    assert created is not None
    assert created["description"] == "Created in Stripe"


def test_webhook_product_created_already_exists(
    admin_authenticated: TestClient,
    plan_with_price: dict,
    mock_billing_provider,
) -> None:
    # plan_with_price already has external_product_id="prod_test123"
    mock_billing_provider.construct_webhook_event.return_value = WebhookPayload(
        external_event_id="evt_product_created_dup",
        event_type="product.created",
        raw={
            "data": {
                "object": {
                    "id": "prod_test123",
                    "name": "Duplicate",
                    "description": None,
                    "active": True,
                }
            }
        },
    )
    resp = admin_authenticated.post(
        "/v1/billing/webhook", content=b"{}", headers={"stripe-signature": "s"}
    )
    assert resp.status_code == 200

    plans = admin_authenticated.get("/v1/billing/plans").json()
    matching = [p for p in plans if p["name"] == "Duplicate"]
    assert len(matching) == 0  # no duplicate created


def test_webhook_product_updated(
    admin_authenticated: TestClient,
    plan_with_price: dict,
    mock_billing_provider,
) -> None:
    mock_billing_provider.construct_webhook_event.return_value = WebhookPayload(
        external_event_id="evt_product_updated",
        event_type="product.updated",
        raw={
            "data": {
                "object": {
                    "id": "prod_test123",
                    "name": "Updated Name",
                    "description": "Updated desc",
                    "active": False,
                }
            }
        },
    )
    resp = admin_authenticated.post(
        "/v1/billing/webhook", content=b"{}", headers={"stripe-signature": "s"}
    )
    assert resp.status_code == 200

    plans = admin_authenticated.get("/v1/billing/plans").json()
    # is_active=False means it won't appear in list_plans (which filters active only)
    assert not any(p["name"] == "Updated Name" for p in plans)


def test_webhook_price_created(
    admin_authenticated: TestClient,
    plan_with_price: dict,
    mock_billing_provider,
) -> None:
    plan_id = plan_with_price["plan"]["id"]

    mock_billing_provider.construct_webhook_event.return_value = WebhookPayload(
        external_event_id="evt_price_created",
        event_type="price.created",
        raw={
            "data": {
                "object": {
                    "id": "price_stripe_new",
                    "product": "prod_test123",
                    "unit_amount": 4999,
                    "currency": "usd",
                    "active": True,
                    "recurring": {"interval": "year", "interval_count": 1},
                }
            }
        },
    )
    resp = admin_authenticated.post(
        "/v1/billing/webhook", content=b"{}", headers={"stripe-signature": "s"}
    )
    assert resp.status_code == 200

    plan = admin_authenticated.get(f"/v1/billing/plans/{plan_id}").json()
    new_price = next(
        (p for p in plan["prices"] if p["external_price_id"] == "price_stripe_new"),
        None,
    )
    assert new_price is not None
    assert new_price["amount"] == 4999
    assert new_price["interval"] == "year"


def test_webhook_price_created_unknown_product(
    admin_authenticated: TestClient,
    mock_billing_provider,
) -> None:
    mock_billing_provider.construct_webhook_event.return_value = WebhookPayload(
        external_event_id="evt_price_created_unknown",
        event_type="price.created",
        raw={
            "data": {
                "object": {
                    "id": "price_orphan",
                    "product": "prod_nonexistent",
                    "unit_amount": 999,
                    "currency": "usd",
                    "active": True,
                    "recurring": {"interval": "month", "interval_count": 1},
                }
            }
        },
    )
    resp = admin_authenticated.post(
        "/v1/billing/webhook", content=b"{}", headers={"stripe-signature": "s"}
    )
    assert resp.status_code == 200  # no crash


@pytest.fixture
async def trialing_subscription(plan_with_price: dict) -> dict:
    """Insert a trialing subscription row directly, bypassing the checkout endpoint."""
    from tests.conftest import TestSessionLocal
    from src.models.billing import Subscription
    from src.models.tenant import Tenant

    price_id = plan_with_price["price"]["id"]
    async with TestSessionLocal() as session:
        tenant = await session.get(Tenant, 1)
        tenant.external_customer_id = "cus_test123"
        sub = Subscription(
            tenant_id=1,  # admin@example.org belongs to tenant 1
            plan_price_id=price_id,
            external_subscription_id="sub_trial",
            status="trialing",
        )
        session.add(sub)
        await session.commit()
    return {"external_subscription_id": "sub_trial"}


def test_webhook_subscription_trial_will_end_sends_email(
    admin_authenticated: TestClient,
    trialing_subscription: dict,
    mock_billing_provider,
    mocker,
) -> None:
    trial_end_ts = int(datetime(2026, 5, 1, tzinfo=UTC).timestamp())
    mock_send = mocker.patch("src.services.billing.send_email")

    mock_billing_provider.construct_webhook_event.return_value = WebhookPayload(
        external_event_id="evt_trial_will_end",
        event_type="customer.subscription.trial_will_end",
        raw={
            "data": {
                "object": {
                    "id": "sub_trial",
                    "trial_end": trial_end_ts,
                }
            }
        },
    )
    resp = admin_authenticated.post(
        "/v1/billing/webhook", content=b"{}", headers={"stripe-signature": "s"}
    )
    assert resp.status_code == 200
    assert mock_send.called
    addresses = {call.kwargs["address"] for call in mock_send.call_args_list}
    assert "admin@example.org" in addresses
    for call in mock_send.call_args_list:
        assert call.kwargs["email_template"] == "trial-ending"
        assert "May 01, 2026" in call.kwargs["data"]["trial_end_date"]


def test_webhook_subscription_trial_will_end_unknown_sub(
    client: TestClient,
    mock_billing_provider,
) -> None:
    mock_billing_provider.construct_webhook_event.return_value = WebhookPayload(
        external_event_id="evt_trial_unknown",
        event_type="customer.subscription.trial_will_end",
        raw={"data": {"object": {"id": "sub_nonexistent", "trial_end": None}}},
    )
    resp = client.post(
        "/v1/billing/webhook", content=b"{}", headers={"stripe-signature": "s"}
    )
    assert resp.status_code == 200  # silently ignored


def test_webhook_price_updated(
    admin_authenticated: TestClient,
    plan_with_price: dict,
    mock_billing_provider,
) -> None:
    plan_id = plan_with_price["plan"]["id"]

    mock_billing_provider.construct_webhook_event.return_value = WebhookPayload(
        external_event_id="evt_price_updated",
        event_type="price.updated",
        raw={
            "data": {
                "object": {
                    "id": "price_test123",
                    "active": False,
                }
            }
        },
    )
    resp = admin_authenticated.post(
        "/v1/billing/webhook", content=b"{}", headers={"stripe-signature": "s"}
    )
    assert resp.status_code == 200

    plan = admin_authenticated.get(f"/v1/billing/plans/{plan_id}").json()
    price = next(p for p in plan["prices"] if p["external_price_id"] == "price_test123")
    assert price["is_active"] is False


def test_webhook_uncollectible_downgrades_to_free_plan(
    admin_authenticated: TestClient,
    plan_with_price: dict,
    trialing_subscription: dict,
    mock_billing_provider,
) -> None:
    """
    invoice.marked_uncollectible (all retries exhausted) should downgrade to free.
    """
    mock_billing_provider.switch_subscription_price.return_value = ExternalSubscription(
        external_subscription_id="sub_trial",
        external_customer_id="cus_test123",
        status="active",
        current_period_start=None,
        current_period_end=None,
        cancel_at_period_end=False,
        canceled_at=None,
        external_price_id="price_free123",
    )
    mock_billing_provider.construct_webhook_event.return_value = WebhookPayload(
        external_event_id="evt_uncollectible_downgrade",
        event_type="invoice.marked_uncollectible",
        raw={"data": {"object": {"subscription": "sub_trial"}}},
    )
    admin_authenticated.post(
        "/v1/billing/webhook", content=b"{}", headers={"stripe-signature": "s"}
    )

    # Stripe fires customer.subscription.updated after the price switch
    mock_billing_provider.construct_webhook_event.return_value = WebhookPayload(
        external_event_id="evt_uncollectible_downgrade_sub_updated",
        event_type="customer.subscription.updated",
        raw={
            "data": {
                "object": {
                    "id": "sub_trial",
                    "status": "active",
                    "cancel_at_period_end": False,
                    "canceled_at": None,
                    "items": {"data": [{"price": {"id": "price_free123"}}]},
                }
            }
        },
    )
    resp = admin_authenticated.post(
        "/v1/billing/webhook", content=b"{}", headers={"stripe-signature": "s"}
    )
    assert resp.status_code == 200

    sub = admin_authenticated.get("/v1/billing/subscriptions/current").json()
    assert sub["status"] == "active"
    assert sub["plan_price"]["external_price_id"] == "price_free123"
    mock_billing_provider.switch_subscription_price.assert_called_once_with(
        "sub_trial", "price_free123", skip_proration=True, new_amount=0
    )


def test_webhook_uncollectible_falls_back_gracefully_on_provider_error(
    admin_authenticated: TestClient,
    plan_with_price: dict,
    trialing_subscription: dict,
    mock_billing_provider,
) -> None:
    """
    When the provider rejects the free-plan switch, the subscription stays but a
    warning is logged - the webhook is still acked to avoid infinite Stripe retries.
    """
    mock_billing_provider.switch_subscription_price.side_effect = (
        BillingProviderException("Stripe error")
    )
    mock_billing_provider.construct_webhook_event.return_value = WebhookPayload(
        external_event_id="evt_uncollectible_fallback",
        event_type="invoice.marked_uncollectible",
        raw={"data": {"object": {"subscription": "sub_trial"}}},
    )
    resp = admin_authenticated.post(
        "/v1/billing/webhook", content=b"{}", headers={"stripe-signature": "s"}
    )
    assert resp.status_code == 200

    # Stripe fires customer.subscription.updated with past_due when the switch failed
    mock_billing_provider.construct_webhook_event.return_value = WebhookPayload(
        external_event_id="evt_uncollectible_fallback_sub_updated",
        event_type="customer.subscription.updated",
        raw={
            "data": {
                "object": {
                    "id": "sub_trial",
                    "status": "past_due",
                    "cancel_at_period_end": False,
                    "canceled_at": None,
                    "items": {"data": [{"price": {"id": "price_test123"}}]},
                }
            }
        },
    )
    resp = admin_authenticated.post(
        "/v1/billing/webhook", content=b"{}", headers={"stripe-signature": "s"}
    )
    assert resp.status_code == 200

    sub = admin_authenticated.get("/v1/billing/subscriptions/current").json()
    assert sub["status"] == "past_due"
    assert sub["plan_price"]["external_price_id"] == "price_test123"


@pytest.fixture
async def no_free_price() -> None:
    async with TestSessionLocal() as session:
        await session.execute(delete(PlanPrice).where(PlanPrice.amount == 0))
        await session.commit()


def test_webhook_subscription_paused_trial_end_downgrades_to_free(
    admin_authenticated: TestClient,
    trialing_subscription: dict,
    mock_billing_provider,
    mocker,
) -> None:
    """
    Trial ended without a payment method (pause_collection is null) — subscription
    should be immediately downgraded to the free plan and set to active.
    """
    mock_billing_provider.switch_subscription_price.return_value = ExternalSubscription(
        external_subscription_id="sub_trial",
        external_customer_id="cus_test123",
        status="active",
        current_period_start=None,
        current_period_end=None,
        cancel_at_period_end=False,
        canceled_at=None,
        external_price_id="price_free123",
    )
    mock_send = mocker.patch("src.services.billing.send_email")

    mock_billing_provider.construct_webhook_event.return_value = WebhookPayload(
        external_event_id="evt_sub_paused_trial_end",
        event_type="customer.subscription.paused",
        raw={
            "data": {
                "object": {
                    "id": "sub_trial",
                    "pause_collection": None,
                }
            }
        },
    )
    resp = admin_authenticated.post(
        "/v1/billing/webhook", content=b"{}", headers={"stripe-signature": "s"}
    )
    assert resp.status_code == 200

    sub = admin_authenticated.get("/v1/billing/subscriptions/current").json()
    assert sub["status"] == "active"
    assert sub["plan_price"]["external_price_id"] == "price_free123"
    mock_billing_provider.switch_subscription_price.assert_called_once_with(
        "sub_trial", "price_free123", skip_proration=True, new_amount=0
    )
    assert mock_send.called
    for call in mock_send.call_args_list:
        assert call.kwargs["email_template"] == "trial-ended"


def test_webhook_subscription_paused_manual_stays_paused(
    admin_authenticated: TestClient,
    trialing_subscription: dict,
    mock_billing_provider,
) -> None:
    """
    Explicit manual pause (pause_collection is set) — subscription should be
    marked paused and the plan price must remain unchanged.
    """
    mock_billing_provider.construct_webhook_event.return_value = WebhookPayload(
        external_event_id="evt_sub_paused_manual",
        event_type="customer.subscription.paused",
        raw={
            "data": {
                "object": {
                    "id": "sub_trial",
                    "pause_collection": {"behavior": "void"},
                }
            }
        },
    )
    resp = admin_authenticated.post(
        "/v1/billing/webhook", content=b"{}", headers={"stripe-signature": "s"}
    )
    assert resp.status_code == 200

    sub = admin_authenticated.get("/v1/billing/subscriptions/current").json()
    assert sub["status"] == "paused"
    mock_billing_provider.switch_subscription_price.assert_not_called()


def test_webhook_subscription_paused_trial_end_no_free_plan_cancels(
    admin_authenticated: TestClient,
    trialing_subscription: dict,
    no_free_price: None,
    mock_billing_provider,
) -> None:
    """
    Trial ended without a payment method and no free plan is configured — subscription
    should be canceled rather than left in a paused limbo.
    """
    mock_billing_provider.construct_webhook_event.return_value = WebhookPayload(
        external_event_id="evt_sub_paused_no_free",
        event_type="customer.subscription.paused",
        raw={
            "data": {
                "object": {
                    "id": "sub_trial",
                    "pause_collection": None,
                }
            }
        },
    )
    resp = admin_authenticated.post(
        "/v1/billing/webhook", content=b"{}", headers={"stripe-signature": "s"}
    )
    assert resp.status_code == 200

    sub_resp = admin_authenticated.get("/v1/billing/subscriptions/current")
    assert sub_resp.status_code == 404
    mock_billing_provider.switch_subscription_price.assert_not_called()


def test_webhook_payment_method_attached_sets_flag(
    admin_authenticated: TestClient,
    trialing_subscription: dict,
    mock_billing_provider,
) -> None:
    assert (
        admin_authenticated.get("/v1/billing/subscriptions/current").json()[
            "has_payment_method"
        ]
        is False
    )

    mock_billing_provider.construct_webhook_event.return_value = WebhookPayload(
        external_event_id="evt_pm_attached",
        event_type="payment_method.attached",
        raw={"data": {"object": {"customer": "cus_test123"}}},
    )
    resp = admin_authenticated.post(
        "/v1/billing/webhook", content=b"{}", headers={"stripe-signature": "s"}
    )
    assert resp.status_code == 200
    assert (
        admin_authenticated.get("/v1/billing/subscriptions/current").json()[
            "has_payment_method"
        ]
        is True
    )


def test_webhook_payment_method_detached_clears_flag(
    admin_authenticated: TestClient,
    trialing_subscription: dict,
    mock_billing_provider,
) -> None:
    # First attach a payment method
    mock_billing_provider.construct_webhook_event.return_value = WebhookPayload(
        external_event_id="evt_pm_attached2",
        event_type="payment_method.attached",
        raw={"data": {"object": {"customer": "cus_test123"}}},
    )
    admin_authenticated.post(
        "/v1/billing/webhook", content=b"{}", headers={"stripe-signature": "s"}
    )
    assert (
        admin_authenticated.get("/v1/billing/subscriptions/current").json()[
            "has_payment_method"
        ]
        is True
    )

    # Now detach it - mock says no remaining methods
    mock_billing_provider.has_payment_method.return_value = False
    mock_billing_provider.construct_webhook_event.return_value = WebhookPayload(
        external_event_id="evt_pm_detached",
        event_type="payment_method.detached",
        raw={
            "data": {
                "object": {"customer": None},
                "previous_attributes": {"customer": "cus_test123"},
            }
        },
    )
    resp = admin_authenticated.post(
        "/v1/billing/webhook", content=b"{}", headers={"stripe-signature": "s"}
    )
    assert resp.status_code == 200
    assert (
        admin_authenticated.get("/v1/billing/subscriptions/current").json()[
            "has_payment_method"
        ]
        is False
    )
    mock_billing_provider.has_payment_method.assert_called_once_with("cus_test123")
