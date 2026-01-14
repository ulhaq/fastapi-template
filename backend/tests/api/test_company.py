import json
from fastapi.testclient import TestClient
import pytest

from tests.utils import (
    assert_filtering_of_items_list,
    assert_pagination,
    assert_sorting_of_items_list,
)


def test_get_all_companies(admin_authenticated: TestClient) -> None:
    response = admin_authenticated.get("/companies")
    assert response.status_code == 200
    rs = response.json()
    assert rs["page_number"] == 1
    assert rs["page_size"] == 10
    assert rs["total"] == 2

    assert len(rs["items"]) == 2
    assert rs["items"][0]["id"] == 1
    assert rs["items"][0]["name"] == "Company 1"
    assert rs["items"][0]["created_at"]
    assert rs["items"][0]["updated_at"]

    assert rs["items"][1]["id"] == 2
    assert rs["items"][1]["name"] == "Company 2"
    assert rs["items"][1]["created_at"]
    assert rs["items"][1]["updated_at"]


@pytest.mark.parametrize(
    "page_number, page_size, page_total, total",
    [
        pytest.param(1, 10, 2, 2),
        pytest.param(2, 10, 0, 2),
    ],
)
def test_paginate_companies(
    page_number: int,
    page_size: int,
    page_total: int,
    total: int,
    admin_authenticated: TestClient,
) -> None:
    response = admin_authenticated.get(
        f"/companies?page_number={page_number}&page_size{page_size}"
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
        pytest.param("created_at"),
        pytest.param("-created_at"),
        pytest.param("updated_at"),
        pytest.param("-updated_at"),
    ],
)
def test_sort_companies(sort: str, admin_authenticated: TestClient) -> None:
    response = admin_authenticated.get(f"/companies?sort={sort}")
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
        pytest.param(["name"], [["Company 1"]], ["eq"], 1),
        pytest.param(["name"], [["a", "d"]], ["co"], 2),
        pytest.param(
            ["created_at"],
            [["2025-04-22T14:04:38.586226", "2050-09-22T14:04:38.586226"]],
            ["between"],
            2,
        ),
    ],
)
def test_filter_companies(
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

    response = admin_authenticated.get(f"/companies?filters={json.dumps(filters)}")
    assert response.status_code == 200
    rs = response.json()

    assert len(rs["items"]) == total_page

    assert_filtering_of_items_list(rs["items"], filter_data)


def test_create_a_company(admin_authenticated: TestClient) -> None:
    response = admin_authenticated.post(
        "/companies",
        json={
            "name": "test company",
        },
    )
    assert response.status_code == 201
    rs = response.json()
    assert rs["id"] == 3
    assert rs["name"] == "test company"

    assert rs["created_at"]
    assert rs["updated_at"]


def test_update_a_company(admin_authenticated: TestClient) -> None:
    response = admin_authenticated.put(
        "/companies/1",
        json={
            "name": "Updated Company",
        },
    )
    assert response.status_code == 200
    rs = response.json()
    assert rs["id"] == 1
    assert rs["name"] == "Updated Company"
    assert rs["created_at"]
    assert rs["updated_at"]


def test_retrieve_a_company(admin_authenticated: TestClient) -> None:
    response = admin_authenticated.get("/companies/1")
    assert response.status_code == 200
    rs = response.json()

    assert rs["id"] == 1
    assert rs["name"] == "Company 1"
    assert rs["created_at"]
    assert rs["updated_at"]


def test_delete_a_company(admin_authenticated: TestClient) -> None:
    response = admin_authenticated.delete("/companies/1")
    assert response.status_code == 204

    response = admin_authenticated.get("/companies/1")
    assert response.status_code == 404


def test_cannot_create_a_company_with_already_existing_name(
    admin_authenticated: TestClient,
) -> None:
    response = admin_authenticated.post(
        "/companies",
        json={
            "name": "Company 1",
        },
    )
    assert response.status_code == 409
    rs = response.json()
    assert rs["msg"] == "Company already exists. [name=Company 1]"


def test_cannot_get_companies_while_unauthorized(
    standard_authenticated: TestClient,
) -> None:
    response = standard_authenticated.get("/companies")
    assert response.status_code == 403
    rs = response.json()
    assert rs["msg"] == "You are not authorized to perform this action"


def test_cannot_update_a_company_while_unauthorized(
    standard_authenticated: TestClient,
) -> None:
    response = standard_authenticated.put(
        "/companies/1",
        json={
            "name": "Administrator",
            "description": "Full access to all system features and settings.",
        },
    )
    assert response.status_code == 403
    rs = response.json()
    assert rs["msg"] == "You are not authorized to perform this action"


def test_cannot_retrieve_a_company_while_unauthorized(
    standard_authenticated: TestClient,
) -> None:
    response = standard_authenticated.get("/companies/1")
    assert response.status_code == 403
    rs = response.json()
    assert rs["msg"] == "You are not authorized to perform this action"


def test_cannot_delete_a_company_while_unauthorized(
    standard_authenticated: TestClient,
) -> None:
    response = standard_authenticated.delete("/companies/1")
    assert response.status_code == 403
    rs = response.json()
    assert rs["msg"] == "You are not authorized to perform this action"
