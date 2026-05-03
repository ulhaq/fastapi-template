import pytest
from fastapi.testclient import TestClient
from httpx import Headers
from sqlalchemy import update

from src.enums import AuditAction
from src.models.billing import Subscription
from tests.conftest import TestSessionLocal

SUPERADMIN_EMAIL = "admin@example.org"


@pytest.fixture
def superadmin_authenticated(client: TestClient) -> TestClient:
    rs = client.post(
        "/v1/auth/token",
        data={"username": SUPERADMIN_EMAIL, "password": "password"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    ).json()
    client.headers = Headers({"Authorization": f"Bearer {rs['access_token']}"})
    return client


@pytest.fixture
async def org2_with_paid_subscription() -> None:
    async with TestSessionLocal() as session:
        await session.execute(
            update(Subscription)
            .where(Subscription.organization_id == 2)
            .values(external_subscription_id="sub_ext_test123")
        )
        await session.commit()


# ---------------------------------------------------------------------------
# Auth guard tests (all admin endpoints require superadmin)
# ---------------------------------------------------------------------------


def test_list_organizations_requires_auth(client: TestClient) -> None:
    assert client.get("/v1/admin/organizations").status_code == 401


def test_list_organizations_requires_superadmin(
    standard_authenticated: TestClient,
) -> None:
    assert standard_authenticated.get("/v1/admin/organizations").status_code == 403


def test_list_users_requires_auth(client: TestClient) -> None:
    assert client.get("/v1/admin/users").status_code == 401


def test_list_users_requires_superadmin(standard_authenticated: TestClient) -> None:
    assert standard_authenticated.get("/v1/admin/users").status_code == 403


def test_list_audit_logs_requires_auth(client: TestClient) -> None:
    assert client.get("/v1/admin/audit-logs").status_code == 401


def test_list_audit_logs_requires_superadmin(
    standard_authenticated: TestClient,
) -> None:
    assert standard_authenticated.get("/v1/admin/audit-logs").status_code == 403


def test_patch_organization_requires_superadmin(
    standard_authenticated: TestClient,
) -> None:
    assert (
        standard_authenticated.patch(
            "/v1/admin/organizations/1", json={"name": "X"}
        ).status_code
        == 403
    )


def test_delete_organization_requires_superadmin(
    standard_authenticated: TestClient,
) -> None:
    assert standard_authenticated.delete("/v1/admin/organizations/2").status_code == 403


def test_patch_user_requires_superadmin(standard_authenticated: TestClient) -> None:
    assert (
        standard_authenticated.patch(
            "/v1/admin/users/1", json={"name": "X"}
        ).status_code
        == 403
    )


def test_delete_user_requires_superadmin(standard_authenticated: TestClient) -> None:
    assert standard_authenticated.delete("/v1/admin/users/1").status_code == 403


# ---------------------------------------------------------------------------
# List organizations
# ---------------------------------------------------------------------------


def test_list_organizations_returns_all_orgs(
    superadmin_authenticated: TestClient,
) -> None:
    response = superadmin_authenticated.get("/v1/admin/organizations")
    assert response.status_code == 200
    rs = response.json()
    assert rs["total"] == 2
    names = {item["name"] for item in rs["items"]}
    assert "Acme Corp" in names
    assert "Globex Ltd" in names


def test_list_organizations_response_shape(
    superadmin_authenticated: TestClient,
) -> None:
    rs = superadmin_authenticated.get("/v1/admin/organizations").json()
    assert "items" in rs
    assert "total" in rs
    assert "page_number" in rs
    assert "page_size" in rs
    item = rs["items"][0]
    assert "id" in item
    assert "name" in item
    assert "created_at" in item


# ---------------------------------------------------------------------------
# Patch organization
# ---------------------------------------------------------------------------


def test_patch_organization_renames(superadmin_authenticated: TestClient) -> None:
    response = superadmin_authenticated.patch(
        "/v1/admin/organizations/1", json={"name": "Renamed Corp"}
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Renamed Corp"


def test_patch_organization_404_on_missing(
    superadmin_authenticated: TestClient,
) -> None:
    response = superadmin_authenticated.patch(
        "/v1/admin/organizations/9999", json={"name": "Ghost"}
    )
    assert response.status_code == 404


def test_patch_organization_creates_audit_log(
    superadmin_authenticated: TestClient,
) -> None:
    superadmin_authenticated.patch(
        "/v1/admin/organizations/1", json={"name": "Audited Corp"}
    )
    rs = superadmin_authenticated.get(
        "/v1/admin/audit-logs", params={"action": AuditAction.ORG_UPDATE}
    ).json()
    assert rs["total"] >= 1
    entry = rs["items"][0]
    assert entry["action"] == AuditAction.ORG_UPDATE
    assert entry["resource_type"] == "organization"
    assert entry["resource_id"] == 1
    assert entry["organization_id"] is None


# ---------------------------------------------------------------------------
# Delete organization
# ---------------------------------------------------------------------------


def test_delete_organization_returns_204(superadmin_authenticated: TestClient) -> None:
    response = superadmin_authenticated.delete("/v1/admin/organizations/2")
    assert response.status_code == 204


def test_delete_organization_soft_deletes_solo_users(
    superadmin_authenticated: TestClient,
) -> None:
    # Dave (admin2@example.org) is only in org 2 — deleting org 2 should soft-delete him
    superadmin_authenticated.delete("/v1/admin/organizations/2")
    rs = superadmin_authenticated.get("/v1/admin/users").json()
    emails = {u["email"] for u in rs["items"]}
    assert "admin2@example.org" not in emails


def test_delete_organization_404_on_missing(
    superadmin_authenticated: TestClient,
) -> None:
    assert (
        superadmin_authenticated.delete("/v1/admin/organizations/9999").status_code
        == 404
    )


def test_delete_organization_blocked_by_active_subscription(
    superadmin_authenticated: TestClient,
    org2_with_paid_subscription: None,
) -> None:
    response = superadmin_authenticated.delete("/v1/admin/organizations/2")
    assert response.status_code == 403


def test_delete_organization_creates_audit_log(
    superadmin_authenticated: TestClient,
) -> None:
    superadmin_authenticated.delete("/v1/admin/organizations/2")
    rs = superadmin_authenticated.get(
        "/v1/admin/audit-logs", params={"action": AuditAction.ORG_DELETE}
    ).json()
    assert rs["total"] >= 1
    entry = rs["items"][0]
    assert entry["action"] == AuditAction.ORG_DELETE
    assert entry["resource_type"] == "organization"
    assert entry["organization_id"] is None


# ---------------------------------------------------------------------------
# List users
# ---------------------------------------------------------------------------


def test_list_users_returns_all_users(superadmin_authenticated: TestClient) -> None:
    rs = superadmin_authenticated.get("/v1/admin/users").json()
    assert rs["total"] == 4
    emails = {u["email"] for u in rs["items"]}
    assert "admin@example.org" in emails
    assert "admin2@example.org" in emails


def test_list_users_response_shape(superadmin_authenticated: TestClient) -> None:
    rs = superadmin_authenticated.get("/v1/admin/users").json()
    item = rs["items"][0]
    assert "id" in item
    assert "name" in item
    assert "email" in item
    assert "created_at" in item


# ---------------------------------------------------------------------------
# Patch user
# ---------------------------------------------------------------------------


def test_patch_user_updates_name(superadmin_authenticated: TestClient) -> None:
    response = superadmin_authenticated.patch(
        "/v1/admin/users/2", json={"name": "Bob Updated"}
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Bob Updated"


def test_patch_user_updates_email(superadmin_authenticated: TestClient) -> None:
    response = superadmin_authenticated.patch(
        "/v1/admin/users/2", json={"email": "bob.new@example.org"}
    )
    assert response.status_code == 200
    assert response.json()["email"] == "bob.new@example.org"


def test_patch_user_email_conflict_returns_409(
    superadmin_authenticated: TestClient,
) -> None:
    # Try to assign admin@example.org (user 1) email to user 2
    response = superadmin_authenticated.patch(
        "/v1/admin/users/2", json={"email": "admin@example.org"}
    )
    assert response.status_code == 409


def test_patch_user_404_on_missing(superadmin_authenticated: TestClient) -> None:
    response = superadmin_authenticated.patch(
        "/v1/admin/users/9999", json={"name": "Ghost"}
    )
    assert response.status_code == 404


def test_patch_user_creates_audit_log(superadmin_authenticated: TestClient) -> None:
    superadmin_authenticated.patch("/v1/admin/users/2", json={"name": "Audited Bob"})
    rs = superadmin_authenticated.get(
        "/v1/admin/audit-logs", params={"action": AuditAction.USER_UPDATE}
    ).json()
    assert rs["total"] >= 1
    entry = rs["items"][0]
    assert entry["action"] == AuditAction.USER_UPDATE
    assert entry["resource_type"] == "user"
    assert entry["organization_id"] is None


# ---------------------------------------------------------------------------
# Delete user
# ---------------------------------------------------------------------------


def test_delete_user_returns_204(superadmin_authenticated: TestClient) -> None:
    # Delete Carol (no_roles@example.org) — user ID 3
    response = superadmin_authenticated.delete("/v1/admin/users/3")
    assert response.status_code == 204


def test_delete_user_removes_from_listing(superadmin_authenticated: TestClient) -> None:
    superadmin_authenticated.delete("/v1/admin/users/3")
    rs = superadmin_authenticated.get("/v1/admin/users").json()
    emails = {u["email"] for u in rs["items"]}
    assert "no_roles@example.org" not in emails


def test_delete_user_404_on_missing(superadmin_authenticated: TestClient) -> None:
    assert superadmin_authenticated.delete("/v1/admin/users/9999").status_code == 404


def test_delete_user_creates_audit_log(superadmin_authenticated: TestClient) -> None:
    superadmin_authenticated.delete("/v1/admin/users/3")
    rs = superadmin_authenticated.get(
        "/v1/admin/audit-logs", params={"action": AuditAction.USER_DELETE}
    ).json()
    assert rs["total"] >= 1
    entry = rs["items"][0]
    assert entry["action"] == AuditAction.USER_DELETE
    assert entry["resource_type"] == "user"
    assert entry["organization_id"] is None


# ---------------------------------------------------------------------------
# Admin audit logs — cross-tenant visibility
# ---------------------------------------------------------------------------


def test_admin_audit_logs_sees_all_orgs(
    superadmin_authenticated: TestClient,
    organization2_admin_authenticated: TestClient,
) -> None:
    # Org 2 admin creates a role (generates an audit entry for org 2)
    organization2_admin_authenticated.post(
        "/v1/roles", json={"name": "CrossTenantRole", "description": "x"}
    )

    # Superadmin sees entries from both orgs
    rs = superadmin_authenticated.get(
        "/v1/admin/audit-logs", params={"action": AuditAction.ROLE_CREATE}
    ).json()
    assert rs["total"] >= 1
    org_ids = {e["organization_id"] for e in rs["items"]}
    assert 2 in org_ids


def test_admin_audit_logs_response_shape(
    superadmin_authenticated: TestClient,
) -> None:
    rs = superadmin_authenticated.get("/v1/admin/audit-logs").json()
    assert "items" in rs
    assert "total" in rs
    assert "page_number" in rs
    assert "page_size" in rs
    entry = rs["items"][0]
    assert "id" in entry
    assert "action" in entry
    assert "user_id" in entry
    assert "organization_id" in entry
    assert "created_at" in entry
