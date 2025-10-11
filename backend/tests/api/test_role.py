import json
from fastapi.testclient import TestClient
import pytest

from tests.utils import (
    assert_filtering_of_items_list,
    assert_pagination,
    assert_sorting_of_items_list,
)


def test_get_all_roles(admin_authenticated: TestClient) -> None:
    response = admin_authenticated.get("/roles")
    assert response.status_code == 200
    rs = response.json()
    assert rs["page_number"] == 1
    assert rs["page_size"] == 10
    assert rs["total"] == 2

    assert rs["items"][0]["id"] == 1
    assert rs["items"][0]["name"] == "admin"
    assert (
        rs["items"][0]["description"]
        == "Full access to all system features and settings."
    )

    assert len(rs["items"]) == 2
    assert rs["items"][0]["id"] == 1
    assert rs["items"][0]["name"] == "admin"
    assert (
        rs["items"][0]["description"]
        == "Full access to all system features and settings."
    )

    assert len(rs["items"][0]["permissions"]) == 14
    assert rs["items"][0]["permissions"][0]["id"] == 1
    assert rs["items"][0]["permissions"][0]["name"] == "read_user"
    assert (
        rs["items"][0]["permissions"][0]["description"]
        == "Allows the user to read user accounts."
    )

    assert rs["items"][0]["permissions"][1]["id"] == 2
    assert rs["items"][0]["permissions"][1]["name"] == "create_user"
    assert (
        rs["items"][0]["permissions"][1]["description"]
        == "Allows the user to create new user accounts."
    )

    assert rs["items"][0]["permissions"][2]["id"] == 3
    assert rs["items"][0]["permissions"][2]["name"] == "update_user"
    assert (
        rs["items"][0]["permissions"][2]["description"]
        == "Allows the user to update user accounts."
    )

    assert rs["items"][0]["permissions"][3]["id"] == 4
    assert rs["items"][0]["permissions"][3]["name"] == "delete_user"
    assert (
        rs["items"][0]["permissions"][3]["description"]
        == "Allows the user to delete user accounts."
    )

    assert rs["items"][0]["permissions"][4]["id"] == 5
    assert rs["items"][0]["permissions"][4]["name"] == "read_role"
    assert (
        rs["items"][0]["permissions"][4]["description"]
        == "Allows the user to read roles."
    )

    assert rs["items"][0]["permissions"][5]["id"] == 6
    assert rs["items"][0]["permissions"][5]["name"] == "create_role"
    assert (
        rs["items"][0]["permissions"][5]["description"]
        == "Allows the user to create new roles."
    )

    assert rs["items"][0]["permissions"][6]["id"] == 7
    assert rs["items"][0]["permissions"][6]["name"] == "update_role"
    assert (
        rs["items"][0]["permissions"][6]["description"]
        == "Allows the user to update roles."
    )

    assert rs["items"][0]["permissions"][7]["id"] == 8
    assert rs["items"][0]["permissions"][7]["name"] == "delete_role"
    assert (
        rs["items"][0]["permissions"][7]["description"]
        == "Allows the user to delete roles."
    )

    assert rs["items"][0]["permissions"][8]["id"] == 9
    assert rs["items"][0]["permissions"][8]["name"] == "manage_user_role"
    assert (
        rs["items"][0]["permissions"][8]["description"]
        == "Allows the user to manage users' roles."
    )

    assert rs["items"][0]["permissions"][9]["id"] == 10
    assert rs["items"][0]["permissions"][9]["name"] == "read_permission"
    assert (
        rs["items"][0]["permissions"][9]["description"]
        == "Allows the user to read permissions."
    )

    assert rs["items"][0]["permissions"][10]["id"] == 11
    assert rs["items"][0]["permissions"][10]["name"] == "create_permission"
    assert (
        rs["items"][0]["permissions"][10]["description"]
        == "Allows the user to create new permissions."
    )

    assert rs["items"][0]["permissions"][11]["id"] == 12
    assert rs["items"][0]["permissions"][11]["name"] == "update_permission"
    assert (
        rs["items"][0]["permissions"][11]["description"]
        == "Allows the user to update permissions."
    )

    assert rs["items"][0]["permissions"][12]["id"] == 13
    assert rs["items"][0]["permissions"][12]["name"] == "delete_permission"
    assert (
        rs["items"][0]["permissions"][12]["description"]
        == "Allows the user to delete permissions."
    )

    assert rs["items"][0]["permissions"][13]["id"] == 14
    assert rs["items"][0]["permissions"][13]["name"] == "manage_role_permission"
    assert (
        rs["items"][0]["permissions"][13]["description"]
        == "Allows the user to manage roles' permissions."
    )

    assert rs["items"][0]["created_at"]
    assert rs["items"][0]["updated_at"]

    assert rs["items"][1]["id"] == 2
    assert rs["items"][1]["name"] == "standard"
    assert rs["items"][1]["description"] == "Access to manage and view own resources."

    assert len(rs["items"][1]["permissions"]) == 2
    assert rs["items"][0]["permissions"][0]["id"] == 1
    assert rs["items"][0]["permissions"][0]["name"] == "read_user"
    assert (
        rs["items"][0]["permissions"][0]["description"]
        == "Allows the user to read user accounts."
    )

    assert rs["items"][0]["permissions"][1]["id"] == 2
    assert rs["items"][0]["permissions"][1]["name"] == "create_user"
    assert (
        rs["items"][0]["permissions"][1]["description"]
        == "Allows the user to create new user accounts."
    )

    assert rs["items"][1]["created_at"]
    assert rs["items"][1]["updated_at"]


@pytest.mark.parametrize(
    "page_number, page_size, page_total, total",
    [
        pytest.param(1, 10, 2, 2),
        pytest.param(2, 10, 0, 2),
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
        f"/roles?page_number={page_number}&page_size{page_size}"
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
    response = admin_authenticated.get(f"/roles?sort={sort}")
    assert response.status_code == 200
    rs = response.json()

    assert_sorting_of_items_list(rs["items"], sort.split(","))


@pytest.mark.parametrize(
    "fields,values,operators,total_page",
    [
        pytest.param(["id"], [[1]], ["eq"], 1),
        pytest.param(["id"], [[0, 1]], ["between"], 1),
        pytest.param(["id"], [[1, 2]], ["between"], 2),
        pytest.param(["id"], [[2, 3]], ["between"], 1),
        pytest.param(["id", "name"], [[1], ["a"]], ["eq", "co"], 2),
        pytest.param(["name"], [["admin"]], ["eq"], 1),
        pytest.param(["name"], [["a", "d"]], ["co"], 2),
        pytest.param(["description"], [["access"]], ["ico"], 2),
        pytest.param(
            ["created_at"],
            [["2025-04-22T14:04:38.586226", "2050-09-22T14:04:38.586226"]],
            ["between"],
            2,
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
    filter_data = zip(fields, values, operators)
    filters = {}

    for field, value, op in filter_data:
        filters[field] = {"v": [*value], "op": op}

    response = admin_authenticated.get(f"/roles?filters={json.dumps(filters)}")
    assert response.status_code == 200
    rs = response.json()

    assert len(rs["items"]) == total_page

    assert_filtering_of_items_list(rs["items"], filter_data)


def test_create_a_role(admin_authenticated: TestClient) -> None:
    response = admin_authenticated.post(
        "/roles",
        json={
            "name": "test role",
            "description": "description of test role",
        },
    )
    assert response.status_code == 201
    rs = response.json()
    assert rs["id"] == 3
    assert rs["name"] == "test role"
    assert rs["description"] == "description of test role"

    assert rs["permissions"] == []

    assert rs["created_at"]
    assert rs["updated_at"]


def test_update_a_role(admin_authenticated: TestClient) -> None:
    response = admin_authenticated.put(
        "/roles/1",
        json={
            "name": "Administrator",
            "description": "Full access to all system features and settings.",
        },
    )
    assert response.status_code == 200
    rs = response.json()
    assert rs["id"] == 1
    assert rs["name"] == "Administrator"
    assert rs["description"] == "Full access to all system features and settings."

    assert len(rs["permissions"]) == 14
    assert rs["permissions"][0]["id"] == 1
    assert rs["permissions"][0]["name"] == "read_user"
    assert (
        rs["permissions"][0]["description"] == "Allows the user to read user accounts."
    )

    assert rs["permissions"][1]["id"] == 2
    assert rs["permissions"][1]["name"] == "create_user"
    assert (
        rs["permissions"][1]["description"]
        == "Allows the user to create new user accounts."
    )

    assert rs["permissions"][2]["id"] == 3
    assert rs["permissions"][2]["name"] == "update_user"
    assert (
        rs["permissions"][2]["description"]
        == "Allows the user to update user accounts."
    )

    assert rs["permissions"][3]["id"] == 4
    assert rs["permissions"][3]["name"] == "delete_user"
    assert (
        rs["permissions"][3]["description"]
        == "Allows the user to delete user accounts."
    )

    assert rs["permissions"][4]["id"] == 5
    assert rs["permissions"][4]["name"] == "read_role"
    assert rs["permissions"][4]["description"] == "Allows the user to read roles."

    assert rs["permissions"][5]["id"] == 6
    assert rs["permissions"][5]["name"] == "create_role"
    assert rs["permissions"][5]["description"] == "Allows the user to create new roles."

    assert rs["permissions"][6]["id"] == 7
    assert rs["permissions"][6]["name"] == "update_role"
    assert rs["permissions"][6]["description"] == "Allows the user to update roles."

    assert rs["permissions"][7]["id"] == 8
    assert rs["permissions"][7]["name"] == "delete_role"
    assert rs["permissions"][7]["description"] == "Allows the user to delete roles."

    assert rs["permissions"][8]["id"] == 9
    assert rs["permissions"][8]["name"] == "manage_user_role"
    assert (
        rs["permissions"][8]["description"] == "Allows the user to manage users' roles."
    )

    assert rs["permissions"][9]["id"] == 10
    assert rs["permissions"][9]["name"] == "read_permission"
    assert rs["permissions"][9]["description"] == "Allows the user to read permissions."

    assert rs["permissions"][10]["id"] == 11
    assert rs["permissions"][10]["name"] == "create_permission"
    assert (
        rs["permissions"][10]["description"]
        == "Allows the user to create new permissions."
    )

    assert rs["permissions"][11]["id"] == 12
    assert rs["permissions"][11]["name"] == "update_permission"
    assert (
        rs["permissions"][11]["description"] == "Allows the user to update permissions."
    )

    assert rs["permissions"][12]["id"] == 13
    assert rs["permissions"][12]["name"] == "delete_permission"
    assert (
        rs["permissions"][12]["description"] == "Allows the user to delete permissions."
    )

    assert rs["permissions"][13]["id"] == 14
    assert rs["permissions"][13]["name"] == "manage_role_permission"
    assert (
        rs["permissions"][13]["description"]
        == "Allows the user to manage roles' permissions."
    )

    assert rs["created_at"]
    assert rs["updated_at"]


def test_retrieve_a_role(admin_authenticated: TestClient) -> None:
    response = admin_authenticated.get("/roles/1")
    assert response.status_code == 200
    rs = response.json()

    assert rs["id"] == 1
    assert rs["name"] == "admin"
    assert rs["description"] == "Full access to all system features and settings."

    assert len(rs["permissions"]) == 14
    assert rs["permissions"][0]["id"] == 1
    assert rs["permissions"][0]["name"] == "read_user"
    assert (
        rs["permissions"][0]["description"] == "Allows the user to read user accounts."
    )

    assert rs["permissions"][1]["id"] == 2
    assert rs["permissions"][1]["name"] == "create_user"
    assert (
        rs["permissions"][1]["description"]
        == "Allows the user to create new user accounts."
    )

    assert rs["permissions"][2]["id"] == 3
    assert rs["permissions"][2]["name"] == "update_user"
    assert (
        rs["permissions"][2]["description"]
        == "Allows the user to update user accounts."
    )

    assert rs["permissions"][3]["id"] == 4
    assert rs["permissions"][3]["name"] == "delete_user"
    assert (
        rs["permissions"][3]["description"]
        == "Allows the user to delete user accounts."
    )

    assert rs["permissions"][4]["id"] == 5
    assert rs["permissions"][4]["name"] == "read_role"
    assert rs["permissions"][4]["description"] == "Allows the user to read roles."

    assert rs["permissions"][5]["id"] == 6
    assert rs["permissions"][5]["name"] == "create_role"
    assert rs["permissions"][5]["description"] == "Allows the user to create new roles."

    assert rs["permissions"][6]["id"] == 7
    assert rs["permissions"][6]["name"] == "update_role"
    assert rs["permissions"][6]["description"] == "Allows the user to update roles."

    assert rs["permissions"][7]["id"] == 8
    assert rs["permissions"][7]["name"] == "delete_role"
    assert rs["permissions"][7]["description"] == "Allows the user to delete roles."

    assert rs["permissions"][8]["id"] == 9
    assert rs["permissions"][8]["name"] == "manage_user_role"
    assert (
        rs["permissions"][8]["description"] == "Allows the user to manage users' roles."
    )

    assert rs["permissions"][9]["id"] == 10
    assert rs["permissions"][9]["name"] == "read_permission"
    assert rs["permissions"][9]["description"] == "Allows the user to read permissions."

    assert rs["permissions"][10]["id"] == 11
    assert rs["permissions"][10]["name"] == "create_permission"
    assert (
        rs["permissions"][10]["description"]
        == "Allows the user to create new permissions."
    )

    assert rs["permissions"][11]["id"] == 12
    assert rs["permissions"][11]["name"] == "update_permission"
    assert (
        rs["permissions"][11]["description"] == "Allows the user to update permissions."
    )

    assert rs["permissions"][12]["id"] == 13
    assert rs["permissions"][12]["name"] == "delete_permission"
    assert (
        rs["permissions"][12]["description"] == "Allows the user to delete permissions."
    )

    assert rs["permissions"][13]["id"] == 14
    assert rs["permissions"][13]["name"] == "manage_role_permission"
    assert (
        rs["permissions"][13]["description"]
        == "Allows the user to manage roles' permissions."
    )

    assert rs["created_at"]
    assert rs["updated_at"]


def test_delete_a_role(admin_authenticated: TestClient) -> None:
    response = admin_authenticated.delete("/roles/1")
    assert response.status_code == 204


def test_manage_permissions_of_a_role(admin_authenticated: TestClient) -> None:
    response = admin_authenticated.post(
        "/roles/1/permissions",
        json={
            "permission_ids": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14],
        },
    )
    assert response.status_code == 200
    rs = response.json()
    assert rs["id"] == 1
    assert rs["name"] == "admin"
    assert rs["description"] == "Full access to all system features and settings."

    assert len(rs["permissions"]) == 14
    assert rs["permissions"][0]["id"] == 1
    assert rs["permissions"][0]["name"] == "read_user"
    assert (
        rs["permissions"][0]["description"] == "Allows the user to read user accounts."
    )

    assert rs["permissions"][1]["id"] == 2
    assert rs["permissions"][1]["name"] == "create_user"
    assert (
        rs["permissions"][1]["description"]
        == "Allows the user to create new user accounts."
    )

    assert rs["permissions"][2]["id"] == 3
    assert rs["permissions"][2]["name"] == "update_user"
    assert (
        rs["permissions"][2]["description"]
        == "Allows the user to update user accounts."
    )

    assert rs["permissions"][3]["id"] == 4
    assert rs["permissions"][3]["name"] == "delete_user"
    assert (
        rs["permissions"][3]["description"]
        == "Allows the user to delete user accounts."
    )

    assert rs["permissions"][4]["id"] == 5
    assert rs["permissions"][4]["name"] == "read_role"
    assert rs["permissions"][4]["description"] == "Allows the user to read roles."

    assert rs["permissions"][5]["id"] == 6
    assert rs["permissions"][5]["name"] == "create_role"
    assert rs["permissions"][5]["description"] == "Allows the user to create new roles."

    assert rs["permissions"][6]["id"] == 7
    assert rs["permissions"][6]["name"] == "update_role"
    assert rs["permissions"][6]["description"] == "Allows the user to update roles."

    assert rs["permissions"][7]["id"] == 8
    assert rs["permissions"][7]["name"] == "delete_role"
    assert rs["permissions"][7]["description"] == "Allows the user to delete roles."

    assert rs["permissions"][8]["id"] == 9
    assert rs["permissions"][8]["name"] == "manage_user_role"
    assert (
        rs["permissions"][8]["description"] == "Allows the user to manage users' roles."
    )

    assert rs["permissions"][9]["id"] == 10
    assert rs["permissions"][9]["name"] == "read_permission"
    assert rs["permissions"][9]["description"] == "Allows the user to read permissions."

    assert rs["permissions"][10]["id"] == 11
    assert rs["permissions"][10]["name"] == "create_permission"
    assert (
        rs["permissions"][10]["description"]
        == "Allows the user to create new permissions."
    )

    assert rs["permissions"][11]["id"] == 12
    assert rs["permissions"][11]["name"] == "update_permission"
    assert (
        rs["permissions"][11]["description"] == "Allows the user to update permissions."
    )

    assert rs["permissions"][12]["id"] == 13
    assert rs["permissions"][12]["name"] == "delete_permission"
    assert (
        rs["permissions"][12]["description"] == "Allows the user to delete permissions."
    )

    assert rs["permissions"][13]["id"] == 14
    assert rs["permissions"][13]["name"] == "manage_role_permission"
    assert (
        rs["permissions"][13]["description"]
        == "Allows the user to manage roles' permissions."
    )

    assert rs["created_at"]
    assert rs["updated_at"]

    response = admin_authenticated.post(
        "/roles/1/permissions",
        json={
            "permission_ids": [1],
        },
    )
    assert response.status_code == 200
    rs = response.json()
    assert rs["id"] == 1
    assert rs["name"] == "admin"
    assert rs["description"] == "Full access to all system features and settings."

    assert len(rs["permissions"]) == 1
    assert rs["permissions"][0]["id"] == 1
    assert rs["permissions"][0]["name"] == "read_user"
    assert (
        rs["permissions"][0]["description"] == "Allows the user to read user accounts."
    )

    assert rs["created_at"]
    assert rs["updated_at"]


def test_cannot_create_a_role_with_already_existing_name(
    admin_authenticated: TestClient,
) -> None:
    response = admin_authenticated.post(
        "/roles",
        json={
            "name": "admin",
            "description": "description of test role",
        },
    )
    assert response.status_code == 409
    rs = response.json()
    assert rs["msg"] == "Role already exists. [name=admin]"


def test_cannot_get_roles_while_unauthorized(
    standard_authenticated: TestClient,
) -> None:
    response = standard_authenticated.get("/roles")
    assert response.status_code == 403
    rs = response.json()
    assert rs["msg"] == "You are not authorized to perform this action"


def test_cannot_update_a_role_while_unauthorized(
    standard_authenticated: TestClient,
) -> None:
    response = standard_authenticated.put(
        "/roles/1",
        json={
            "name": "Administrator",
            "description": "Full access to all system features and settings.",
        },
    )
    assert response.status_code == 403
    rs = response.json()
    assert rs["msg"] == "You are not authorized to perform this action"


def test_cannot_retrieve_a_role_while_unauthorized(
    standard_authenticated: TestClient,
) -> None:
    response = standard_authenticated.get("/roles/1")
    assert response.status_code == 403
    rs = response.json()
    assert rs["msg"] == "You are not authorized to perform this action"


def test_cannot_delete_a_role_while_unauthorized(
    standard_authenticated: TestClient,
) -> None:
    response = standard_authenticated.delete("/roles/1")
    assert response.status_code == 403
    rs = response.json()
    assert rs["msg"] == "You are not authorized to perform this action"


def test_cannot_manage_a_role_while_unauthorized(
    standard_authenticated: TestClient,
) -> None:
    response = standard_authenticated.post(
        "/roles/1/permissions",
        json={
            "permission_ids": [1],
        },
    )
    assert response.status_code == 403
    rs = response.json()
    assert rs["msg"] == "You are not authorized to perform this action"
