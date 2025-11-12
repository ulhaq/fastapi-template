from fastapi.testclient import TestClient


def test_get_authenticated_user(admin_authenticated: TestClient) -> None:
    response = admin_authenticated.get("/users/me")
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

    assert len(rs["roles"][0]["permissions"]) == 19
    assert rs["roles"][0]["permissions"][0]["id"] == 1
    assert rs["roles"][0]["permissions"][0]["name"] == "read_company"
    assert (
        rs["roles"][0]["permissions"][0]["description"]
        == "Allows the user to read company accounts."
    )

    assert rs["roles"][0]["permissions"][1]["id"] == 2
    assert rs["roles"][0]["permissions"][1]["name"] == "create_company"
    assert (
        rs["roles"][0]["permissions"][1]["description"]
        == "Allows the user to create new company accounts."
    )

    assert rs["roles"][0]["permissions"][2]["id"] == 3
    assert rs["roles"][0]["permissions"][2]["name"] == "update_company"
    assert (
        rs["roles"][0]["permissions"][2]["description"]
        == "Allows the user to update company accounts."
    )

    assert rs["roles"][0]["permissions"][3]["id"] == 4
    assert rs["roles"][0]["permissions"][3]["name"] == "delete_company"
    assert (
        rs["roles"][0]["permissions"][3]["description"]
        == "Allows the user to delete company accounts."
    )

    assert rs["roles"][0]["permissions"][4]["id"] == 5
    assert rs["roles"][0]["permissions"][4]["name"] == "manage_company_user"
    assert (
        rs["roles"][0]["permissions"][4]["description"]
        == "Allows the user to manage companies' users."
    )

    assert rs["roles"][0]["permissions"][5]["id"] == 6
    assert rs["roles"][0]["permissions"][5]["name"] == "read_user"
    assert (
        rs["roles"][0]["permissions"][5]["description"]
        == "Allows the user to read user."
    )

    assert rs["roles"][0]["permissions"][6]["id"] == 7
    assert rs["roles"][0]["permissions"][6]["name"] == "create_user"
    assert (
        rs["roles"][0]["permissions"][6]["description"]
        == "Allows the user to create new user."
    )

    assert rs["roles"][0]["permissions"][7]["id"] == 8
    assert rs["roles"][0]["permissions"][7]["name"] == "update_user"
    assert (
        rs["roles"][0]["permissions"][7]["description"]
        == "Allows the user to update user."
    )

    assert rs["roles"][0]["permissions"][8]["id"] == 9
    assert rs["roles"][0]["permissions"][8]["name"] == "delete_user"
    assert (
        rs["roles"][0]["permissions"][8]["description"]
        == "Allows the user to delete user."
    )

    assert rs["roles"][0]["permissions"][9]["id"] == 10
    assert rs["roles"][0]["permissions"][9]["name"] == "read_role"
    assert (
        rs["roles"][0]["permissions"][9]["description"]
        == "Allows the user to read roles."
    )

    assert rs["roles"][0]["permissions"][10]["id"] == 11
    assert rs["roles"][0]["permissions"][10]["name"] == "create_role"
    assert (
        rs["roles"][0]["permissions"][10]["description"]
        == "Allows the user to create new roles."
    )

    assert rs["roles"][0]["permissions"][11]["id"] == 12
    assert rs["roles"][0]["permissions"][11]["name"] == "update_role"
    assert (
        rs["roles"][0]["permissions"][11]["description"]
        == "Allows the user to update roles."
    )

    assert rs["roles"][0]["permissions"][12]["id"] == 13
    assert rs["roles"][0]["permissions"][12]["name"] == "delete_role"
    assert (
        rs["roles"][0]["permissions"][12]["description"]
        == "Allows the user to delete roles."
    )

    assert rs["roles"][0]["permissions"][13]["id"] == 14
    assert rs["roles"][0]["permissions"][13]["name"] == "manage_user_role"
    assert (
        rs["roles"][0]["permissions"][13]["description"]
        == "Allows the user to manage users' roles."
    )

    assert rs["roles"][0]["permissions"][14]["id"] == 15
    assert rs["roles"][0]["permissions"][14]["name"] == "read_permission"
    assert (
        rs["roles"][0]["permissions"][14]["description"]
        == "Allows the user to read permissions."
    )

    assert rs["roles"][0]["permissions"][15]["id"] == 16
    assert rs["roles"][0]["permissions"][15]["name"] == "create_permission"
    assert (
        rs["roles"][0]["permissions"][15]["description"]
        == "Allows the user to create new permissions."
    )

    assert rs["roles"][0]["permissions"][16]["id"] == 17
    assert rs["roles"][0]["permissions"][16]["name"] == "update_permission"
    assert (
        rs["roles"][0]["permissions"][16]["description"]
        == "Allows the user to update permissions."
    )

    assert rs["roles"][0]["permissions"][17]["id"] == 18
    assert rs["roles"][0]["permissions"][17]["name"] == "delete_permission"
    assert (
        rs["roles"][0]["permissions"][17]["description"]
        == "Allows the user to delete permissions."
    )

    assert rs["roles"][0]["permissions"][18]["id"] == 19
    assert rs["roles"][0]["permissions"][18]["name"] == "manage_role_permission"
    assert (
        rs["roles"][0]["permissions"][18]["description"]
        == "Allows the user to manage roles' permissions."
    )

    assert rs["created_at"]
    assert rs["updated_at"]


def test_create_a_user(admin_authenticated: TestClient) -> None:
    response = admin_authenticated.post(
        "/users",
        json={
            "name": "John Doe",
            "email": "new@testing.com",
            "password": "password",
            "company_id": 1,
        },
    )
    assert response.status_code == 201
    rs = response.json()
    assert rs["id"] == 4
    assert rs["name"] == "John Doe"
    assert rs["email"] == "new@testing.com"

    assert rs["roles"] == []

    assert rs["created_at"]
    assert rs["updated_at"]


def test_update_authenticated_user_profile(
    admin_authenticated: TestClient, client: TestClient
) -> None:
    response = admin_authenticated.put(
        "/users/me",
        json={"name": "John Doe", "email": "new@testing.com"},
    )
    assert response.status_code == 200
    rs = response.json()
    assert rs["id"] == 1
    assert rs["name"] == "John Doe"
    assert rs["email"] == "new@testing.com"

    response = client.post(
        "/auth/token",
        data={"username": "new@testing.com", "password": "password"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    rs = response.json()
    access_token = rs["access_token"]

    response = client.get(
        "/users/me", headers={"Authorization": f"Bearer {access_token}"}
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
        "/users/me/change-password",
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
        "/auth/token",
        data={"username": "admin@example.org", "password": "new password"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    rs = response.json()
    access_token = rs["access_token"]

    response = client.get(
        "/users/me", headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 200
    rs = response.json()
    assert rs["id"] == 1
    assert rs["name"] == "Admin"
    assert rs["email"] == "admin@example.org"


def test_manage_roles_of_a_user(admin_authenticated: TestClient) -> None:
    response = admin_authenticated.post(
        "/users/2/roles",
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

    assert len(rs["roles"][0]["permissions"]) == 19
    assert rs["roles"][0]["permissions"][0]["id"] == 1
    assert rs["roles"][0]["permissions"][0]["name"] == "read_company"
    assert (
        rs["roles"][0]["permissions"][0]["description"]
        == "Allows the user to read company accounts."
    )

    assert rs["roles"][0]["permissions"][1]["id"] == 2
    assert rs["roles"][0]["permissions"][1]["name"] == "create_company"
    assert (
        rs["roles"][0]["permissions"][1]["description"]
        == "Allows the user to create new company accounts."
    )

    assert rs["roles"][0]["permissions"][2]["id"] == 3
    assert rs["roles"][0]["permissions"][2]["name"] == "update_company"
    assert (
        rs["roles"][0]["permissions"][2]["description"]
        == "Allows the user to update company accounts."
    )

    assert rs["roles"][0]["permissions"][3]["id"] == 4
    assert rs["roles"][0]["permissions"][3]["name"] == "delete_company"
    assert (
        rs["roles"][0]["permissions"][3]["description"]
        == "Allows the user to delete company accounts."
    )

    assert rs["roles"][0]["permissions"][4]["id"] == 5
    assert rs["roles"][0]["permissions"][4]["name"] == "manage_company_user"
    assert (
        rs["roles"][0]["permissions"][4]["description"]
        == "Allows the user to manage companies' users."
    )

    assert rs["roles"][0]["permissions"][5]["id"] == 6
    assert rs["roles"][0]["permissions"][5]["name"] == "read_user"
    assert (
        rs["roles"][0]["permissions"][5]["description"]
        == "Allows the user to read user."
    )

    assert rs["roles"][0]["permissions"][6]["id"] == 7
    assert rs["roles"][0]["permissions"][6]["name"] == "create_user"
    assert (
        rs["roles"][0]["permissions"][6]["description"]
        == "Allows the user to create new user."
    )

    assert rs["roles"][0]["permissions"][7]["id"] == 8
    assert rs["roles"][0]["permissions"][7]["name"] == "update_user"
    assert (
        rs["roles"][0]["permissions"][7]["description"]
        == "Allows the user to update user."
    )

    assert rs["roles"][0]["permissions"][8]["id"] == 9
    assert rs["roles"][0]["permissions"][8]["name"] == "delete_user"
    assert (
        rs["roles"][0]["permissions"][8]["description"]
        == "Allows the user to delete user."
    )

    assert rs["roles"][0]["permissions"][9]["id"] == 10
    assert rs["roles"][0]["permissions"][9]["name"] == "read_role"
    assert (
        rs["roles"][0]["permissions"][9]["description"]
        == "Allows the user to read roles."
    )

    assert rs["roles"][0]["permissions"][10]["id"] == 11
    assert rs["roles"][0]["permissions"][10]["name"] == "create_role"
    assert (
        rs["roles"][0]["permissions"][10]["description"]
        == "Allows the user to create new roles."
    )

    assert rs["roles"][0]["permissions"][11]["id"] == 12
    assert rs["roles"][0]["permissions"][11]["name"] == "update_role"
    assert (
        rs["roles"][0]["permissions"][11]["description"]
        == "Allows the user to update roles."
    )

    assert rs["roles"][0]["permissions"][12]["id"] == 13
    assert rs["roles"][0]["permissions"][12]["name"] == "delete_role"
    assert (
        rs["roles"][0]["permissions"][12]["description"]
        == "Allows the user to delete roles."
    )

    assert rs["roles"][0]["permissions"][13]["id"] == 14
    assert rs["roles"][0]["permissions"][13]["name"] == "manage_user_role"
    assert (
        rs["roles"][0]["permissions"][13]["description"]
        == "Allows the user to manage users' roles."
    )

    assert rs["roles"][0]["permissions"][14]["id"] == 15
    assert rs["roles"][0]["permissions"][14]["name"] == "read_permission"
    assert (
        rs["roles"][0]["permissions"][14]["description"]
        == "Allows the user to read permissions."
    )

    assert rs["roles"][0]["permissions"][15]["id"] == 16
    assert rs["roles"][0]["permissions"][15]["name"] == "create_permission"
    assert (
        rs["roles"][0]["permissions"][15]["description"]
        == "Allows the user to create new permissions."
    )

    assert rs["roles"][0]["permissions"][16]["id"] == 17
    assert rs["roles"][0]["permissions"][16]["name"] == "update_permission"
    assert (
        rs["roles"][0]["permissions"][16]["description"]
        == "Allows the user to update permissions."
    )

    assert rs["roles"][0]["permissions"][17]["id"] == 18
    assert rs["roles"][0]["permissions"][17]["name"] == "delete_permission"
    assert (
        rs["roles"][0]["permissions"][17]["description"]
        == "Allows the user to delete permissions."
    )

    assert rs["roles"][0]["permissions"][18]["id"] == 19
    assert rs["roles"][0]["permissions"][18]["name"] == "manage_role_permission"
    assert (
        rs["roles"][0]["permissions"][18]["description"]
        == "Allows the user to manage roles' permissions."
    )

    assert rs["roles"][1]["id"] == 2
    assert rs["roles"][1]["name"] == "standard"
    assert rs["roles"][1]["description"] == "Access to manage and view own resources."

    assert len(rs["roles"][1]["permissions"]) == 2
    assert rs["roles"][1]["permissions"][0]["id"] == 6
    assert rs["roles"][1]["permissions"][0]["name"] == "read_user"
    assert (
        rs["roles"][1]["permissions"][0]["description"]
        == "Allows the user to read user."
    )

    assert rs["roles"][1]["permissions"][1]["id"] == 7
    assert rs["roles"][1]["permissions"][1]["name"] == "create_user"
    assert (
        rs["roles"][1]["permissions"][1]["description"]
        == "Allows the user to create new user."
    )

    assert rs["created_at"]
    assert rs["updated_at"]

    response = admin_authenticated.post(
        "/users/2/roles",
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
    assert rs["roles"][0]["permissions"][0]["id"] == 6
    assert rs["roles"][0]["permissions"][0]["name"] == "read_user"
    assert (
        rs["roles"][0]["permissions"][0]["description"]
        == "Allows the user to read user."
    )

    assert rs["roles"][0]["permissions"][1]["id"] == 7
    assert rs["roles"][0]["permissions"][1]["name"] == "create_user"
    assert (
        rs["roles"][0]["permissions"][1]["description"]
        == "Allows the user to create new user."
    )

    assert rs["created_at"]
    assert rs["updated_at"]


def test_delete_a_user(admin_authenticated: TestClient) -> None:
    response = admin_authenticated.delete("/users/2")
    assert response.status_code == 204


def test_cannot_manage_own_roles(admin_authenticated: TestClient) -> None:
    response = admin_authenticated.post(
        "/users/1/roles",
        json={
            "role_ids": [1, 2],
        },
    )

    assert response.status_code == 403
    rs = response.json()
    assert rs["msg"] == "You are not allowed to manage your own roles"


def test_cannot_create_a_user_while_unauthorized(client: TestClient) -> None:
    rs = client.post(
        "auth/token",
        data={"username": "no_roles@example.org", "password": "password"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    ).json()

    response = client.post(
        "/users",
        json={
            "name": "John Doe",
            "email": "new@testing.com",
            "password": "password",
            "company_id": 1,
        },
        headers={"Authorization": f"Bearer {rs['access_token']}"},
    )
    assert response.status_code == 403
    rs = response.json()
    assert rs["msg"] == "You are not authorized to perform this action"


def test_cannot_delete_a_user_while_unauthorized(
    standard_authenticated: TestClient,
) -> None:
    response = standard_authenticated.delete("/users/1")
    assert response.status_code == 403
    rs = response.json()
    assert rs["msg"] == "You are not authorized to perform this action"
