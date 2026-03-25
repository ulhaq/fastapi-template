from fastapi.testclient import TestClient


# --- Company isolation ---


def test_cannot_get_other_company(company2_admin_authenticated: TestClient) -> None:
    response = company2_admin_authenticated.get("/v1/companies/1")
    assert response.status_code == 403


def test_cannot_update_other_company(company2_admin_authenticated: TestClient) -> None:
    response = company2_admin_authenticated.put(
        "/v1/companies/1", json={"name": "Hacked"}
    )
    assert response.status_code == 403


def test_cannot_patch_other_company(company2_admin_authenticated: TestClient) -> None:
    response = company2_admin_authenticated.patch(
        "/v1/companies/1", json={"name": "Hacked"}
    )
    assert response.status_code == 403


def test_cannot_delete_other_company(company2_admin_authenticated: TestClient) -> None:
    response = company2_admin_authenticated.delete("/v1/companies/1")
    assert response.status_code == 403


def test_companies_list_only_shows_own_company(
    company2_admin_authenticated: TestClient,
) -> None:
    response = company2_admin_authenticated.get("/v1/companies")
    assert response.status_code == 200
    rs = response.json()
    assert rs["total"] == 1
    assert rs["items"][0]["name"] == "Company 2"


# --- User isolation ---


def test_cannot_delete_other_company_user(
    company2_admin_authenticated: TestClient,
) -> None:
    response = company2_admin_authenticated.delete("/v1/users/1")
    assert response.status_code == 404


def test_cannot_manage_roles_of_other_company_user(
    company2_admin_authenticated: TestClient,
) -> None:
    response = company2_admin_authenticated.post(
        "/v1/users/1/roles", json={"role_ids": [3]}
    )
    assert response.status_code == 404


def test_cannot_transfer_other_company_user(
    company2_admin_authenticated: TestClient,
) -> None:
    response = company2_admin_authenticated.post(
        "/v1/users/1/transfer", json={"company_id": 2}
    )
    assert response.status_code == 404


# --- Role isolation ---


def test_cannot_get_other_company_role(
    company2_admin_authenticated: TestClient,
) -> None:
    response = company2_admin_authenticated.get("/v1/roles/1")
    assert response.status_code == 404


def test_cannot_update_other_company_role(
    company2_admin_authenticated: TestClient,
) -> None:
    response = company2_admin_authenticated.put(
        "/v1/roles/1", json={"name": "hacked", "description": "hacked"}
    )
    assert response.status_code == 404


def test_cannot_patch_other_company_role(
    company2_admin_authenticated: TestClient,
) -> None:
    response = company2_admin_authenticated.patch(
        "/v1/roles/1", json={"name": "hacked"}
    )
    assert response.status_code == 404


def test_cannot_delete_other_company_role(
    company2_admin_authenticated: TestClient,
) -> None:
    response = company2_admin_authenticated.delete("/v1/roles/1")
    assert response.status_code == 404


def test_roles_list_only_shows_own_company_roles(
    company2_admin_authenticated: TestClient,
) -> None:
    response = company2_admin_authenticated.get("/v1/roles?page_size=50")
    assert response.status_code == 200
    rs = response.json()
    for role in rs["items"]:
        assert role["company_id"] == 2


def test_new_role_not_visible_to_other_company(
    admin_authenticated: TestClient, company2_admin_authenticated: TestClient
) -> None:
    response = admin_authenticated.post(
        "/v1/roles", json={"name": "secret_role", "description": "Company 1 only"}
    )
    assert response.status_code == 201

    response = company2_admin_authenticated.get("/v1/roles?page_size=50")
    assert response.status_code == 200
    rs = response.json()
    role_names = [r["name"] for r in rs["items"]]
    assert "secret_role" not in role_names


# --- Cross-company role assignment ---


def test_cannot_assign_other_company_role_to_own_user(
    admin_authenticated: TestClient,
) -> None:
    # Role 3 belongs to Company 2; user 2 belongs to Company 1
    response = admin_authenticated.post(
        "/v1/users/2/roles", json={"role_ids": [3]}
    )
    assert response.status_code == 403


# --- User transfer ---


def test_transfer_user_strips_roles(admin_authenticated: TestClient) -> None:
    # User 2 (standard) has role 2 in Company 1
    response = admin_authenticated.post(
        "/v1/users/2/transfer", json={"company_id": 2}
    )
    assert response.status_code == 200
    rs = response.json()
    assert rs["roles"] == []


def test_cannot_transfer_self(admin_authenticated: TestClient) -> None:
    response = admin_authenticated.post(
        "/v1/users/1/transfer", json={"company_id": 2}
    )
    assert response.status_code == 403
    rs = response.json()
    assert rs["msg"] == "You are not allowed to transfer yourself"


def test_cannot_transfer_to_nonexistent_company(
    admin_authenticated: TestClient,
) -> None:
    response = admin_authenticated.post(
        "/v1/users/2/transfer", json={"company_id": 999}
    )
    assert response.status_code == 404


def test_cannot_transfer_to_same_company(admin_authenticated: TestClient) -> None:
    response = admin_authenticated.post(
        "/v1/users/2/transfer", json={"company_id": 1}
    )
    assert response.status_code == 403
    rs = response.json()
    assert rs["msg"] == "User already belongs to the target company"
