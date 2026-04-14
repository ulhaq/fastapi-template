from unittest.mock import MagicMock

from fastapi.testclient import TestClient


def test_user_tenants_list_only_shows_own_tenant(
    tenant2_admin_authenticated: TestClient,
) -> None:
    response = tenant2_admin_authenticated.get("/v1/tenants")
    assert response.status_code == 200
    rs = response.json()
    assert len(rs) == 1
    assert rs[0]["name"] == "Tenant 2"


def test_create_a_tenant(admin_authenticated: TestClient) -> None:
    response = admin_authenticated.post(
        "/v1/tenants",
        json={
            "name": "test tenant",
        },
    )
    assert response.status_code == 201
    rs = response.json()
    assert rs["id"] == 3
    assert rs["name"] == "test tenant"
    assert rs["created_at"]
    assert rs["updated_at"]

    # Creator should be a member and have owner access
    response = admin_authenticated.get("/v1/tenants/3")
    assert response.status_code == 200

    response = admin_authenticated.get("/v1/tenants/3/users")
    assert response.status_code == 200
    rs = response.json()
    assert rs["total"] == 1
    assert rs["items"][0]["roles"][0]["name"] == "Owner"


def test_cannot_create_a_tenant_with_already_existing_name(
    admin_authenticated: TestClient,
) -> None:
    response = admin_authenticated.post(
        "/v1/tenants",
        json={
            "name": "Tenant 1",
        },
    )
    assert response.status_code == 409
    rs = response.json()
    assert rs["msg"] == "Tenant already exists. [name=Tenant 1]"


def test_create_a_tenant_creates_incomplete_subscription(
    admin_authenticated: TestClient,
    mock_billing_provider: MagicMock,
) -> None:
    admin_authenticated.post("/v1/tenants", json={"name": "billed tenant"})

    mock_billing_provider.get_or_create_customer.assert_called_once()
    # Subscription is no longer created directly via provider during tenant
    # setup - the user must complete Stripe Checkout to start the trial.
    mock_billing_provider.create_subscription.assert_not_called()


def test_patch_a_tenant(admin_authenticated: TestClient) -> None:
    response = admin_authenticated.patch(
        "/v1/tenants/1",
        json={"name": "Patched Tenant"},
    )
    assert response.status_code == 200
    rs = response.json()
    assert rs["id"] == 1
    assert rs["name"] == "Patched Tenant"
    assert rs["created_at"]
    assert rs["updated_at"]


def test_patch_a_tenant_with_partial_body(admin_authenticated: TestClient) -> None:
    response = admin_authenticated.patch("/v1/tenants/1", json={})
    assert response.status_code == 200
    rs = response.json()
    assert rs["id"] == 1
    assert rs["name"] == "Tenant 1"


def test_retrieve_a_tenant(admin_authenticated: TestClient) -> None:
    response = admin_authenticated.get("/v1/tenants/1")
    assert response.status_code == 200
    rs = response.json()

    assert rs["id"] == 1
    assert rs["name"] == "Tenant 1"
    assert rs["created_at"]
    assert rs["updated_at"]


def test_delete_a_tenant(admin_authenticated: TestClient) -> None:
    response = admin_authenticated.delete("/v1/tenants/1")
    assert response.status_code == 204

    response = admin_authenticated.get("/v1/tenants/1")
    assert response.status_code == 404


def test_cannot_access_other_tenant(admin_authenticated: TestClient) -> None:
    response = admin_authenticated.get("/v1/tenants/2")
    assert response.status_code == 403

    response = admin_authenticated.patch("/v1/tenants/2", json={"name": "Hacked"})
    assert response.status_code == 403

    response = admin_authenticated.delete("/v1/tenants/2")
    assert response.status_code == 403


def test_cannot_patch_a_tenant_while_unauthorized(
    standard_authenticated: TestClient,
) -> None:
    response = standard_authenticated.patch(
        "/v1/tenants/1",
        json={"name": "Patched Tenant"},
    )
    assert response.status_code == 403
    rs = response.json()
    assert rs["msg"] == "You are not authorized to perform this action"


def test_cannot_retrieve_a_tenant_while_unauthorized(
    standard_authenticated: TestClient,
) -> None:
    response = standard_authenticated.get("/v1/tenants/1")
    assert response.status_code == 403
    rs = response.json()
    assert rs["msg"] == "You are not authorized to perform this action"


def test_cannot_delete_a_tenant_while_unauthorized(
    standard_authenticated: TestClient,
) -> None:
    response = standard_authenticated.delete("/v1/tenants/1")
    assert response.status_code == 403
    rs = response.json()
    assert rs["msg"] == "You are not authorized to perform this action"
