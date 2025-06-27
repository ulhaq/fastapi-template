from fastapi.testclient import TestClient
from pytest_mock import MockerFixture, mocker as _mocker


def test_register_an_account(client: TestClient) -> None:
    response = client.post(
        "/auth/register",
        json={
            "name": "new user",
            "email": "new_user@testing.com",
            "password": "password",
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


def test_request_password_reset(client: TestClient) -> None:
    response = client.post("auth/reset-password", json={"email": "admin@example.org"})
    assert response.status_code == 204


def test_reset_password(mocker: MockerFixture, client: TestClient) -> None:
    mock_send = mocker.patch("src.services.auth.send_email")

    client.post("auth/reset-password", json={"email": "admin@example.org"})

    mock_send.assert_called_once()

    token = mock_send.call_args.kwargs["data"]["reset_url"].split("reset/")[1]

    response = client.post(
        f"auth/reset-password/{token}", json={"password": "new password"}
    )
    assert response.status_code == 204

    response = client.post(
        "auth/token",
        data={"username": "admin@example.org", "password": "new password"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == 200


def test_request_password_reset_with_non_existent_email(client: TestClient) -> None:
    response = client.post(
        "auth/reset-password", json={"email": "non-existent@example.org"}
    )
    assert response.status_code == 204


def test_cannot_reset_password_with_invalid_token(client: TestClient) -> None:
    token = "invalidtoken"

    response = client.post(
        f"auth/reset-password/{token}", json={"password": "new password"}
    )
    assert response.status_code == 401
    rs = response.json()
    assert rs["type"] == "NotAuthenticatedException"
    assert rs["msg"] == "Signature invalid"


def test_cannot_reset_password_with_expired_token(client: TestClient) -> None:
    token = "ImFkbWluQGV4YW1wbGUub3JnIg.aF8G0w.BdTusBenIsBI6wSVfzBk16ATs-I"

    response = client.post(
        f"auth/reset-password/{token}", json={"password": "new password"}
    )
    assert response.status_code == 401
    rs = response.json()
    assert rs["type"] == "NotAuthenticatedException"
    assert rs["msg"] == "Signature expired"


def test_cannot_register_an_account_with_already_existing_email(
    client: TestClient,
) -> None:
    response = client.post(
        "/auth/register",
        json={
            "name": "new user",
            "email": "admin@example.org",
            "password": "password",
        },
    )
    assert response.status_code == 409
    rs = response.json()
    assert rs["type"] == "AlreadyExistsException"
    assert rs["msg"] == "Account already exists. [email=admin@example.org]"


def test_cannot_get_access_token_with_wrong_credentials(client: TestClient) -> None:
    response = client.post(
        "auth/token",
        data={"username": "no-user@example.org", "password": "password"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == 401
    rs = response.json()
    assert rs["type"] == "NotAuthenticatedException"
    assert rs["msg"] == "Not authenticated"
