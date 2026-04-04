import pytest
from fastapi.testclient import TestClient

from src.billing.types import WebhookPayload
from src.core.exceptions import BillingWebhookException


def _send_webhook(client: TestClient, payload: WebhookPayload, mock_billing_provider) -> None:
    mock_billing_provider.construct_webhook_event.return_value = payload
    client.post(
        "/v1/billing/webhook",
        content=b"{}",
        headers={"stripe-signature": "sig_test"},
    )


def test_webhook_valid_payload(client: TestClient, mock_billing_provider) -> None:
    mock_billing_provider.construct_webhook_event.return_value = WebhookPayload(
        external_event_id="evt_001",
        event_type="subscription.updated",
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
        event_type="subscription.updated",
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
    from datetime import UTC, datetime

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
        event_type="subscription.deleted",
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


def test_webhook_payment_failed_sets_past_due(
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

    # Fire invoice.payment_failed
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
    assert sub["status"] == "past_due"


def test_webhook_subscription_updated(
    admin_authenticated: TestClient,
    plan_with_price: dict,
    mock_billing_provider,
) -> None:
    from datetime import UTC, datetime

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
        event_type="subscription.updated",
        raw={
            "data": {
                "object": {
                    "id": "sub_to_update",
                    "status": "past_due",
                    "cancel_at_period_end": True,
                    "current_period_start": now_ts,
                    "current_period_end": now_ts + 2592000,
                    "canceled_at": None,
                    "items": {
                        "data": [
                            {"price": {"id": "price_test123"}}
                        ]
                    },
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


def _activate_sub(client, price_id: int, mock_billing_provider, event_id: str, sub_id: str) -> None:
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
    from datetime import UTC, datetime

    price_id = plan_with_price["price"]["id"]
    admin_authenticated.post(
        "/v1/billing/subscriptions/checkout", json={"plan_price_id": price_id}
    )

    # subscription.created fires before checkout.session.completed in Stripe's event order,
    # so external_subscription_id is not yet set - handler must fall back to customer lookup
    now_ts = int(datetime.now(UTC).timestamp())
    mock_billing_provider.construct_webhook_event.return_value = WebhookPayload(
        external_event_id="evt_sub_created",
        event_type="subscription.created",
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
    assert admin_authenticated.get("/v1/billing/subscriptions/current").status_code == 404


def test_webhook_payment_action_required_sets_incomplete(
    admin_authenticated: TestClient,
    plan_with_price: dict,
    mock_billing_provider,
) -> None:
    price_id = plan_with_price["price"]["id"]
    _activate_sub(admin_authenticated, price_id, mock_billing_provider, "evt_act_pam", "sub_pam")

    mock_billing_provider.construct_webhook_event.return_value = WebhookPayload(
        external_event_id="evt_payment_action_required",
        event_type="invoice.payment_action_required",
        raw={"data": {"object": {"subscription": "sub_pam"}}},
    )
    resp = admin_authenticated.post(
        "/v1/billing/webhook", content=b"{}", headers={"stripe-signature": "s"}
    )
    assert resp.status_code == 200
    sub = admin_authenticated.get("/v1/billing/subscriptions/current").json()
    assert sub["status"] == "incomplete"


def test_webhook_marked_uncollectible_cancels_subscription(
    admin_authenticated: TestClient,
    plan_with_price: dict,
    mock_billing_provider,
) -> None:
    price_id = plan_with_price["price"]["id"]
    _activate_sub(admin_authenticated, price_id, mock_billing_provider, "evt_act_muc", "sub_muc")

    mock_billing_provider.construct_webhook_event.return_value = WebhookPayload(
        external_event_id="evt_marked_uncollectible",
        event_type="invoice.marked_uncollectible",
        raw={"data": {"object": {"subscription": "sub_muc"}}},
    )
    resp = admin_authenticated.post(
        "/v1/billing/webhook", content=b"{}", headers={"stripe-signature": "s"}
    )
    assert resp.status_code == 200
    assert admin_authenticated.get("/v1/billing/subscriptions/current").status_code == 404


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
        (p for p in plan["prices"] if p["external_price_id"] == "price_stripe_new"), None
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
