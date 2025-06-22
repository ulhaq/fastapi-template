import logging
from fastapi.testclient import TestClient

log = logging.getLogger(__name__)


def test_get_all_permissions(admin_authenticated: TestClient) -> None:
    response = admin_authenticated.get("/permissions?page_size=20")
    assert response.status_code == 200
    rs = response.json()

    assert rs["page_number"] == 1
    assert rs["page_size"] == 20
    assert rs["total"] == 14

    assert rs["items"][0]["id"] == 1
    assert rs["items"][0]["name"] == "read_user"
    assert rs["items"][0]["description"] == "Allows the user to read user accounts."

    assert len(rs["items"][0]["roles"]) == 2
    assert rs["items"][0]["roles"][0]["id"] == 1
    assert rs["items"][0]["roles"][0]["name"] == "admin"
    assert (
        rs["items"][0]["roles"][0]["description"]
        == "Full access to all system features and settings."
    )

    assert rs["items"][0]["roles"][1]["id"] == 2
    assert rs["items"][0]["roles"][1]["name"] == "standard"
    assert (
        rs["items"][0]["roles"][1]["description"]
        == "Access to manage and view own resources."
    )

    assert rs["items"][0]["created_at"]
    assert rs["items"][0]["updated_at"]

    assert rs["items"][1]["id"] == 2
    assert rs["items"][1]["name"] == "create_user"
    assert (
        rs["items"][1]["description"] == "Allows the user to create new user accounts."
    )

    assert len(rs["items"][1]["roles"]) == 2
    assert rs["items"][1]["roles"][0]["id"] == 1
    assert rs["items"][1]["roles"][0]["name"] == "admin"
    assert (
        rs["items"][1]["roles"][0]["description"]
        == "Full access to all system features and settings."
    )

    assert rs["items"][1]["roles"][1]["id"] == 2
    assert rs["items"][1]["roles"][1]["name"] == "standard"
    assert (
        rs["items"][1]["roles"][1]["description"]
        == "Access to manage and view own resources."
    )
    assert rs["items"][1]["created_at"]
    assert rs["items"][1]["updated_at"]

    assert rs["items"][2]["id"] == 3
    assert rs["items"][2]["name"] == "update_user"
    assert rs["items"][2]["description"] == "Allows the user to update user accounts."

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
    assert rs["items"][3]["name"] == "delete_user"
    assert rs["items"][3]["description"] == "Allows the user to delete user accounts."

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
    assert rs["items"][4]["name"] == "read_role"
    assert rs["items"][4]["description"] == "Allows the user to read roles."

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
    assert rs["items"][5]["name"] == "create_role"
    assert rs["items"][5]["description"] == "Allows the user to create new roles."

    assert len(rs["items"][5]["roles"]) == 1
    assert rs["items"][5]["roles"][0]["id"] == 1
    assert rs["items"][5]["roles"][0]["name"] == "admin"
    assert (
        rs["items"][5]["roles"][0]["description"]
        == "Full access to all system features and settings."
    )

    assert rs["items"][5]["created_at"]
    assert rs["items"][5]["updated_at"]

    assert rs["items"][6]["id"] == 7
    assert rs["items"][6]["name"] == "update_role"
    assert rs["items"][6]["description"] == "Allows the user to update roles."

    assert len(rs["items"][6]["roles"]) == 1
    assert rs["items"][6]["roles"][0]["id"] == 1
    assert rs["items"][6]["roles"][0]["name"] == "admin"
    assert (
        rs["items"][6]["roles"][0]["description"]
        == "Full access to all system features and settings."
    )

    assert rs["items"][6]["created_at"]
    assert rs["items"][6]["updated_at"]

    assert rs["items"][7]["id"] == 8
    assert rs["items"][7]["name"] == "delete_role"
    assert rs["items"][7]["description"] == "Allows the user to delete roles."

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
    assert rs["items"][8]["name"] == "manage_user_role"
    assert rs["items"][8]["description"] == "Allows the user to manage users' roles."

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
    assert rs["items"][9]["name"] == "read_permission"
    assert rs["items"][9]["description"] == "Allows the user to read permissions."

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
    assert rs["items"][10]["name"] == "create_permission"
    assert (
        rs["items"][10]["description"] == "Allows the user to create new permissions."
    )

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
    assert rs["items"][11]["name"] == "update_permission"
    assert rs["items"][11]["description"] == "Allows the user to update permissions."

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
    assert rs["items"][12]["name"] == "delete_permission"
    assert rs["items"][12]["description"] == "Allows the user to delete permissions."

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
    assert rs["items"][13]["name"] == "manage_role_permission"
    assert (
        rs["items"][13]["description"]
        == "Allows the user to manage roles' permissions."
    )

    assert len(rs["items"][13]["roles"]) == 1
    assert rs["items"][13]["roles"][0]["id"] == 1
    assert rs["items"][13]["roles"][0]["name"] == "admin"
    assert (
        rs["items"][13]["roles"][0]["description"]
        == "Full access to all system features and settings."
    )

    assert rs["items"][13]["created_at"]
    assert rs["items"][13]["updated_at"]


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
    assert rs["id"] == 15
    assert rs["name"] == "test permission"
    assert rs["description"] == "description of test permission"

    assert rs["roles"] == []

    assert rs["created_at"]
    assert rs["updated_at"]


def test_update_a_permission(admin_authenticated: TestClient) -> None:
    response = admin_authenticated.put(
        "/permissions/1",
        json={
            "name": "User Read Permission",
            "description": "Allows the user to read any user accounts.",
        },
    )
    assert response.status_code == 200
    rs = response.json()
    assert rs["id"] == 1
    assert rs["name"] == "User Read Permission"
    assert rs["description"] == "Allows the user to read any user accounts."

    assert len(rs["roles"]) == 2
    assert rs["roles"][0]["id"] == 1
    assert rs["roles"][0]["name"] == "admin"
    assert (
        rs["roles"][0]["description"]
        == "Full access to all system features and settings."
    )

    assert rs["roles"][1]["id"] == 2
    assert rs["roles"][1]["name"] == "standard"
    assert rs["roles"][1]["description"] == "Access to manage and view own resources."

    assert rs["created_at"]
    assert rs["updated_at"]


def test_retrieve_a_permission(admin_authenticated: TestClient) -> None:
    response = admin_authenticated.get("/permissions/1")
    assert response.status_code == 200
    rs = response.json()

    assert rs["id"] == 1
    assert rs["name"] == "read_user"
    assert rs["description"] == "Allows the user to read user accounts."

    assert len(rs["roles"]) == 2
    assert rs["roles"][0]["id"] == 1
    assert rs["roles"][0]["name"] == "admin"
    assert (
        rs["roles"][0]["description"]
        == "Full access to all system features and settings."
    )

    assert rs["roles"][1]["id"] == 2
    assert rs["roles"][1]["name"] == "standard"
    assert rs["roles"][1]["description"] == "Access to manage and view own resources."

    assert rs["created_at"]
    assert rs["updated_at"]


def test_delete_a_permission(admin_authenticated: TestClient) -> None:
    response = admin_authenticated.delete("/permissions/1")
    assert response.status_code == 204


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
