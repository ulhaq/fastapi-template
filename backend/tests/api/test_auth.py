import time
from unittest.mock import patch
from fastapi.testclient import TestClient
from pytest_mock import MockerFixture


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
    assert rs["id"] == 3
    assert rs["name"] == "new user"

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
    assert rs["refresh_token"]


def test_refresh_access_token(client: TestClient) -> None:
    with patch("src.core.config.settings.auth_access_token_expiry", 2):
        response = client.post(
            "auth/token",
            data={"username": "admin@example.org", "password": "password"},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        assert response.status_code == 200
        rs = response.json()
        old_access_token = rs["access_token"]
        old_refresh_token = rs["refresh_token"]

        response = client.get(
            "users/me", headers={"Authorization": f"Bearer {old_access_token}"}
        )
        assert response.status_code == 200

        time.sleep(2)

        response = client.get(
            "users/me", headers={"Authorization": f"Bearer {old_access_token}"}
        )
        assert response.status_code == 401

        response = client.post("auth/refresh")
        assert response.status_code == 200
        rs = response.json()
        assert rs["token_type"] == "bearer"
        assert rs["access_token"] and rs["access_token"] != old_access_token
        assert rs["refresh_token"] and rs["refresh_token"] == old_refresh_token

        response = client.get(
            "users/me", headers={"Authorization": f"Bearer {rs['access_token']}"}
        )
        assert response.status_code == 200


def test_logout(client: TestClient) -> None:
    response = client.post(
        "auth/token",
        data={"username": "admin@example.org", "password": "password"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == 200
    assert "refresh_token=" in response.headers["set-cookie"]

    response = client.post("auth/logout")
    assert response.status_code == 204
    assert "refresh_token=" in dict(response.headers).get("set-cookie", "")


def test_request_password_reset(client: TestClient) -> None:
    response = client.post(
        "auth/reset-password/request", json={"email": "admin@example.org"}
    )
    assert response.status_code == 202


def test_reset_password(mocker: MockerFixture, client: TestClient) -> None:
    mock_send = mocker.patch("src.services.auth.send_email")

    client.post("auth/reset-password/request", json={"email": "admin@example.org"})

    mock_send.assert_called_once()

    token = mock_send.call_args.kwargs["data"]["reset_url"].split("token=")[1]

    response = client.post(
        "auth/reset-password", json={"token": token, "password": "new password"}
    )
    assert response.status_code == 204

    response = client.post(
        "auth/reset-password", json={"token": token, "password": "new password"}
    )
    assert response.status_code == 401
    rs = response.json()
    assert rs["error_code"] == "token_invalid"
    assert rs["msg"] == "Token invalid"

    response = client.post(
        "auth/token",
        data={"username": "admin@example.org", "password": "new password"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == 200


def test_request_password_reset_with_non_existent_email(client: TestClient) -> None:
    response = client.post(
        "auth/reset-password/request", json={"email": "non-existent@example.org"}
    )
    assert response.status_code == 202


def test_cannot_refresh_access_token_with_invalid_token(client: TestClient) -> None:
    response = client.post(
        "auth/refresh",
        cookies={"refresh_token": "invalidtoken"},
    )
    assert response.status_code == 401
    rs = response.json()
    assert rs["error_code"] == "token_invalid"
    assert rs["msg"] == "Token invalid"


def test_cannot_refresh_access_token_with_expired_token(client: TestClient) -> None:
    with patch("src.core.config.settings.auth_refresh_token_expiry", -1):
        response = client.post(
            "auth/token",
            data={"username": "admin@example.org", "password": "password"},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        assert response.status_code == 200
        rs = response.json()

        response = client.post(
            "auth/refresh", cookies={"refresh_token": rs["refresh_token"]}
        )
        assert response.status_code == 401
        rs = response.json()
        assert rs["error_code"] == "token_expired"
        assert rs["msg"] == "Token expired"


def test_cannot_reset_password_with_invalid_token(client: TestClient) -> None:
    response = client.post(
        "auth/reset-password",
        json={"token": "invalidtoken", "password": "new password"},
    )
    assert response.status_code == 401
    rs = response.json()
    assert rs["error_code"] == "signature_invalid"
    assert rs["msg"] == "Signature invalid"


def test_cannot_reset_password_with_expired_token(
    mocker: MockerFixture, client: TestClient
) -> None:
    mock_send = mocker.patch("src.services.auth.send_email")

    with patch("src.core.config.settings.auth_password_reset_expiry", -1):
        client.post("auth/reset-password/request", json={"email": "admin@example.org"})

        token = mock_send.call_args.kwargs["data"]["reset_url"].split("token=")[1]

        response = client.post(
            "auth/reset-password", json={"token": token, "password": "new password"}
        )
        assert response.status_code == 401
        rs = response.json()
        assert rs["error_code"] == "signature_expired"
        assert rs["msg"] == "Signature expired"


def test_cannot_register_an_account_with_already_existing_email(
    client: TestClient,
) -> None:
    response = client.post(
        "/auth/register",
        json={"name": "new user", "email": "admin@example.org", "password": "password"},
    )
    assert response.status_code == 409
    rs = response.json()
    assert rs["error_code"] == "email_already_exists"
    assert rs["msg"] == "Account already exists. [email=admin@example.org]"


def test_cannot_get_access_token_with_wrong_credentials(client: TestClient) -> None:
    response = client.post(
        "auth/token",
        data={"username": "no-user@example.org", "password": "password"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == 401
    rs = response.json()
    assert rs["error_code"] == "login_failed"
    assert rs["msg"] == "Not authenticated"
