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

    assert len(rs["roles"][0]["permissions"]) == 14
    assert rs["roles"][0]["permissions"][0]["id"] == 1
    assert rs["roles"][0]["permissions"][0]["name"] == "read_user"
    assert (
        rs["roles"][0]["permissions"][0]["description"]
        == "Allows the user to read user accounts."
    )

    assert rs["roles"][0]["permissions"][1]["id"] == 2
    assert rs["roles"][0]["permissions"][1]["name"] == "create_user"
    assert (
        rs["roles"][0]["permissions"][1]["description"]
        == "Allows the user to create new user accounts."
    )

    assert rs["roles"][0]["permissions"][2]["id"] == 3
    assert rs["roles"][0]["permissions"][2]["name"] == "update_user"
    assert (
        rs["roles"][0]["permissions"][2]["description"]
        == "Allows the user to update user accounts."
    )

    assert rs["roles"][0]["permissions"][3]["id"] == 4
    assert rs["roles"][0]["permissions"][3]["name"] == "delete_user"
    assert (
        rs["roles"][0]["permissions"][3]["description"]
        == "Allows the user to delete user accounts."
    )

    assert rs["roles"][0]["permissions"][4]["id"] == 5
    assert rs["roles"][0]["permissions"][4]["name"] == "read_role"
    assert (
        rs["roles"][0]["permissions"][4]["description"]
        == "Allows the user to read roles."
    )

    assert rs["roles"][0]["permissions"][5]["id"] == 6
    assert rs["roles"][0]["permissions"][5]["name"] == "create_role"
    assert (
        rs["roles"][0]["permissions"][5]["description"]
        == "Allows the user to create new roles."
    )

    assert rs["roles"][0]["permissions"][6]["id"] == 7
    assert rs["roles"][0]["permissions"][6]["name"] == "update_role"
    assert (
        rs["roles"][0]["permissions"][6]["description"]
        == "Allows the user to update roles."
    )

    assert rs["roles"][0]["permissions"][7]["id"] == 8
    assert rs["roles"][0]["permissions"][7]["name"] == "delete_role"
    assert (
        rs["roles"][0]["permissions"][7]["description"]
        == "Allows the user to delete roles."
    )

    assert rs["roles"][0]["permissions"][8]["id"] == 9
    assert rs["roles"][0]["permissions"][8]["name"] == "manage_user_role"
    assert (
        rs["roles"][0]["permissions"][8]["description"]
        == "Allows the user to manage users' roles."
    )

    assert rs["roles"][0]["permissions"][9]["id"] == 10
    assert rs["roles"][0]["permissions"][9]["name"] == "read_permission"
    assert (
        rs["roles"][0]["permissions"][9]["description"]
        == "Allows the user to read permissions."
    )

    assert rs["roles"][0]["permissions"][10]["id"] == 11
    assert rs["roles"][0]["permissions"][10]["name"] == "create_permission"
    assert (
        rs["roles"][0]["permissions"][10]["description"]
        == "Allows the user to create new permissions."
    )

    assert rs["roles"][0]["permissions"][11]["id"] == 12
    assert rs["roles"][0]["permissions"][11]["name"] == "update_permission"
    assert (
        rs["roles"][0]["permissions"][11]["description"]
        == "Allows the user to update permissions."
    )

    assert rs["roles"][0]["permissions"][12]["id"] == 13
    assert rs["roles"][0]["permissions"][12]["name"] == "delete_permission"
    assert (
        rs["roles"][0]["permissions"][12]["description"]
        == "Allows the user to delete permissions."
    )

    assert rs["roles"][0]["permissions"][13]["id"] == 14
    assert rs["roles"][0]["permissions"][13]["name"] == "manage_role_permission"
    assert (
        rs["roles"][0]["permissions"][13]["description"]
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


def test_manage_roles_of_a_user(admin_authenticated: TestClient) -> None:
    response = admin_authenticated.post(
        "/users/1/roles",
        json={
            "role_ids": [1, 2],
        },
    )
    assert response.status_code == 200
    rs = response.json()
    assert rs["id"] == 1
    assert rs["name"] == "Admin"
    assert rs["email"] == "admin@example.org"

    assert len(rs["roles"]) == 2
    assert rs["roles"][0]["id"] == 1
    assert rs["roles"][0]["name"] == "admin"
    assert (
        rs["roles"][0]["description"]
        == "Full access to all system features and settings."
    )

    assert len(rs["roles"][0]["permissions"]) == 14
    assert rs["roles"][0]["permissions"][0]["id"] == 1
    assert rs["roles"][0]["permissions"][0]["name"] == "read_user"
    assert (
        rs["roles"][0]["permissions"][0]["description"]
        == "Allows the user to read user accounts."
    )

    assert rs["roles"][0]["permissions"][1]["id"] == 2
    assert rs["roles"][0]["permissions"][1]["name"] == "create_user"
    assert (
        rs["roles"][0]["permissions"][1]["description"]
        == "Allows the user to create new user accounts."
    )

    assert rs["roles"][0]["permissions"][2]["id"] == 3
    assert rs["roles"][0]["permissions"][2]["name"] == "update_user"
    assert (
        rs["roles"][0]["permissions"][2]["description"]
        == "Allows the user to update user accounts."
    )

    assert rs["roles"][0]["permissions"][3]["id"] == 4
    assert rs["roles"][0]["permissions"][3]["name"] == "delete_user"
    assert (
        rs["roles"][0]["permissions"][3]["description"]
        == "Allows the user to delete user accounts."
    )

    assert rs["roles"][0]["permissions"][4]["id"] == 5
    assert rs["roles"][0]["permissions"][4]["name"] == "read_role"
    assert (
        rs["roles"][0]["permissions"][4]["description"]
        == "Allows the user to read roles."
    )

    assert rs["roles"][0]["permissions"][5]["id"] == 6
    assert rs["roles"][0]["permissions"][5]["name"] == "create_role"
    assert (
        rs["roles"][0]["permissions"][5]["description"]
        == "Allows the user to create new roles."
    )

    assert rs["roles"][0]["permissions"][6]["id"] == 7
    assert rs["roles"][0]["permissions"][6]["name"] == "update_role"
    assert (
        rs["roles"][0]["permissions"][6]["description"]
        == "Allows the user to update roles."
    )

    assert rs["roles"][0]["permissions"][7]["id"] == 8
    assert rs["roles"][0]["permissions"][7]["name"] == "delete_role"
    assert (
        rs["roles"][0]["permissions"][7]["description"]
        == "Allows the user to delete roles."
    )

    assert rs["roles"][0]["permissions"][8]["id"] == 9
    assert rs["roles"][0]["permissions"][8]["name"] == "manage_user_role"
    assert (
        rs["roles"][0]["permissions"][8]["description"]
        == "Allows the user to manage users' roles."
    )

    assert rs["roles"][0]["permissions"][9]["id"] == 10
    assert rs["roles"][0]["permissions"][9]["name"] == "read_permission"
    assert (
        rs["roles"][0]["permissions"][9]["description"]
        == "Allows the user to read permissions."
    )

    assert rs["roles"][0]["permissions"][10]["id"] == 11
    assert rs["roles"][0]["permissions"][10]["name"] == "create_permission"
    assert (
        rs["roles"][0]["permissions"][10]["description"]
        == "Allows the user to create new permissions."
    )

    assert rs["roles"][0]["permissions"][11]["id"] == 12
    assert rs["roles"][0]["permissions"][11]["name"] == "update_permission"
    assert (
        rs["roles"][0]["permissions"][11]["description"]
        == "Allows the user to update permissions."
    )

    assert rs["roles"][0]["permissions"][12]["id"] == 13
    assert rs["roles"][0]["permissions"][12]["name"] == "delete_permission"
    assert (
        rs["roles"][0]["permissions"][12]["description"]
        == "Allows the user to delete permissions."
    )

    assert rs["roles"][0]["permissions"][13]["id"] == 14
    assert rs["roles"][0]["permissions"][13]["name"] == "manage_role_permission"
    assert (
        rs["roles"][0]["permissions"][13]["description"]
        == "Allows the user to manage roles' permissions."
    )

    assert rs["roles"][1]["id"] == 2
    assert rs["roles"][1]["name"] == "standard"
    assert rs["roles"][1]["description"] == "Access to manage and view own resources."

    assert len(rs["roles"][1]["permissions"]) == 2
    assert rs["roles"][1]["permissions"][0]["id"] == 1
    assert rs["roles"][1]["permissions"][0]["name"] == "read_user"
    assert (
        rs["roles"][1]["permissions"][0]["description"]
        == "Allows the user to read user accounts."
    )

    assert rs["roles"][1]["permissions"][1]["id"] == 2
    assert rs["roles"][1]["permissions"][1]["name"] == "create_user"
    assert (
        rs["roles"][1]["permissions"][1]["description"]
        == "Allows the user to create new user accounts."
    )

    assert rs["created_at"]
    assert rs["updated_at"]

    response = admin_authenticated.post(
        "/users/1/roles",
        json={
            "role_ids": [2],
        },
    )
    assert response.status_code == 200
    rs = response.json()
    assert rs["id"] == 1
    assert rs["name"] == "Admin"
    assert rs["email"] == "admin@example.org"

    assert len(rs["roles"]) == 1
    assert rs["roles"][0]["id"] == 2
    assert rs["roles"][0]["name"] == "standard"
    assert rs["roles"][0]["description"] == "Access to manage and view own resources."

    assert len(rs["roles"][0]["permissions"]) == 2
    assert rs["roles"][0]["permissions"][0]["id"] == 1
    assert rs["roles"][0]["permissions"][0]["name"] == "read_user"
    assert (
        rs["roles"][0]["permissions"][0]["description"]
        == "Allows the user to read user accounts."
    )

    assert rs["roles"][0]["permissions"][1]["id"] == 2
    assert rs["roles"][0]["permissions"][1]["name"] == "create_user"
    assert (
        rs["roles"][0]["permissions"][1]["description"]
        == "Allows the user to create new user accounts."
    )

    assert rs["created_at"]
    assert rs["updated_at"]


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
