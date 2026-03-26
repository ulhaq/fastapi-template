from fastapi.testclient import TestClient

from src.enums import PERMISSION_DESCRIPTIONS, Permission


def test_get_authenticated_user(admin_authenticated: TestClient) -> None:
    response = admin_authenticated.get("/v1/users/me")
    assert response.status_code == 200
    rs = response.json()
    assert rs["id"] == 1
    assert rs["name"] == "Admin"
    assert rs["email"] == "admin@example.org"

    assert len(rs["roles"]) == 1
    assert rs["roles"][0]["id"] == 1
    assert rs["roles"][0]["name"] == "admin"
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


def test_create_a_user(admin_authenticated: TestClient) -> None:
    response = admin_authenticated.post(
        "/v1/users",
        json={
            "name": "John Doe",
            "email": "new@testing.com",
            "password": "password",
        },
    )
    assert response.status_code == 201
    rs = response.json()
    assert rs["id"] == 5
    assert rs["name"] == "John Doe"
    assert rs["email"] == "new@testing.com"

    assert rs["roles"] == []

    assert rs["created_at"]
    assert rs["updated_at"]


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


def test_update_authenticated_user_profile(
    admin_authenticated: TestClient, client: TestClient
) -> None:
    response = admin_authenticated.put(
        "/v1/users/me",
        json={"name": "John Doe", "email": "new@testing.com"},
    )
    assert response.status_code == 200
    rs = response.json()
    assert rs["id"] == 1
    assert rs["name"] == "John Doe"
    assert rs["email"] == "new@testing.com"

    response = client.post(
        "/v1/auth/token",
        data={"username": "new@testing.com", "password": "password"},
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
    assert rs["name"] == "John Doe"
    assert rs["email"] == "new@testing.com"


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
    assert len(permissions) == 2

    permission_names = {p["name"] for p in permissions}
    assert permission_names == {"read:user", "create:user"}

    for p in permissions:
        assert p["name"] in PERMISSION_DESCRIPTIONS
        assert p["description"] == PERMISSION_DESCRIPTIONS[Permission(p["name"])]

    assert rs["created_at"]
    assert rs["updated_at"]


def test_manage_roles_of_a_user(admin_authenticated: TestClient) -> None:
    response = admin_authenticated.post(
        "/v1/users/2/roles",
        json={
            "role_ids": [1, 2],
        },
    )
    assert response.status_code == 200
    rs = response.json()
    assert rs["id"] == 2
    assert rs["name"] == "Standard"
    assert rs["email"] == "standard@example.org"

    assert len(rs["roles"]) == 2
    assert rs["roles"][0]["id"] == 1
    assert rs["roles"][0]["name"] == "admin"
    assert (
        rs["roles"][0]["description"]
        == "Full access to all system features and settings."
    )

    assert len(rs["roles"][0]["permissions"]) == len(Permission)

    assert rs["roles"][1]["id"] == 2
    assert rs["roles"][1]["name"] == "standard"
    assert rs["roles"][1]["description"] == "Access to manage and view own resources."

    assert len(rs["roles"][1]["permissions"]) == 2
    standard_perm_names = {p["name"] for p in rs["roles"][1]["permissions"]}
    assert standard_perm_names == {"read:user", "create:user"}

    assert rs["created_at"]
    assert rs["updated_at"]

    response = admin_authenticated.post(
        "/v1/users/2/roles",
        json={
            "role_ids": [2],
        },
    )
    assert response.status_code == 200
    rs = response.json()
    assert rs["id"] == 2
    assert rs["name"] == "Standard"
    assert rs["email"] == "standard@example.org"

    assert len(rs["roles"]) == 1
    assert rs["roles"][0]["id"] == 2
    assert rs["roles"][0]["name"] == "standard"
    assert rs["roles"][0]["description"] == "Access to manage and view own resources."

    assert len(rs["roles"][0]["permissions"]) == 2
    standard_perm_names = {p["name"] for p in rs["roles"][0]["permissions"]}
    assert standard_perm_names == {"read:user", "create:user"}

    assert rs["created_at"]
    assert rs["updated_at"]


def test_delete_a_user(admin_authenticated: TestClient) -> None:
    response = admin_authenticated.delete("/v1/users/2")
    assert response.status_code == 204


def test_can_delete_admin_when_another_exists(admin_authenticated: TestClient) -> None:
    admin_authenticated.post("/v1/users/2/roles", json={"role_ids": [1]})

    response = admin_authenticated.delete("/v1/users/2")
    assert response.status_code == 204


def test_cannot_delete_last_admin(admin_authenticated: TestClient) -> None:
    response = admin_authenticated.delete("/v1/users/1")
    assert response.status_code == 403
    rs = response.json()
    assert rs["msg"] == (
        "Cannot perform this action: tenant must retain at least one "
        "user with role management access"
    )


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


def test_cannot_create_a_user_while_unauthorized(client: TestClient) -> None:
    rs = client.post(
        "/v1/auth/token",
        data={"username": "no_roles@example.org", "password": "password"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    ).json()

    response = client.post(
        "/v1/users",
        json={
            "name": "John Doe",
            "email": "new@testing.com",
            "password": "password",
        },
        headers={"Authorization": f"Bearer {rs['access_token']}"},
    )
    assert response.status_code == 403
    rs = response.json()
    assert rs["msg"] == "You are not authorized to perform this action"


def test_cannot_delete_a_user_while_unauthorized(
    standard_authenticated: TestClient,
) -> None:
    response = standard_authenticated.delete("/v1/users/1")
    assert response.status_code == 403
    rs = response.json()
    assert rs["msg"] == "You are not authorized to perform this action"
