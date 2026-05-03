import json
from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from src.enums import PERMISSION_DESCRIPTIONS, Permission
from src.models.permission import Permission as PermissionModel
from tests.conftest import TestSessionLocal
from tests.utils import (
    assert_filtering_of_items_list,
    assert_pagination,
    assert_sorting_of_items_list,
)

TOTAL_PERMISSIONS = len(Permission)


def _assert_all_permissions(permissions: list[dict]) -> None:
    assert len(permissions) == TOTAL_PERMISSIONS
    perm_names = {p["name"] for p in permissions}
    assert perm_names == {p.value for p in Permission}
    for p in permissions:
        assert p["description"] == PERMISSION_DESCRIPTIONS[Permission(p["name"])]


def test_get_all_roles(admin_authenticated: TestClient) -> None:
    response = admin_authenticated.get("/v1/roles")
    assert response.status_code == 200
    rs = response.json()
    assert rs["page_number"] == 1
    assert rs["page_size"] == 10
    assert rs["total"] == 3

    assert len(rs["items"]) == 3
    assert rs["items"][0]["id"] == 1
    assert rs["items"][0]["name"] == "Owner"
    assert (
        rs["items"][0]["description"]
        == "Full access to all system features and settings."
    )
    assert rs["items"][0]["is_protected"] is True

    _assert_all_permissions(rs["items"][0]["permissions"])
    assert rs["items"][0]["created_at"]
    assert rs["items"][0]["updated_at"]

    assert rs["items"][1]["id"] == 2
    assert rs["items"][1]["name"] == "Admin"
    assert (
        rs["items"][1]["description"]
        == "Access to manage users, roles, organization settings, and billing."
    )
    assert rs["items"][1]["is_protected"] is False
    assert len(rs["items"][1]["permissions"]) == 12
    assert rs["items"][1]["created_at"]
    assert rs["items"][1]["updated_at"]

    assert rs["items"][2]["id"] == 3
    assert rs["items"][2]["name"] == "Member"
    assert (
        rs["items"][2]["description"]
        == "Read-only access to users, roles, and organization settings."
    )
    assert rs["items"][2]["is_protected"] is False
    assert len(rs["items"][2]["permissions"]) == 4
    member_perm_names = {p["name"] for p in rs["items"][2]["permissions"]}
    assert member_perm_names == {
        "read:user",
        "read:role",
        "read:permission",
        "manage:api_token",
    }
    assert rs["items"][2]["created_at"]
    assert rs["items"][2]["updated_at"]


@pytest.mark.parametrize(
    "page_number, page_size, page_total, total",
    [
        pytest.param(1, 10, 3, 3),
        pytest.param(2, 10, 0, 3),
    ],
)
def test_paginate_roles(
    page_number: int,
    page_size: int,
    page_total: int,
    total: int,
    admin_authenticated: TestClient,
) -> None:
    response = admin_authenticated.get(
        f"/v1/roles?page_number={page_number}&page_size{page_size}"
    )
    assert response.status_code == 200
    rs = response.json()

    assert_pagination(rs, page_number, page_size, page_total, total)


@pytest.mark.parametrize(
    "sort",
    [
        pytest.param("id"),
        pytest.param("-id"),
        pytest.param("name"),
        pytest.param("-name"),
        pytest.param("description"),
        pytest.param("-description"),
        pytest.param("name,description"),
        pytest.param("-name,-description"),
        pytest.param("-name,description"),
        pytest.param("name,-description"),
        pytest.param("created_at"),
        pytest.param("-created_at"),
        pytest.param("updated_at"),
        pytest.param("-updated_at"),
    ],
)
def test_sort_roles(sort: str, admin_authenticated: TestClient) -> None:
    response = admin_authenticated.get(f"/v1/roles?sort={sort}")
    assert response.status_code == 200
    rs = response.json()

    assert_sorting_of_items_list(rs["items"], sort.split(","))


@pytest.mark.parametrize(
    "fields,values,operators,total_page",
    [
        pytest.param(["id"], [[1]], ["eq"], 1),
        pytest.param(["id"], [[0, 1]], ["between"], 1),
        pytest.param(["id"], [[1, 2]], ["between"], 2),
        pytest.param(["id"], [[2, 3]], ["between"], 2),
        pytest.param(["id", "name"], [[1], ["a"]], ["eq", "co"], 2),
        pytest.param(["name"], [["Owner"]], ["eq"], 1),
        pytest.param(["name"], [["n"]], ["co"], 2),
        pytest.param(["description"], [["access"]], ["ico"], 3),
        pytest.param(
            ["created_at"],
            [["2025-04-22T14:04:38.586226", "2050-09-22T14:04:38.586226"]],
            ["between"],
            3,
        ),
    ],
)
def test_filter_roles(
    fields: list[str],
    values: list[list],
    operators: list[str],
    total_page: int,
    admin_authenticated: TestClient,
) -> None:
    filter_data = zip(fields, values, operators, strict=False)
    filters = {}

    for field, value, op in filter_data:
        filters[field] = {"v": [*value], "op": op}

    response = admin_authenticated.get(f"/v1/roles?filters={json.dumps(filters)}")
    assert response.status_code == 200
    rs = response.json()

    assert len(rs["items"]) == total_page

    assert_filtering_of_items_list(rs["items"], filter_data)


def test_create_a_role(admin_authenticated: TestClient) -> None:
    response = admin_authenticated.post(
        "/v1/roles",
        json={
            "name": "test role",
            "description": "description of test role",
        },
    )
    assert response.status_code == 201
    rs = response.json()
    assert rs["id"] == 7
    assert rs["name"] == "test role"
    assert rs["description"] == "description of test role"
    assert rs["organization_id"] == 1

    assert rs["permissions"] == []

    assert rs["created_at"]
    assert rs["updated_at"]


def test_patch_a_role(admin_authenticated: TestClient) -> None:
    response = admin_authenticated.patch(
        "/v1/roles/2",
        json={
            "name": "Basic",
            "description": "Basic Access",
        },
    )
    assert response.status_code == 200
    rs = response.json()
    assert rs["id"] == 2
    assert rs["name"] == "Basic"
    assert rs["description"] == "Basic Access"
    assert rs["created_at"]
    assert rs["updated_at"]


def test_patch_a_role_with_partial_body(admin_authenticated: TestClient) -> None:
    response = admin_authenticated.patch("/v1/roles/2", json={})
    assert response.status_code == 200
    rs = response.json()
    assert rs["id"] == 2
    assert rs["name"] == "Admin"
    assert (
        rs["description"]
        == "Access to manage users, roles, organization settings, and billing."
    )


def test_retrieve_a_role(admin_authenticated: TestClient) -> None:
    response = admin_authenticated.get("/v1/roles/1")
    assert response.status_code == 200
    rs = response.json()

    assert rs["id"] == 1
    assert rs["name"] == "Owner"
    assert rs["description"] == "Full access to all system features and settings."
    assert rs["is_protected"] is True

    _assert_all_permissions(rs["permissions"])

    assert rs["created_at"]
    assert rs["updated_at"]


def test_manage_permissions_of_a_role(admin_authenticated: TestClient) -> None:
    response = admin_authenticated.get("/v1/permissions?page_size=50")
    all_perms = response.json()["items"]
    user_perm_ids = [
        p["id"]
        for p in all_perms
        if "user" in p["name"] or "role" in p["name"] or "permission" in p["name"]
    ]

    response = admin_authenticated.post(
        "/v1/roles/2/permissions",
        json={
            "permission_ids": user_perm_ids,
        },
    )
    assert response.status_code == 200
    rs = response.json()
    assert rs["id"] == 2
    assert rs["name"] == "Admin"
    assert len(rs["permissions"]) == len(user_perm_ids)

    assert rs["created_at"]
    assert rs["updated_at"]

    update_organization_id = next(
        p["id"] for p in all_perms if p["name"] == "update:organization"
    )
    response = admin_authenticated.post(
        "/v1/roles/2/permissions",
        json={
            "permission_ids": [update_organization_id],
        },
    )
    assert response.status_code == 200
    rs = response.json()
    assert rs["id"] == 2
    assert rs["name"] == "Admin"

    assert len(rs["permissions"]) == 1
    assert rs["permissions"][0]["name"] == "update:organization"
    assert (
        rs["permissions"][0]["description"]
        == "Allows the user to update organization accounts."
    )

    assert rs["created_at"]
    assert rs["updated_at"]


def test_delete_a_role(admin_authenticated: TestClient) -> None:
    response = admin_authenticated.delete("/v1/roles/2")
    assert response.status_code == 204

    response = admin_authenticated.get("/v1/roles/2")
    assert response.status_code == 404


def test_cannot_get_non_existent_role(admin_authenticated: TestClient) -> None:
    response = admin_authenticated.get("/v1/roles/0")
    assert response.status_code == 404
    rs = response.json()
    assert rs["msg"] == "Role not found. [identifier=0]"


def test_cannot_create_a_role_with_already_existing_name(
    admin_authenticated: TestClient,
) -> None:
    response = admin_authenticated.post(
        "/v1/roles",
        json={
            "name": "Owner",
            "description": "description of test role",
        },
    )
    assert response.status_code == 409
    rs = response.json()
    assert rs["msg"] == "Role already exists. [name=Owner]"


def test_cannot_patch_protected_role(admin_authenticated: TestClient) -> None:
    response = admin_authenticated.patch("/v1/roles/1", json={"name": "Hacked"})
    assert response.status_code == 403
    rs = response.json()
    assert rs["error_code"] == "protected_role_modification"


def test_cannot_delete_protected_role(admin_authenticated: TestClient) -> None:
    response = admin_authenticated.delete("/v1/roles/1")
    assert response.status_code == 403
    rs = response.json()
    assert rs["error_code"] == "protected_role_modification"


def test_cannot_manage_permissions_of_protected_role(
    admin_authenticated: TestClient,
) -> None:
    response = admin_authenticated.post(
        "/v1/roles/1/permissions", json={"permission_ids": [1]}
    )
    assert response.status_code == 403
    rs = response.json()
    assert rs["error_code"] == "protected_role_modification"


def test_cannot_patch_a_role_while_unauthorized(
    standard_authenticated: TestClient,
) -> None:
    response = standard_authenticated.patch(
        "/v1/roles/1",
        json={"name": "Administrator"},
    )
    assert response.status_code == 403
    rs = response.json()
    assert rs["msg"] == "You are not authorized to perform this action"


def test_cannot_get_roles_while_unauthorized(
    no_roles_authenticated: TestClient,
) -> None:
    response = no_roles_authenticated.get("/v1/roles")
    assert response.status_code == 403
    rs = response.json()
    assert rs["msg"] == "You are not authorized to perform this action"


def test_cannot_retrieve_a_role_while_unauthorized(
    no_roles_authenticated: TestClient,
) -> None:
    response = no_roles_authenticated.get("/v1/roles/1")
    assert response.status_code == 403
    rs = response.json()
    assert rs["msg"] == "You are not authorized to perform this action"


def test_cannot_delete_a_role_while_unauthorized(
    standard_authenticated: TestClient,
) -> None:
    response = standard_authenticated.delete("/v1/roles/1")
    assert response.status_code == 403
    rs = response.json()
    assert rs["msg"] == "You are not authorized to perform this action"


def test_cannot_manage_a_role_while_unauthorized(
    standard_authenticated: TestClient,
) -> None:
    response = standard_authenticated.post(
        "/v1/roles/1/permissions",
        json={
            "permission_ids": [1],
        },
    )
    assert response.status_code == 403
    rs = response.json()
    assert rs["msg"] == "You are not authorized to perform this action"


async def test_deleted_permission_excluded_from_role_permissions(
    admin_authenticated: TestClient,
) -> None:
    # Role 3 "Member" starts with read:user among its permissions
    response = admin_authenticated.get("/v1/roles/3")
    assert response.status_code == 200
    perm_names = {p["name"] for p in response.json()["permissions"]}
    assert Permission.READ_USER.value in perm_names

    # Soft-delete read:user directly via DB (no API endpoint exists for this)
    async with TestSessionLocal() as session:
        result = await session.execute(
            select(PermissionModel).where(
                PermissionModel.name == Permission.READ_USER.value
            )
        )
        permission = result.scalar_one()
        permission.deleted_at = datetime.now(UTC)
        await session.commit()

    # The soft-deleted permission must not appear in the role's permissions
    response = admin_authenticated.get("/v1/roles/3")
    assert response.status_code == 200
    perm_names = {p["name"] for p in response.json()["permissions"]}
    assert Permission.READ_USER.value not in perm_names
