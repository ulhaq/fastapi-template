import json
from fastapi.testclient import TestClient
import pytest

from tests.utils import (
    assert_filtering_of_items_list,
    assert_pagination,
    assert_sorting_of_items_list,
)


def test_get_all_tenants(admin_authenticated: TestClient) -> None:
    response = admin_authenticated.get("/v1/tenants")
    assert response.status_code == 200
    rs = response.json()
    assert rs["page_number"] == 1
    assert rs["page_size"] == 10
    assert rs["total"] == 1

    assert len(rs["items"]) == 1
    assert rs["items"][0]["id"] == 1
    assert rs["items"][0]["name"] == "Tenant 1"
    assert rs["items"][0]["created_at"]
    assert rs["items"][0]["updated_at"]


@pytest.mark.parametrize(
    "page_number, page_size, page_total, total",
    [
        pytest.param(1, 10, 1, 1),
        pytest.param(2, 10, 0, 1),
    ],
)
def test_paginate_tenants(
    page_number: int,
    page_size: int,
    page_total: int,
    total: int,
    admin_authenticated: TestClient,
) -> None:
    response = admin_authenticated.get(
        f"/v1/tenants?page_number={page_number}&page_size{page_size}"
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
def test_sort_tenants(sort: str, admin_authenticated: TestClient) -> None:
    response = admin_authenticated.get(f"/v1/tenants?sort={sort}")
    assert response.status_code == 200
    rs = response.json()

    assert_sorting_of_items_list(rs["items"], sort.split(","))


@pytest.mark.parametrize(
    "fields,values,operators,total_page",
    [
        pytest.param(["id"], [[1]], ["eq"], 1),
        pytest.param(["id"], [[0, 1]], ["between"], 1),
        pytest.param(["id"], [[1, 2]], ["between"], 1),
        pytest.param(["name"], [["Tenant 1"]], ["eq"], 1),
        pytest.param(["name"], [["a", "d"]], ["co"], 1),
        pytest.param(
            ["created_at"],
            [["2025-04-22T14:04:38.586226", "2050-09-22T14:04:38.586226"]],
            ["between"],
            1,
        ),
    ],
)
def test_filter_tenants(
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

    response = admin_authenticated.get(f"/v1/tenants?filters={json.dumps(filters)}")
    assert response.status_code == 200
    rs = response.json()

    assert len(rs["items"]) == total_page

    assert_filtering_of_items_list(rs["items"], filter_data)


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


def test_update_a_tenant(admin_authenticated: TestClient) -> None:
    response = admin_authenticated.put(
        "/v1/tenants/1",
        json={
            "name": "Updated Tenant",
        },
    )
    assert response.status_code == 200
    rs = response.json()
    assert rs["id"] == 1
    assert rs["name"] == "Updated Tenant"
    assert rs["created_at"]
    assert rs["updated_at"]


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

    response = admin_authenticated.put(
        "/v1/tenants/2", json={"name": "Hacked"}
    )
    assert response.status_code == 403

    response = admin_authenticated.patch(
        "/v1/tenants/2", json={"name": "Hacked"}
    )
    assert response.status_code == 403

    response = admin_authenticated.delete("/v1/tenants/2")
    assert response.status_code == 403


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


def test_cannot_get_tenants_while_unauthorized(
    standard_authenticated: TestClient,
) -> None:
    response = standard_authenticated.get("/v1/tenants")
    assert response.status_code == 403
    rs = response.json()
    assert rs["msg"] == "You are not authorized to perform this action"


def test_cannot_update_a_tenant_while_unauthorized(
    standard_authenticated: TestClient,
) -> None:
    response = standard_authenticated.put(
        "/v1/tenants/1",
        json={
            "name": "Administrator",
            "description": "Full access to all system features and settings.",
        },
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
