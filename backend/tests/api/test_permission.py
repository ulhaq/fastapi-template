import json
from fastapi.testclient import TestClient
import pytest

from tests.utils import (
    assert_filtering_of_items_list,
    assert_pagination,
    assert_sorting_of_items_list,
)


def test_get_all_permissions(admin_authenticated: TestClient) -> None:
    response = admin_authenticated.get("/v1/permissions?page_size=100")
    assert response.status_code == 200
    rs = response.json()

    assert rs["page_number"] == 1
    assert rs["page_size"] == 100
    assert rs["total"] == 15

    assert len(rs["items"]) == 15
    assert rs["items"][0]["id"] == 1
    assert rs["items"][0]["name"] == "update:organization"
    assert (
        rs["items"][0]["description"]
        == "Allows the user to update organization accounts."
    )
    assert rs["items"][0]["created_at"]
    assert rs["items"][0]["updated_at"]


@pytest.mark.parametrize(
    "page_number, page_size, page_total, total",
    [
        pytest.param(1, 10, 10, 15),
        pytest.param(2, 10, 5, 15),
        pytest.param(3, 10, 0, 15),
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
        f"/v1/permissions?page_number={page_number}&page_size{page_size}"
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
    response = admin_authenticated.get(f"/v1/permissions?sort={sort}")
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
        pytest.param(["name"], [["create:user"]], ["eq"], 1),
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

    response = admin_authenticated.get(f"/v1/permissions?filters={json.dumps(filters)}")
    assert response.status_code == 200
    rs = response.json()

    assert len(rs["items"]) == total_page

    assert_filtering_of_items_list(rs["items"], filter_data)


def test_retrieve_a_permission(admin_authenticated: TestClient) -> None:
    response = admin_authenticated.get("/v1/permissions/1")
    assert response.status_code == 200
    rs = response.json()

    assert rs["id"] == 1
    assert rs["name"] == "update:organization"
    assert rs["description"] == "Allows the user to update organization accounts."
    assert rs["created_at"]
    assert rs["updated_at"]


def test_cannot_get_non_existent_permission(admin_authenticated: TestClient) -> None:
    response = admin_authenticated.get("/v1/permissions/0")
    assert response.status_code == 404
    rs = response.json()
    assert rs["msg"] == "Permission not found. [identifier=0]"


def test_cannot_get_permissions_while_unauthorized(
    standard_authenticated: TestClient,
) -> None:
    response = standard_authenticated.get("/v1/permissions")
    assert response.status_code == 403
    rs = response.json()
    assert rs["msg"] == "You are not authorized to perform this action"


def test_cannot_retrieve_a_permission_while_unauthorized(
    standard_authenticated: TestClient,
) -> None:
    response = standard_authenticated.get("/v1/permissions/1")
    assert response.status_code == 403
    rs = response.json()
    assert rs["msg"] == "You are not authorized to perform this action"
