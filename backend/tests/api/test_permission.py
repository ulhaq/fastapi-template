import json
from fastapi.testclient import TestClient
import pytest

from tests.utils import (
    assert_filtering_of_items_list,
    assert_pagination,
    assert_sorting_of_items_list,
)


def test_get_all_permissions(admin_authenticated: TestClient) -> None:
    response = admin_authenticated.get("/permissions?page_size=20")
    assert response.status_code == 200
    rs = response.json()

    assert rs["page_number"] == 1
    assert rs["page_size"] == 20
    assert rs["total"] == 19

    assert len(rs["items"]) == 19
    assert rs["items"][0]["id"] == 1
    assert rs["items"][0]["name"] == "read_company"
    assert rs["items"][0]["description"] == "Allows the user to read company accounts."
    assert len(rs["items"][0]["roles"]) == 1
    assert rs["items"][0]["roles"][0]["id"] == 1
    assert rs["items"][0]["roles"][0]["name"] == "admin"
    assert (
        rs["items"][0]["roles"][0]["description"]
        == "Full access to all system features and settings."
    )
    assert rs["items"][0]["created_at"]
    assert rs["items"][0]["updated_at"]

    assert rs["items"][1]["id"] == 2
    assert rs["items"][1]["name"] == "create_company"
    assert (
        rs["items"][1]["description"]
        == "Allows the user to create new company accounts."
    )
    assert len(rs["items"][1]["roles"]) == 1
    assert rs["items"][1]["roles"][0]["id"] == 1
    assert rs["items"][1]["roles"][0]["name"] == "admin"
    assert (
        rs["items"][1]["roles"][0]["description"]
        == "Full access to all system features and settings."
    )
    assert rs["items"][1]["created_at"]
    assert rs["items"][1]["updated_at"]

    assert rs["items"][2]["id"] == 3
    assert rs["items"][2]["name"] == "update_company"
    assert (
        rs["items"][2]["description"] == "Allows the user to update company accounts."
    )
    assert len(rs["items"][2]["roles"]) == 1
    assert rs["items"][2]["roles"][0]["id"] == 1
    assert rs["items"][2]["roles"][0]["name"] == "admin"
    assert (
        rs["items"][2]["roles"][0]["description"]
        == "Full access to all system features and settings."
    )
    assert rs["items"][2]["created_at"]
    assert rs["items"][2]["updated_at"]

    assert rs["items"][3]["id"] == 4
    assert rs["items"][3]["name"] == "delete_company"
    assert (
        rs["items"][3]["description"] == "Allows the user to delete company accounts."
    )
    assert len(rs["items"][3]["roles"]) == 1
    assert rs["items"][3]["roles"][0]["id"] == 1
    assert rs["items"][3]["roles"][0]["name"] == "admin"
    assert (
        rs["items"][3]["roles"][0]["description"]
        == "Full access to all system features and settings."
    )
    assert rs["items"][3]["created_at"]
    assert rs["items"][3]["updated_at"]

    assert rs["items"][4]["id"] == 5
    assert rs["items"][4]["name"] == "manage_company_user"
    assert (
        rs["items"][4]["description"] == "Allows the user to manage companies' users."
    )
    assert len(rs["items"][4]["roles"]) == 1
    assert rs["items"][4]["roles"][0]["id"] == 1
    assert rs["items"][4]["roles"][0]["name"] == "admin"
    assert (
        rs["items"][4]["roles"][0]["description"]
        == "Full access to all system features and settings."
    )
    assert rs["items"][4]["created_at"]
    assert rs["items"][4]["updated_at"]

    assert rs["items"][5]["id"] == 6
    assert rs["items"][5]["name"] == "read_user"
    assert (
        rs["items"][5]["description"] == "Allows the user to read users."
    )
    assert len(rs["items"][5]["roles"]) == 2
    assert rs["items"][5]["roles"][0]["id"] == 1
    assert rs["items"][5]["roles"][0]["name"] == "admin"
    assert (
        rs["items"][5]["roles"][0]["description"]
        == "Full access to all system features and settings."
    )
    assert rs["items"][5]["roles"][1]["id"] == 2
    assert rs["items"][5]["roles"][1]["name"] == "standard"
    assert (
        rs["items"][5]["roles"][1]["description"]
        == "Access to manage and view own resources."
    )
    assert rs["items"][5]["created_at"]
    assert rs["items"][5]["updated_at"]

    assert rs["items"][6]["id"] == 7
    assert rs["items"][6]["name"] == "create_user"
    assert (
        rs["items"][6]["description"] == "Allows the user to create new users."
    )
    assert len(rs["items"][6]["roles"]) == 2
    assert rs["items"][6]["roles"][0]["id"] == 1
    assert rs["items"][6]["roles"][0]["name"] == "admin"
    assert (
        rs["items"][6]["roles"][0]["description"]
        == "Full access to all system features and settings."
    )
    assert rs["items"][6]["roles"][1]["id"] == 2
    assert rs["items"][6]["roles"][1]["name"] == "standard"
    assert (
        rs["items"][6]["roles"][1]["description"]
        == "Access to manage and view own resources."
    )
    assert rs["items"][6]["created_at"]
    assert rs["items"][6]["updated_at"]

    assert rs["items"][7]["id"] == 8
    assert rs["items"][7]["name"] == "update_user"
    assert rs["items"][7]["description"] == "Allows the user to update users."

    assert len(rs["items"][7]["roles"]) == 1
    assert rs["items"][7]["roles"][0]["id"] == 1
    assert rs["items"][7]["roles"][0]["name"] == "admin"
    assert (
        rs["items"][7]["roles"][0]["description"]
        == "Full access to all system features and settings."
    )
    assert rs["items"][7]["created_at"]
    assert rs["items"][7]["updated_at"]

    assert rs["items"][8]["id"] == 9
    assert rs["items"][8]["name"] == "delete_user"
    assert rs["items"][8]["description"] == "Allows the user to delete users."

    assert len(rs["items"][8]["roles"]) == 1
    assert rs["items"][8]["roles"][0]["id"] == 1
    assert rs["items"][8]["roles"][0]["name"] == "admin"
    assert (
        rs["items"][8]["roles"][0]["description"]
        == "Full access to all system features and settings."
    )
    assert rs["items"][8]["created_at"]
    assert rs["items"][8]["updated_at"]

    assert rs["items"][9]["id"] == 10
    assert rs["items"][9]["name"] == "read_role"
    assert rs["items"][9]["description"] == "Allows the user to read roles."
    assert len(rs["items"][9]["roles"]) == 1
    assert rs["items"][9]["roles"][0]["id"] == 1
    assert rs["items"][9]["roles"][0]["name"] == "admin"
    assert (
        rs["items"][9]["roles"][0]["description"]
        == "Full access to all system features and settings."
    )
    assert rs["items"][9]["created_at"]
    assert rs["items"][9]["updated_at"]

    assert rs["items"][10]["id"] == 11
    assert rs["items"][10]["name"] == "create_role"
    assert rs["items"][10]["description"] == "Allows the user to create new roles."
    assert len(rs["items"][10]["roles"]) == 1
    assert rs["items"][10]["roles"][0]["id"] == 1
    assert rs["items"][10]["roles"][0]["name"] == "admin"
    assert (
        rs["items"][10]["roles"][0]["description"]
        == "Full access to all system features and settings."
    )
    assert rs["items"][10]["created_at"]
    assert rs["items"][10]["updated_at"]

    assert rs["items"][11]["id"] == 12
    assert rs["items"][11]["name"] == "update_role"
    assert rs["items"][11]["description"] == "Allows the user to update roles."
    assert len(rs["items"][11]["roles"]) == 1
    assert rs["items"][11]["roles"][0]["id"] == 1
    assert rs["items"][11]["roles"][0]["name"] == "admin"
    assert (
        rs["items"][11]["roles"][0]["description"]
        == "Full access to all system features and settings."
    )
    assert rs["items"][11]["created_at"]
    assert rs["items"][11]["updated_at"]

    assert rs["items"][12]["id"] == 13
    assert rs["items"][12]["name"] == "delete_role"
    assert rs["items"][12]["description"] == "Allows the user to delete roles."
    assert len(rs["items"][12]["roles"]) == 1
    assert rs["items"][12]["roles"][0]["id"] == 1
    assert rs["items"][12]["roles"][0]["name"] == "admin"
    assert (
        rs["items"][12]["roles"][0]["description"]
        == "Full access to all system features and settings."
    )
    assert rs["items"][12]["created_at"]
    assert rs["items"][12]["updated_at"]

    assert rs["items"][13]["id"] == 14
    assert rs["items"][13]["name"] == "manage_user_role"
    assert rs["items"][13]["description"] == "Allows the user to manage users' roles."
    assert len(rs["items"][13]["roles"]) == 1
    assert rs["items"][13]["roles"][0]["id"] == 1
    assert rs["items"][13]["roles"][0]["name"] == "admin"
    assert (
        rs["items"][13]["roles"][0]["description"]
        == "Full access to all system features and settings."
    )
    assert rs["items"][13]["created_at"]
    assert rs["items"][13]["updated_at"]

    assert rs["items"][14]["id"] == 15
    assert rs["items"][14]["name"] == "read_permission"
    assert rs["items"][14]["description"] == "Allows the user to read permissions."
    assert len(rs["items"][14]["roles"]) == 1
    assert rs["items"][14]["roles"][0]["id"] == 1
    assert rs["items"][14]["roles"][0]["name"] == "admin"
    assert (
        rs["items"][14]["roles"][0]["description"]
        == "Full access to all system features and settings."
    )
    assert rs["items"][14]["created_at"]
    assert rs["items"][14]["updated_at"]

    assert rs["items"][15]["id"] == 16
    assert rs["items"][15]["name"] == "create_permission"
    assert (
        rs["items"][15]["description"] == "Allows the user to create new permissions."
    )
    assert len(rs["items"][15]["roles"]) == 1
    assert rs["items"][15]["roles"][0]["id"] == 1
    assert rs["items"][15]["roles"][0]["name"] == "admin"
    assert (
        rs["items"][15]["roles"][0]["description"]
        == "Full access to all system features and settings."
    )
    assert rs["items"][15]["created_at"]
    assert rs["items"][15]["updated_at"]

    assert rs["items"][16]["id"] == 17
    assert rs["items"][16]["name"] == "update_permission"
    assert rs["items"][16]["description"] == "Allows the user to update permissions."
    assert len(rs["items"][16]["roles"]) == 1
    assert rs["items"][16]["roles"][0]["id"] == 1
    assert rs["items"][16]["roles"][0]["name"] == "admin"
    assert (
        rs["items"][16]["roles"][0]["description"]
        == "Full access to all system features and settings."
    )
    assert rs["items"][16]["created_at"]
    assert rs["items"][16]["updated_at"]

    assert rs["items"][17]["id"] == 18
    assert rs["items"][17]["name"] == "delete_permission"
    assert rs["items"][17]["description"] == "Allows the user to delete permissions."
    assert len(rs["items"][17]["roles"]) == 1
    assert rs["items"][17]["roles"][0]["id"] == 1
    assert rs["items"][17]["roles"][0]["name"] == "admin"
    assert (
        rs["items"][17]["roles"][0]["description"]
        == "Full access to all system features and settings."
    )
    assert rs["items"][17]["created_at"]
    assert rs["items"][17]["updated_at"]

    assert rs["items"][18]["id"] == 19
    assert rs["items"][18]["name"] == "manage_role_permission"
    assert (
        rs["items"][18]["description"]
        == "Allows the user to manage roles' permissions."
    )
    assert len(rs["items"][18]["roles"]) == 1
    assert rs["items"][18]["roles"][0]["id"] == 1
    assert rs["items"][18]["roles"][0]["name"] == "admin"
    assert (
        rs["items"][18]["roles"][0]["description"]
        == "Full access to all system features and settings."
    )
    assert rs["items"][18]["created_at"]
    assert rs["items"][18]["updated_at"]


@pytest.mark.parametrize(
    "page_number, page_size, page_total, total",
    [
        pytest.param(1, 10, 10, 19),
        pytest.param(2, 10, 9, 19),
        pytest.param(3, 10, 0, 19),
    ],
)
def test_paginate_permissions(
    page_number: int,
    page_size: int,
    page_total: int,
    total: int,
    admin_authenticated: TestClient,
) -> None:
    response = admin_authenticated.get(
        f"/permissions?page_number={page_number}&page_size{page_size}"
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
def test_sort_permissions(sort: str, admin_authenticated: TestClient) -> None:
    response = admin_authenticated.get(f"/permissions?sort={sort}")
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
        pytest.param(["id", "name"], [[1], ["a"]], ["eq", "co"], 10),
        pytest.param(["name"], [["create_user"]], ["eq"], 1),
        pytest.param(["name"], [["re", "ate"]], ["co"], 10),
        pytest.param(["description"], [["allows"]], ["ico"], 10),
        pytest.param(
            ["created_at"],
            [["2025-04-22T14:04:38.586226", "2050-09-22T14:04:38.586226"]],
            ["between"],
            10,
        ),
    ],
)
def test_filter_permissions(
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

    response = admin_authenticated.get(f"/permissions?filters={json.dumps(filters)}")
    assert response.status_code == 200
    rs = response.json()

    assert len(rs["items"]) == total_page

    assert_filtering_of_items_list(rs["items"], filter_data)


def test_create_a_permission(admin_authenticated: TestClient) -> None:
    response = admin_authenticated.post(
        "/permissions",
        json={
            "name": "test permission",
            "description": "description of test permission",
        },
    )
    assert response.status_code == 201
    rs = response.json()
    assert rs["id"] == 20
    assert rs["name"] == "test permission"
    assert rs["description"] == "description of test permission"

    assert rs["roles"] == []

    assert rs["created_at"]
    assert rs["updated_at"]


def test_update_a_permission(admin_authenticated: TestClient) -> None:
    response = admin_authenticated.put(
        "/permissions/1",
        json={
            "name": "Company Read Permission",
            "description": "Allows the user to read any company.",
        },
    )
    assert response.status_code == 200
    rs = response.json()
    assert rs["id"] == 1
    assert rs["name"] == "Company Read Permission"
    assert rs["description"] == "Allows the user to read any company."

    assert len(rs["roles"]) == 1
    assert rs["roles"][0]["id"] == 1
    assert rs["roles"][0]["name"] == "admin"
    assert (
        rs["roles"][0]["description"]
        == "Full access to all system features and settings."
    )

    assert rs["created_at"]
    assert rs["updated_at"]


def test_retrieve_a_permission(admin_authenticated: TestClient) -> None:
    response = admin_authenticated.get("/permissions/1")
    assert response.status_code == 200
    rs = response.json()

    assert rs["id"] == 1
    assert rs["name"] == "read_company"
    assert rs["description"] == "Allows the user to read company accounts."

    assert len(rs["roles"]) == 1
    assert rs["roles"][0]["id"] == 1
    assert rs["roles"][0]["name"] == "admin"
    assert (
        rs["roles"][0]["description"]
        == "Full access to all system features and settings."
    )

    assert rs["created_at"]
    assert rs["updated_at"]


def test_delete_a_permission(admin_authenticated: TestClient) -> None:
    response = admin_authenticated.delete("/permissions/1")
    assert response.status_code == 204

    response = admin_authenticated.get("/permissions/1")
    assert response.status_code == 404


def test_cannot_get_non_existent_permission(admin_authenticated: TestClient) -> None:
    response = admin_authenticated.get("/permissions/0")
    assert response.status_code == 404
    rs = response.json()
    assert rs["msg"] == "Permission not found. [identifier=0]"


def test_cannot_create_a_permission_with_already_existing_name(
    admin_authenticated: TestClient,
) -> None:
    response = admin_authenticated.post(
        "/permissions",
        json={
            "name": "create_user",
            "description": "description of test permission",
        },
    )
    assert response.status_code == 409
    rs = response.json()
    assert rs["msg"] == "Permission already exists. [name=create_user]"


def test_cannot_get_permissions_while_unauthorized(
    standard_authenticated: TestClient,
) -> None:
    response = standard_authenticated.get("/permissions")
    assert response.status_code == 403
    rs = response.json()
    assert rs["msg"] == "You are not authorized to perform this action"


def test_cannot_update_a_permission_while_unauthorized(
    standard_authenticated: TestClient,
) -> None:
    response = standard_authenticated.put(
        "/permissions/1",
        json={
            "name": "Administrator",
            "description": "Full access to all system features and settings.",
        },
    )
    assert response.status_code == 403
    rs = response.json()
    assert rs["msg"] == "You are not authorized to perform this action"


def test_cannot_retrieve_a_permission_while_unauthorized(
    standard_authenticated: TestClient,
) -> None:
    response = standard_authenticated.get("/permissions/1")
    assert response.status_code == 403
    rs = response.json()
    assert rs["msg"] == "You are not authorized to perform this action"


def test_cannot_delete_a_permission_while_unauthorized(
    standard_authenticated: TestClient,
) -> None:
    response = standard_authenticated.delete("/permissions/1")
    assert response.status_code == 403
    rs = response.json()
    assert rs["msg"] == "You are not authorized to perform this action"
