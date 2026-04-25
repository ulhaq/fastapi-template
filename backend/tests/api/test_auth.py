import time
from unittest.mock import patch
from fastapi.testclient import TestClient
from pytest_mock import MockerFixture

from src.core.limiter import limiter
from src.enums import ADMIN_ROLE_NAME, MEMBER_ROLE_NAME, DEFAULT_ROLES, Permission


def _do_register(client: TestClient, email: str = "new_user@example.org") -> None:
    client.post("/v1/auth/register", json={"email": email})


def _do_verify(
    mocker: MockerFixture, client: TestClient, email: str = "new_user@example.org"
) -> str:
    """Register, capture verification token, verify email, return setup_token."""
    mock_send = mocker.patch("src.services.auth.send_email")
    _do_register(client, email)
    verify_url = mock_send.call_args.kwargs["data"]["verify_url"]
    token = verify_url.split("token=")[1]
    mock_send.stop()

    rs = client.post("/v1/auth/verify-email", json={"token": token}).json()
    return rs["setup_token"]


def _do_complete(
    mocker: MockerFixture,
    client: TestClient,
    email: str = "new_user@example.org",
    name: str = "New User",
    password: str = "password1",
) -> dict:
    """Full registration flow - returns the Token response JSON."""
    setup_token = _do_verify(mocker, client, email)
    response = client.post(
        "/v1/auth/complete-registration",
        json={"setup_token": setup_token, "name": name, "password": password},
    )
    return response.json()


def test_register_an_account(client: TestClient) -> None:
    response = client.post(
        "/v1/auth/register",
        json={"email": "new_user@example.org"},
    )
    assert response.status_code == 202
    assert response.json()["message"] == "Check your email to verify your account."


def test_verify_email(mocker: MockerFixture, client: TestClient) -> None:
    mock_send = mocker.patch("src.services.auth.send_email")
    _do_register(client)

    verify_url = mock_send.call_args.kwargs["data"]["verify_url"]
    token = verify_url.split("token=")[1]

    response = client.post("/v1/auth/verify-email", json={"token": token})
    assert response.status_code == 200
    assert response.json()["setup_token"]


def test_complete_registration(mocker: MockerFixture, client: TestClient) -> None:
    setup_token = _do_verify(mocker, client)
    response = client.post(
        "/v1/auth/complete-registration",
        json={"setup_token": setup_token, "name": "New User", "password": "password1"},
    )
    assert response.status_code == 201
    rs = response.json()
    assert rs["access_token"]
    assert rs["refresh_token"]
    assert rs["token_type"] == "bearer"


def test_registered_user_can_login(mocker: MockerFixture, client: TestClient) -> None:
    _do_complete(mocker, client, password="password1")
    response = client.post(
        "v1/auth/token",
        data={"username": "new_user@example.org", "password": "password1"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == 200
    assert response.json()["access_token"]


def test_registered_user_has_owner_role_with_all_permissions(
    mocker: MockerFixture, client: TestClient
) -> None:
    token_data = _do_complete(mocker, client, password="password1")
    access_token = token_data["access_token"]

    response = client.get(
        "/v1/users/me", headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 200
    rs = response.json()
    assert len(rs["roles"]) == 1
    assert rs["roles"][0]["name"] == "Owner"
    assert len(rs["roles"][0]["permissions"]) == len(list(Permission))


def test_registration_creates_default_roles(
    mocker: MockerFixture, client: TestClient
) -> None:
    token_data = _do_complete(mocker, client, password="password1")
    access_token = token_data["access_token"]

    response = client.get(
        "/v1/roles", headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 200
    roles = {r["name"]: r for r in response.json()["items"]}

    assert set(roles) == {"Owner", ADMIN_ROLE_NAME, MEMBER_ROLE_NAME}

    assert roles["Owner"]["is_protected"] is True
    assert len(roles["Owner"]["permissions"]) == len(list(Permission))

    _, _, admin_permissions = next(r for r in DEFAULT_ROLES if r[0] == ADMIN_ROLE_NAME)
    assert roles[ADMIN_ROLE_NAME]["is_protected"] is False
    assert {p["name"] for p in roles[ADMIN_ROLE_NAME]["permissions"]} == set(
        admin_permissions
    )

    _, _, member_permissions = next(
        r for r in DEFAULT_ROLES if r[0] == MEMBER_ROLE_NAME
    )
    assert roles[MEMBER_ROLE_NAME]["is_protected"] is False
    assert {p["name"] for p in roles[MEMBER_ROLE_NAME]["permissions"]} == set(
        member_permissions
    )


def test_cannot_verify_email_with_invalid_token(client: TestClient) -> None:
    response = client.post("/v1/auth/verify-email", json={"token": "invalidtoken"})
    assert response.status_code == 401
    assert response.json()["error_code"] == "signature_invalid"


def test_cannot_verify_email_token_twice(
    mocker: MockerFixture, client: TestClient
) -> None:
    mock_send = mocker.patch("src.services.auth.send_email")
    _do_register(client)
    token = mock_send.call_args.kwargs["data"]["verify_url"].split("token=")[1]

    client.post("/v1/auth/verify-email", json={"token": token})
    response = client.post("/v1/auth/verify-email", json={"token": token})
    assert response.status_code == 401
    assert response.json()["error_code"] == "token_invalid"


def test_cannot_complete_registration_with_invalid_setup_token(
    client: TestClient,
) -> None:
    response = client.post(
        "/v1/auth/complete-registration",
        json={"setup_token": "badtoken", "name": "X", "password": "password1"},
    )
    assert response.status_code == 401
    assert response.json()["error_code"] == "signature_invalid"


def test_get_access_token(client: TestClient) -> None:
    response = client.post(
        "v1/auth/token",
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
            "v1/auth/token",
            data={"username": "admin@example.org", "password": "password"},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        assert response.status_code == 200
        rs = response.json()
        old_access_token = rs["access_token"]
        old_refresh_token = rs["refresh_token"]

        response = client.get(
            "/v1/users/me", headers={"Authorization": f"Bearer {old_access_token}"}
        )
        assert response.status_code == 200

        time.sleep(2)

        response = client.get(
            "/v1/users/me", headers={"Authorization": f"Bearer {old_access_token}"}
        )
        assert response.status_code == 401

        response = client.post("v1/auth/refresh")
        assert response.status_code == 200
        rs = response.json()
        assert rs["token_type"] == "bearer"
        assert rs["access_token"] and rs["access_token"] != old_access_token
        assert rs["refresh_token"] and rs["refresh_token"] != old_refresh_token

        response = client.get(
            "/v1/users/me", headers={"Authorization": f"Bearer {rs['access_token']}"}
        )
        assert response.status_code == 200


def test_logout(client: TestClient) -> None:
    response = client.post(
        "v1/auth/token",
        data={"username": "admin@example.org", "password": "password"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == 200
    assert "refresh_token=" in response.headers["set-cookie"]

    response = client.post("v1/auth/logout")
    assert response.status_code == 204
    assert "refresh_token=" in dict(response.headers).get("set-cookie", "")


def test_request_password_reset(client: TestClient) -> None:
    response = client.post(
        "v1/auth/reset-password/request", json={"email": "admin@example.org"}
    )
    assert response.status_code == 202


def test_reset_password(mocker: MockerFixture, client: TestClient) -> None:
    mock_send = mocker.patch("src.services.auth.send_email")

    client.post("v1/auth/reset-password/request", json={"email": "admin@example.org"})

    mock_send.assert_called_once()

    token = mock_send.call_args.kwargs["data"]["reset_url"].split("token=")[1]

    response = client.post(
        "v1/auth/reset-password", json={"token": token, "password": "new password"}
    )
    assert response.status_code == 204

    response = client.post(
        "v1/auth/reset-password", json={"token": token, "password": "new password"}
    )
    assert response.status_code == 401
    rs = response.json()
    assert rs["error_code"] == "token_invalid"
    assert rs["msg"] == "Token invalid"

    response = client.post(
        "v1/auth/token",
        data={"username": "admin@example.org", "password": "new password"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == 200


def test_request_password_reset_with_non_existent_email(client: TestClient) -> None:
    response = client.post(
        "v1/auth/reset-password/request", json={"email": "non-existent@example.org"}
    )
    assert response.status_code == 202


def test_cannot_refresh_access_token_with_invalid_token(client: TestClient) -> None:
    response = client.post(
        "v1/auth/refresh",
        cookies={"refresh_token": "invalidtoken"},
    )
    assert response.status_code == 401
    rs = response.json()
    assert rs["error_code"] == "unauthorized"
    assert rs["msg"] == "Not authenticated"


def test_cannot_refresh_access_token_with_expired_token(client: TestClient) -> None:
    with patch("src.core.config.settings.auth_refresh_token_expiry", -1):
        response = client.post(
            "v1/auth/token",
            data={"username": "admin@example.org", "password": "password"},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        assert response.status_code == 200
        rs = response.json()

        response = client.post(
            "v1/auth/refresh", cookies={"refresh_token": rs["refresh_token"]}
        )
        assert response.status_code == 401
        rs = response.json()
        assert rs["error_code"] == "token_expired"
        assert rs["msg"] == "Token expired"


def test_cannot_reset_password_with_invalid_token(client: TestClient) -> None:
    response = client.post(
        "v1/auth/reset-password",
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
        client.post(
            "v1/auth/reset-password/request", json={"email": "admin@example.org"}
        )

        token = mock_send.call_args.kwargs["data"]["reset_url"].split("token=")[1]

        response = client.post(
            "v1/auth/reset-password", json={"token": token, "password": "new password"}
        )
        assert response.status_code == 401
        rs = response.json()
        assert rs["error_code"] == "signature_expired"
        assert rs["msg"] == "Signature expired"


def test_owner_cannot_register_a_new_account(
    client: TestClient,
) -> None:
    response = client.post(
        "/v1/auth/register",
        json={"email": "admin@example.org"},
    )
    assert response.status_code == 409
    rs = response.json()
    assert rs["error_code"] == "email_already_exists"
    assert rs["msg"] == "Account already exists. [email=admin@example.org]"


def test_existing_user_cannot_register_again(
    client: TestClient,
) -> None:
    response = client.post(
        "/v1/auth/register",
        json={"email": "standard@example.org"},
    )
    assert response.status_code == 409
    assert response.json()["error_code"] == "email_already_exists"


def test_cannot_get_access_token_with_wrong_credentials(client: TestClient) -> None:
    response = client.post(
        "v1/auth/token",
        data={"username": "no-user@example.org", "password": "password"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == 401
    rs = response.json()
    assert rs["error_code"] == "login_failed"
    assert rs["msg"] == "Not authenticated"


def test_get_access_token_sets_httponly_refresh_token_cookie(
    client: TestClient,
) -> None:
    response = client.post(
        "v1/auth/token",
        data={"username": "admin@example.org", "password": "password"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == 200
    cookie = response.headers.get("set-cookie", "")
    assert "refresh_token=" in cookie
    assert "HttpOnly" in cookie
    assert "Path=/v1/auth" in cookie


def test_cannot_refresh_without_cookie(client: TestClient) -> None:
    response = client.post(
        "v1/auth/refresh",
        cookies={"refresh_token": ""},
    )
    assert response.status_code == 401


def test_cannot_refresh_after_logout(client: TestClient) -> None:
    response = client.post(
        "v1/auth/token",
        data={"username": "admin@example.org", "password": "password"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == 200
    old_refresh_token = response.json()["refresh_token"]

    client.post("v1/auth/logout")

    client.cookies.set("refresh_token", old_refresh_token)
    response = client.post("v1/auth/refresh")
    assert response.status_code == 401


def test_cannot_reuse_refresh_token_after_rotation(client: TestClient) -> None:
    response = client.post(
        "v1/auth/token",
        data={"username": "admin@example.org", "password": "password"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == 200
    old_refresh_token = response.json()["refresh_token"]

    response = client.post("v1/auth/refresh")
    assert response.status_code == 200

    client.cookies.set("refresh_token", old_refresh_token)
    response = client.post("v1/auth/refresh")
    assert response.status_code == 401


def test_second_login_invalidates_previous_refresh_token(client: TestClient) -> None:
    response = client.post(
        "v1/auth/token",
        data={"username": "admin@example.org", "password": "password"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == 200
    first_refresh_token = response.json()["refresh_token"]

    client.post(
        "v1/auth/token",
        data={"username": "admin@example.org", "password": "password"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )

    client.cookies.set("refresh_token", first_refresh_token)
    response = client.post("v1/auth/refresh")
    assert response.status_code == 401


def test_register_rate_limit(client: TestClient) -> None:
    limiter._storage.reset()
    with patch.object(limiter, "enabled", True):
        for _ in range(5):
            client.post("/v1/auth/register", json={"email": "x@example.org"})
        response = client.post("/v1/auth/register", json={"email": "x@example.org"})
    assert response.status_code == 429


def test_token_rate_limit(client: TestClient) -> None:
    limiter._storage.reset()
    with patch.object(limiter, "enabled", True):
        for _ in range(10):
            client.post(
                "v1/auth/token",
                data={"username": "admin@example.org", "password": "wrong"},
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
        response = client.post(
            "v1/auth/token",
            data={"username": "admin@example.org", "password": "wrong"},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
    assert response.status_code == 429


def test_refresh_rate_limit(client: TestClient) -> None:
    limiter._storage.reset()
    with patch.object(limiter, "enabled", True):
        for _ in range(10):
            client.post("v1/auth/refresh", cookies={"refresh_token": "invalid"})
        response = client.post("v1/auth/refresh", cookies={"refresh_token": "invalid"})
    assert response.status_code == 429


def test_reset_password_request_rate_limit(client: TestClient) -> None:
    limiter._storage.reset()
    with patch.object(limiter, "enabled", True):
        for _ in range(5):
            client.post(
                "v1/auth/reset-password/request",
                json={"email": "nobody@example.org"},
            )
        response = client.post(
            "v1/auth/reset-password/request",
            json={"email": "nobody@example.org"},
        )
    assert response.status_code == 429


def test_reset_password_rate_limit(client: TestClient) -> None:
    limiter._storage.reset()
    with patch.object(limiter, "enabled", True):
        for _ in range(5):
            client.post(
                "v1/auth/reset-password",
                json={"token": "invalid", "password": "password1"},
            )
        response = client.post(
            "v1/auth/reset-password",
            json={"token": "invalid", "password": "password1"},
        )
    assert response.status_code == 429


# --- POST /auth/complete-invite ---


def _do_invite(
    mocker: MockerFixture,
    admin_client: TestClient,
    email: str = "invited@example.org",
) -> str:
    """Send an invite and return the raw invite token captured from the mocked email."""
    mock_send = mocker.patch("src.services.user.send_email")
    admin_client.post("/v1/users/invite", json={"email": email, "role_ids": []})
    invite_url = mock_send.call_args.kwargs["data"]["invite_url"]
    return invite_url.split("token=")[1]


def test_complete_invite(
    mocker: MockerFixture, admin_authenticated: TestClient, client: TestClient
) -> None:
    token = _do_invite(mocker, admin_authenticated)
    response = client.post(
        "/v1/auth/complete-invite",
        json={"invite_token": token, "name": "Invited User", "password": "password1"},
    )
    assert response.status_code == 201
    rs = response.json()
    assert rs["access_token"]
    assert rs["refresh_token"]
    assert rs["token_type"] == "bearer"


def test_invited_user_can_login(
    mocker: MockerFixture, admin_authenticated: TestClient, client: TestClient
) -> None:
    token = _do_invite(mocker, admin_authenticated)
    client.post(
        "/v1/auth/complete-invite",
        json={"invite_token": token, "name": "Invited User", "password": "securepass1"},
    )
    response = client.post(
        "/v1/auth/token",
        data={"username": "invited@example.org", "password": "securepass1"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == 200
    assert response.json()["access_token"]


def test_invited_user_is_added_to_organization_with_roles(
    mocker: MockerFixture, admin_authenticated: TestClient, client: TestClient
) -> None:
    mock_send = mocker.patch("src.services.user.send_email")
    admin_authenticated.post(
        "/v1/users/invite",
        json={"email": "invited@example.org", "role_ids": [2]},
    )
    token = mock_send.call_args.kwargs["data"]["invite_url"].split("token=")[1]

    rs = client.post(
        "/v1/auth/complete-invite",
        json={"invite_token": token, "name": "Invited User", "password": "password1"},
    ).json()

    profile = client.get(
        "/v1/users/me", headers={"Authorization": f"Bearer {rs['access_token']}"}
    ).json()
    assert profile["email"] == "invited@example.org"
    role_names = {r["name"] for r in profile["roles"]}
    assert "standard" in role_names


def test_cannot_complete_invite_with_invalid_token(client: TestClient) -> None:
    response = client.post(
        "/v1/auth/complete-invite",
        json={
            "invite_token": "notavalidtoken",
            "name": "User",
            "password": "password1",
        },
    )
    assert response.status_code == 401
    assert response.json()["error_code"] == "signature_invalid"


def test_cannot_complete_invite_with_expired_token(
    mocker: MockerFixture, admin_authenticated: TestClient, client: TestClient
) -> None:
    token = _do_invite(mocker, admin_authenticated)
    with patch("src.core.config.settings.invite_expiry", -1):
        response = client.post(
            "/v1/auth/complete-invite",
            json={"invite_token": token, "name": "User", "password": "password1"},
        )
    assert response.status_code == 401
    assert response.json()["error_code"] == "signature_expired"


def test_complete_invite_rate_limit(client: TestClient) -> None:
    limiter._storage.reset()
    with patch.object(limiter, "enabled", True):
        for _ in range(5):
            client.post(
                "/v1/auth/complete-invite",
                json={"invite_token": "x", "name": "User", "password": "password1"},
            )
        response = client.post(
            "/v1/auth/complete-invite",
            json={"invite_token": "x", "name": "User", "password": "password1"},
        )
    assert response.status_code == 429


# --- POST /auth/invite-status ---


def test_invite_status_valid_token(
    mocker: MockerFixture, admin_authenticated: TestClient, client: TestClient
) -> None:
    token = _do_invite(mocker, admin_authenticated)
    response = client.post("/v1/auth/invite-status", json={"token": token})
    assert response.status_code == 200
    rs = response.json()
    assert rs["email"] == "invited@example.org"
    assert rs["user_exists"] is False


def test_invite_status_existing_user(
    mocker: MockerFixture, admin_authenticated: TestClient, client: TestClient
) -> None:
    # admin2@example.org is in Org 2, not Org 1 - can be invited to Org 1
    token = _do_invite(mocker, admin_authenticated, email="admin2@example.org")
    response = client.post("/v1/auth/invite-status", json={"token": token})
    assert response.status_code == 200
    rs = response.json()
    assert rs["email"] == "admin2@example.org"
    assert rs["user_exists"] is True


def test_invite_status_invalid_token(client: TestClient) -> None:
    response = client.post("/v1/auth/invite-status", json={"token": "notavalidtoken"})
    assert response.status_code == 401
    assert response.json()["error_code"] == "signature_invalid"


def test_invite_status_expired_token(
    mocker: MockerFixture, admin_authenticated: TestClient, client: TestClient
) -> None:
    token = _do_invite(mocker, admin_authenticated)
    with patch("src.core.config.settings.invite_expiry", -1):
        response = client.post("/v1/auth/invite-status", json={"token": token})
    assert response.status_code == 401
    assert response.json()["error_code"] == "signature_expired"


# --- existing user invite flow ---


def test_complete_invite_existing_user(
    mocker: MockerFixture, admin_authenticated: TestClient, client: TestClient
) -> None:
    mocker.patch("src.services.auth.send_email")
    # admin2@example.org is in Org 2 - invite to Org 1 without name/password
    token = _do_invite(mocker, admin_authenticated, email="admin2@example.org")
    response = client.post(
        "/v1/auth/complete-invite",
        json={"invite_token": token},
    )
    assert response.status_code == 201
    rs = response.json()
    assert rs["access_token"]
    assert rs["refresh_token"]


def test_complete_invite_existing_user_is_added_to_org(
    mocker: MockerFixture, admin_authenticated: TestClient, client: TestClient
) -> None:
    mocker.patch("src.services.auth.send_email")
    token = _do_invite(mocker, admin_authenticated, email="admin2@example.org")
    rs = client.post(
        "/v1/auth/complete-invite",
        json={"invite_token": token},
    ).json()
    profile = client.get(
        "/v1/users/me", headers={"Authorization": f"Bearer {rs['access_token']}"}
    ).json()
    assert profile["email"] == "admin2@example.org"


def test_complete_invite_existing_user_sends_added_to_org_email(
    mocker: MockerFixture, admin_authenticated: TestClient, client: TestClient
) -> None:
    mock_send = mocker.patch("src.services.auth.send_email")
    token = _do_invite(mocker, admin_authenticated, email="admin2@example.org")
    client.post("/v1/auth/complete-invite", json={"invite_token": token})
    mock_send.assert_called_once()
    assert mock_send.call_args.kwargs["email_template"] == "added-to-org"


def test_cannot_invite_user_already_in_org(
    mocker: MockerFixture, admin_authenticated: TestClient
) -> None:
    # Accept first invite, then verify re-invite is blocked via invite_user
    mocker.patch("src.services.auth.send_email")
    token = _do_invite(mocker, admin_authenticated, email="admin2@example.org")
    admin_authenticated.post("/v1/auth/complete-invite", json={"invite_token": token})

    # Now admin2 is in Org 1 - invite_user should block a second invite
    mocker.patch("src.services.user.send_email")
    response = admin_authenticated.post(
        "/v1/users/invite",
        json={"email": "admin2@example.org", "role_ids": []},
    )
    assert response.status_code == 409
    assert response.json()["error_code"] == "email_already_exists"


def test_complete_invite_new_user_missing_name_or_password(
    mocker: MockerFixture, admin_authenticated: TestClient, client: TestClient
) -> None:
    token = _do_invite(mocker, admin_authenticated)
    response = client.post(
        "/v1/auth/complete-invite",
        json={"invite_token": token},
    )
    assert response.status_code == 422
