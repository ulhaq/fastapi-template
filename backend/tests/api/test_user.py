import pytest
from datetime import UTC, datetime
from fastapi.testclient import TestClient
from httpx import Headers
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.enums import PERMISSION_DESCRIPTIONS, Permission
from src.models.organization import Organization
from src.models.user import User
from tests.conftest import TestSessionLocal
from tests.utils import assert_filtering_of_items_list, assert_pagination, assert_sorting_of_items_list


async def _seed_external_customer(organization_id: int, external_customer_id: str | None) -> None:
    async with TestSessionLocal() as session:
        organization = await session.get(Organization, organization_id)
        organization.external_customer_id = external_customer_id
        await session.commit()


def test_get_authenticated_user(admin_authenticated: TestClient) -> None:
    response = admin_authenticated.get("/v1/users/me")
    assert response.status_code == 200
    rs = response.json()
    assert rs["id"] == 1
    assert rs["name"] == "Admin"
    assert rs["email"] == "admin@example.org"

    assert len(rs["roles"]) == 1
    assert rs["roles"][0]["id"] == 1
    assert rs["roles"][0]["name"] == "Owner"
    assert rs["roles"][0]["is_protected"] is True
    assert (
        rs["roles"][0]["description"]
        == "Full access to all system features and settings."
    )

    permissions = rs["roles"][0]["permissions"]
    assert len(permissions) == len(Permission)

    permission_names = {p["name"] for p in permissions}
    assert permission_names == {p.value for p in Permission}

    for p in permissions:
        assert p["name"] in PERMISSION_DESCRIPTIONS
        assert p["description"] == PERMISSION_DESCRIPTIONS[Permission(p["name"])]

    assert rs["created_at"]
    assert rs["updated_at"]


def test_invite_a_user(admin_authenticated: TestClient, mocker) -> None:
    mocker.patch("src.services.user.send_email")
    response = admin_authenticated.post(
        "/v1/users/invite",
        json={"email": "new@testing.com", "role_ids": []},
    )
    assert response.status_code == 204


def test_patch_authenticated_user_profile(admin_authenticated: TestClient) -> None:
    response = admin_authenticated.patch("/v1/users/me", json={"name": "Admin Patched"})
    assert response.status_code == 200
    rs = response.json()
    assert rs["id"] == 1
    assert rs["name"] == "Admin Patched"
    assert rs["email"] == "admin@example.org"
    assert rs["created_at"]
    assert rs["updated_at"]


def test_patch_authenticated_user_profile_with_partial_body(
    admin_authenticated: TestClient,
) -> None:
    response = admin_authenticated.patch("/v1/users/me", json={})
    assert response.status_code == 200
    rs = response.json()
    assert rs["id"] == 1
    assert rs["name"] == "Admin"
    assert rs["email"] == "admin@example.org"


def test_change_authenticated_user_password(
    admin_authenticated: TestClient, client: TestClient
) -> None:
    response = admin_authenticated.put(
        "/v1/users/me/change-password",
        json={
            "password": "password",
            "new_password": "new password",
            "confirm_password": "new password",
        },
    )
    assert response.status_code == 200
    rs = response.json()
    assert rs["id"] == 1
    assert rs["name"] == "Admin"
    assert rs["email"] == "admin@example.org"

    response = client.post(
        "/v1/auth/token",
        data={"username": "admin@example.org", "password": "new password"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    rs = response.json()
    access_token = rs["access_token"]

    response = client.get(
        "/v1/users/me", headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 200
    rs = response.json()
    assert rs["id"] == 1
    assert rs["name"] == "Admin"
    assert rs["email"] == "admin@example.org"


def test_retrieve_a_user(admin_authenticated: TestClient) -> None:
    response = admin_authenticated.get("/v1/users/2")
    assert response.status_code == 200
    rs = response.json()

    assert rs["id"] == 2
    assert rs["name"] == "Standard"
    assert rs["email"] == "standard@example.org"
    assert len(rs["roles"]) == 1
    assert rs["roles"][0]["id"] == 2
    assert rs["roles"][0]["name"] == "standard"
    assert rs["roles"][0]["description"] == "Access to manage and view own resources."

    permissions = rs["roles"][0]["permissions"]
    assert len(permissions) == 1

    permission_names = {p["name"] for p in permissions}
    assert permission_names == {"read:user"}

    for p in permissions:
        assert p["name"] in PERMISSION_DESCRIPTIONS
        assert p["description"] == PERMISSION_DESCRIPTIONS[Permission(p["name"])]

    assert rs["created_at"]
    assert rs["updated_at"]


def test_manage_roles_of_a_user(admin_authenticated: TestClient) -> None:
    # Assign the standard role to user 3 (who currently has no roles)
    response = admin_authenticated.post(
        "/v1/users/3/roles",
        json={"role_ids": [2]},
    )
    assert response.status_code == 200
    rs = response.json()
    assert rs["id"] == 3
    assert len(rs["roles"]) == 1
    assert rs["roles"][0]["id"] == 2
    assert rs["roles"][0]["name"] == "standard"

    # Remove all roles from user 3
    response = admin_authenticated.post(
        "/v1/users/3/roles",
        json={"role_ids": []},
    )
    assert response.status_code == 200
    rs = response.json()
    assert rs["id"] == 3
    assert len(rs["roles"]) == 0



def test_cannot_manage_own_roles(admin_authenticated: TestClient) -> None:
    response = admin_authenticated.post(
        "/v1/users/1/roles",
        json={
            "role_ids": [1, 2],
        },
    )

    assert response.status_code == 403
    rs = response.json()
    assert rs["msg"] == "You are not allowed to manage your own roles"


def test_cannot_invite_a_user_while_unauthorized(client: TestClient) -> None:
    rs = client.post(
        "/v1/auth/token",
        data={"username": "no_roles@example.org", "password": "password"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    ).json()

    response = client.post(
        "/v1/users/invite",
        json={"email": "new@testing.com", "role_ids": []},
        headers={"Authorization": f"Bearer {rs['access_token']}"},
    )
    assert response.status_code == 403
    rs = response.json()
    assert rs["msg"] == "You are not authorized to perform this action"



def test_patch_a_user(admin_authenticated: TestClient) -> None:
    response = admin_authenticated.patch("/v1/users/2", json={"name": "Standard Patched", "email": "patched@example.org"})
    assert response.status_code == 200
    rs = response.json()
    assert rs["id"] == 2
    assert rs["name"] == "Standard Patched"
    assert rs["email"] == "patched@example.org"
    assert rs["created_at"]
    assert rs["updated_at"]


def test_patch_a_user_with_partial_body(admin_authenticated: TestClient) -> None:
    response = admin_authenticated.patch("/v1/users/2", json={"name": "Only Name"})
    assert response.status_code == 200
    rs = response.json()
    assert rs["id"] == 2
    assert rs["name"] == "Only Name"
    assert rs["email"] == "standard@example.org"


def test_cannot_patch_a_user_with_duplicate_email(admin_authenticated: TestClient) -> None:
    response = admin_authenticated.patch("/v1/users/2", json={"email": "admin@example.org"})
    assert response.status_code == 409
    rs = response.json()
    assert "already exists" in rs["msg"]


def test_cannot_patch_a_user_while_unauthorized(standard_authenticated: TestClient) -> None:
    response = standard_authenticated.patch("/v1/users/1", json={"name": "Hacked"})
    assert response.status_code == 403
    rs = response.json()
    assert rs["msg"] == "You are not authorized to perform this action"


def test_cannot_remove_last_owner_via_manage_roles(
    admin_authenticated: TestClient, client: TestClient
) -> None:
    # Get the MANAGE_USER_ROLE permission ID
    rs = admin_authenticated.get("/v1/permissions?page_size=50").json()
    manage_role_perm_id = next(
        p["id"] for p in rs["items"] if p["name"] == "manage:user_role"
    )

    # Create a role with only MANAGE_USER_ROLE (not Owner)
    rs = admin_authenticated.post(
        "/v1/roles", json={"name": "Manager", "description": "Role manager"}
    ).json()
    manager_role_id = rs["id"]
    admin_authenticated.post(
        f"/v1/roles/{manager_role_id}/permissions",
        json={"permission_ids": [manage_role_perm_id]},
    )

    # Assign Manager role to user 2 (standard user)
    admin_authenticated.post("/v1/users/2/roles", json={"role_ids": [manager_role_id]})

    # Login as user 2 (has MANAGE_USER_ROLE but not Owner role)
    rs = client.post(
        "/v1/auth/token",
        data={"username": "standard@example.org", "password": "password"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    ).json()

    client.headers = Headers({"Authorization": f"Bearer {rs['access_token']}"})

    # Try to remove Owner from user 1 (the only Owner) > should fail
    response = client.post("/v1/users/1/roles", json={"role_ids": []})
    assert response.status_code == 403
    rs = response.json()
    assert rs["error_code"] == "protected_role_modification"


async def test_patch_profile_email_syncs_to_stripe_when_owner(
    admin_authenticated: TestClient, mock_billing_provider
) -> None:
    await _seed_external_customer(organization_id=1, external_customer_id="cus_test123")

    response = admin_authenticated.patch(
        "/v1/users/me", json={"email": "new_owner@example.org"}
    )
    assert response.status_code == 200
    assert response.json()["email"] == "new_owner@example.org"

    mock_billing_provider.update_customer.assert_called_once_with(
        "cus_test123", email="new_owner@example.org"
    )


async def test_patch_profile_email_does_not_sync_when_not_owner(
    standard_authenticated: TestClient, mock_billing_provider
) -> None:
    await _seed_external_customer(organization_id=1, external_customer_id="cus_test123")

    response = standard_authenticated.patch(
        "/v1/users/me", json={"email": "new_standard@example.org"}
    )
    assert response.status_code == 200

    mock_billing_provider.update_customer.assert_not_called()


async def test_patch_profile_email_no_sync_without_external_customer(
    admin_authenticated: TestClient, mock_billing_provider
) -> None:
    # Clear external_customer_id - simulates a organization whose Stripe customer
    # creation failed at registration. No sync should happen in that case.
    await _seed_external_customer(organization_id=1, external_customer_id=None)

    response = admin_authenticated.patch(
        "/v1/users/me", json={"email": "new_owner@example.org"}
    )
    assert response.status_code == 200

    mock_billing_provider.update_customer.assert_not_called()


# --- GET /v1/users ---


def test_get_all_users(admin_authenticated: TestClient) -> None:
    response = admin_authenticated.get("/v1/users")
    assert response.status_code == 200
    rs = response.json()
    assert rs["page_number"] == 1
    assert rs["page_size"] == 10
    assert rs["total"] == 3
    assert len(rs["items"]) == 3
    emails = {u["email"] for u in rs["items"]}
    assert emails == {"admin@example.org", "standard@example.org", "no_roles@example.org"}


@pytest.mark.parametrize(
    "page_number, page_size, page_total, total",
    [
        pytest.param(1, 10, 3, 3),
        pytest.param(2, 10, 0, 3),
    ],
)
def test_paginate_users(
    page_number: int,
    page_size: int,
    page_total: int,
    total: int,
    admin_authenticated: TestClient,
) -> None:
    response = admin_authenticated.get(
        f"/v1/users?page_number={page_number}&page_size={page_size}"
    )
    assert response.status_code == 200
    assert_pagination(response.json(), page_number, page_size, page_total, total)


@pytest.mark.parametrize("sort", ["id", "-id", "name", "-name", "created_at", "-created_at"])
def test_sort_users(sort: str, admin_authenticated: TestClient) -> None:
    response = admin_authenticated.get(f"/v1/users?sort={sort}&page_size=50")
    assert response.status_code == 200
    assert_sorting_of_items_list(response.json()["items"], [sort])


@pytest.mark.parametrize(
    "fields,values,operators",
    [
        (["name"], [["Admin"]], ["eq"]),
        (["name"], [["dmin"]], ["ico"]),
    ],
)
def test_filter_users(
    fields: list,
    values: list,
    operators: list,
    admin_authenticated: TestClient,
) -> None:
    import json

    filters = {
        field: {"v": value, "op": op}
        for field, value, op in zip(fields, values, operators)
    }
    response = admin_authenticated.get(f"/v1/users?filters={json.dumps(filters)}&page_size=50")
    assert response.status_code == 200
    filter_data = list(zip(fields, values, operators))
    assert_filtering_of_items_list(response.json()["items"], filter_data)


def test_cannot_get_users_while_unauthorized(client: TestClient) -> None:
    rs = client.post(
        "/v1/auth/token",
        data={"username": "no_roles@example.org", "password": "password"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    ).json()
    response = client.get(
        "/v1/users",
        headers={"Authorization": f"Bearer {rs['access_token']}"},
    )
    assert response.status_code == 403
    assert response.json()["msg"] == "You are not authorized to perform this action"


def test_cannot_assign_owner_role_via_manage_roles(
    admin_authenticated: TestClient,
) -> None:
    response = admin_authenticated.post("/v1/users/3/roles", json={"role_ids": [1]})
    assert response.status_code == 403
    rs = response.json()
    assert rs["error_code"] == "protected_role_modification"


def test_cannot_remove_owner_role_via_manage_roles(
    admin_authenticated: TestClient, client: TestClient
) -> None:
    # Give user 2 a role with MANAGE_USER_ROLE so they can call manage_roles
    rs = admin_authenticated.get("/v1/permissions?page_size=50").json()
    manage_role_perm_id = next(
        p["id"] for p in rs["items"] if p["name"] == "manage:user_role"
    )
    rs = admin_authenticated.post(
        "/v1/roles", json={"name": "Manager", "description": "Role manager"}
    ).json()
    manager_role_id = rs["id"]
    admin_authenticated.post(
        f"/v1/roles/{manager_role_id}/permissions",
        json={"permission_ids": [manage_role_perm_id]},
    )
    admin_authenticated.post("/v1/users/2/roles", json={"role_ids": [manager_role_id]})

    # Login as user 2 and try to strip user 1's Owner role
    rs = client.post(
        "/v1/auth/token",
        data={"username": "standard@example.org", "password": "password"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    ).json()
    client.headers = Headers({"Authorization": f"Bearer {rs['access_token']}"})

    response = client.post("/v1/users/1/roles", json={"role_ids": []})
    assert response.status_code == 403
    rs = response.json()
    assert rs["error_code"] == "protected_role_modification"



def test_deleted_role_excluded_from_user_roles(admin_authenticated: TestClient) -> None:
    # Standard user (id=2) starts with the "standard" role
    response = admin_authenticated.get("/v1/users/2")
    assert response.status_code == 200
    assert len(response.json()["roles"]) == 1
    assert response.json()["roles"][0]["name"] == "standard"

    # Admin soft-deletes the role
    response = admin_authenticated.delete("/v1/roles/2")
    assert response.status_code == 204

    # The soft-deleted role must not appear in the user's roles
    response = admin_authenticated.get("/v1/users/2")
    assert response.status_code == 200
    assert response.json()["roles"] == []



async def test_deleted_user_excluded_from_organization_users() -> None:
    # Soft-delete the standard user (id=2) directly
    async with TestSessionLocal() as session:
        user = await session.get(User, 2)
        user.deleted_at = datetime.now(UTC)
        await session.commit()

    # Load org 1 via the relationship and verify the soft-deleted user is excluded
    async with TestSessionLocal() as session:
        result = await session.execute(
            select(Organization)
            .where(Organization.id == 1)
            .options(selectinload(Organization.users))
        )
        org = result.scalar_one()
        user_ids = {u.id for u in org.users}
        assert 1 in user_ids       # admin still present
        assert 2 not in user_ids   # soft-deleted user excluded
