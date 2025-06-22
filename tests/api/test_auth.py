import logging
from fastapi.testclient import TestClient

log = logging.getLogger(__name__)


def test_register_an_account(client: TestClient) -> None:
    response = client.post(
        "/auth/register",
        json={
            "name": "new user",
            "email": "new_user@testing.com",
            "password": "test",
        },
    )
    assert response.status_code == 201
    rs = response.json()
    assert rs["id"] == 4
    assert rs["name"] == "new user"
    assert rs["email"] == "new_user@testing.com"

    assert rs["roles"] == []

    assert rs["created_at"]
    assert rs["updated_at"]


def test_get_access_token(client: TestClient) -> None:
    response = client.post(
        "auth/token",
        data={"username": "admin@example.org", "password": "password"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == 200
    rs = response.json()
    assert rs["token_type"] == "bearer"
    assert rs["access_token"]


def test_cannot_register_an_account_with_already_existing_email(
    client: TestClient,
) -> None:
    response = client.post(
        "/auth/register",
        json={
            "name": "new user",
            "email": "admin@example.org",
            "password": "test",
        },
    )
    assert response.status_code == 409
    rs = response.json()
    assert rs["msg"] == "Account already exists. [email=admin@example.org]"
