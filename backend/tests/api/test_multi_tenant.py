"""Tests for multi-tenant user membership features:
- POST /auth/switch-tenant
- GET  /tenants
- POST /tenants/{tenant_id}/users/{user_id}
- DELETE /tenants/{tenant_id}/users/{user_id}
- GET  /tenants/{tenant_id}/users
- Login auto-selects most-recently-active tenant
"""

from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _login(client: TestClient, email: str, password: str = "password") -> str:
    rs = client.post(
        "/v1/auth/token",
        data={"username": email, "password": password},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert rs.status_code == 200, rs.json()
    return rs.json()["access_token"]


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# GET /tenants
# ---------------------------------------------------------------------------


def test_get_my_tenants_returns_own_tenant(admin_authenticated: TestClient) -> None:
    response = admin_authenticated.get("/v1/tenants")
    assert response.status_code == 200
    tenants = response.json()
    assert len(tenants) == 1
    assert tenants[0]["id"] == 1
    assert tenants[0]["name"] == "Tenant 1"


def test_get_my_tenants_after_joining_second_tenant(
    admin_authenticated: TestClient,
    tenant2_admin_authenticated: TestClient,
) -> None:
    # admin2 (Tenant 2) adds admin (user 1) to Tenant 2
    response = tenant2_admin_authenticated.post("/v1/tenants/2/users/1")
    assert response.status_code == 204

    response = admin_authenticated.get("/v1/tenants")
    assert response.status_code == 200
    tenants = response.json()
    assert len(tenants) == 2
    tenant_ids = {t["id"] for t in tenants}
    assert {1, 2} == tenant_ids


def test_get_my_tenants_unauthenticated(client: TestClient) -> None:
    response = client.get("/v1/tenants")
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# POST /tenants/{tenant_id}/users/{user_id}
# ---------------------------------------------------------------------------


def test_add_user_to_tenant(
    tenant2_admin_authenticated: TestClient,
) -> None:
    # admin2 (active in Tenant 2) adds user 1 (admin@example.org) to Tenant 2
    response = tenant2_admin_authenticated.post("/v1/tenants/2/users/1")
    assert response.status_code == 204


def test_cannot_add_user_to_tenant_you_are_not_active_in(
    admin_authenticated: TestClient,
) -> None:
    # admin is active in Tenant 1; they cannot add users to Tenant 2
    response = admin_authenticated.post("/v1/tenants/2/users/4")
    assert response.status_code == 403


def test_cannot_add_nonexistent_user_to_tenant(
    tenant2_admin_authenticated: TestClient,
) -> None:
    response = tenant2_admin_authenticated.post("/v1/tenants/2/users/9999")
    assert response.status_code == 404


def test_cannot_add_user_already_in_tenant(
    admin_authenticated: TestClient,
) -> None:
    # user 2 (standard) is already in Tenant 1
    response = admin_authenticated.post("/v1/tenants/1/users/2")
    assert response.status_code == 409


def test_cannot_add_user_to_tenant_without_permission(
    standard_authenticated: TestClient,
) -> None:
    # standard user lacks MANAGE_TENANT_USER permission
    response = standard_authenticated.post("/v1/tenants/1/users/4")
    assert response.status_code == 403


def test_cannot_add_user_to_tenant_unauthenticated(client: TestClient) -> None:
    response = client.post("/v1/tenants/1/users/2")
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# DELETE /tenants/{tenant_id}/users/{user_id}
# ---------------------------------------------------------------------------


def test_remove_user_from_tenant(
    admin_authenticated: TestClient,
) -> None:
    # admin removes user 3 (no_roles) from Tenant 1
    response = admin_authenticated.delete("/v1/tenants/1/users/3")
    assert response.status_code == 204

    # user 3 should no longer appear in Tenant 1 users
    response = admin_authenticated.get("/v1/tenants/1/users")
    assert response.status_code == 200
    user_ids = [u["id"] for u in response.json()["items"]]
    assert 3 not in user_ids


def test_cannot_remove_user_from_tenant_you_are_not_active_in(
    admin_authenticated: TestClient,
) -> None:
    # admin is active in Tenant 1; cannot remove from Tenant 2
    response = admin_authenticated.delete("/v1/tenants/2/users/4")
    assert response.status_code == 403


def test_cannot_remove_nonmember_from_tenant(
    tenant2_admin_authenticated: TestClient,
) -> None:
    # user 2 (standard) is not in Tenant 2
    response = tenant2_admin_authenticated.delete("/v1/tenants/2/users/2")
    assert response.status_code == 404


def test_cannot_remove_last_admin_from_tenant(
    admin_authenticated: TestClient,
) -> None:
    # user 1 is the only user with MANAGE_USER_ROLE in Tenant 1
    response = admin_authenticated.delete("/v1/tenants/1/users/1")
    assert response.status_code == 403
    assert "role management access" in response.json()["msg"]


def test_cannot_remove_user_without_permission(
    standard_authenticated: TestClient,
) -> None:
    response = standard_authenticated.delete("/v1/tenants/1/users/3")
    assert response.status_code == 403


# ---------------------------------------------------------------------------
# GET /tenants/{tenant_id}/users
# ---------------------------------------------------------------------------


def test_get_tenant_users(admin_authenticated: TestClient) -> None:
    response = admin_authenticated.get("/v1/tenants/1/users")
    assert response.status_code == 200
    rs = response.json()
    assert rs["total"] == 3  # admin, standard, no_roles
    emails = {u["email"] for u in rs["items"]}
    assert "admin@example.org" in emails
    assert "standard@example.org" in emails
    assert "no_roles@example.org" in emails


def test_get_tenant_users_shows_only_tenant_roles(
    admin_authenticated: TestClient,
    tenant2_admin_authenticated: TestClient,
) -> None:
    # Add admin (user 1) to Tenant 2 with no roles there
    tenant2_admin_authenticated.post("/v1/tenants/2/users/1")

    # When Tenant 1 lists its users, admin's roles should be Tenant 1 roles only
    response = admin_authenticated.get("/v1/tenants/1/users")
    assert response.status_code == 200
    admin_user = next(u for u in response.json()["items"] if u["email"] == "admin@example.org")
    for role in admin_user["roles"]:
        assert role["tenant_id"] == 1


def test_cannot_get_users_of_other_tenant(
    admin_authenticated: TestClient,
) -> None:
    response = admin_authenticated.get("/v1/tenants/2/users")
    assert response.status_code == 403


def test_cannot_get_tenant_users_without_read_user_permission(
    client: TestClient,
) -> None:
    # no_roles user has no permissions at all
    token = _login(client, "no_roles@example.org")
    response = client.get("/v1/tenants/1/users", headers=_auth_headers(token))
    assert response.status_code == 403


# ---------------------------------------------------------------------------
# POST /auth/switch-tenant
# ---------------------------------------------------------------------------


def test_switch_tenant(
    client: TestClient,
    tenant2_admin_authenticated: TestClient,
) -> None:
    # Add admin (user 1) to Tenant 2
    tenant2_admin_authenticated.post("/v1/tenants/2/users/1")

    # Login as admin (currently active in Tenant 1)
    token = _login(client, "admin@example.org")

    # Switch to Tenant 2
    response = client.post(
        "/v1/auth/switch-tenant",
        json={"tenant_id": 2},
        headers=_auth_headers(token),
    )
    assert response.status_code == 200
    new_token = response.json()["access_token"]
    assert new_token
    assert new_token != token


def test_switch_tenant_context_changes(
    client: TestClient,
    tenant2_admin_authenticated: TestClient,
) -> None:
    # Add admin (user 1) to Tenant 2 (no roles assigned there)
    tenant2_admin_authenticated.post("/v1/tenants/2/users/1")

    token = _login(client, "admin@example.org")

    # Active in Tenant 1 - /users/me shows Admin role
    me_t1 = client.get("/v1/users/me", headers=_auth_headers(token)).json()
    assert len(me_t1["roles"]) == 1
    assert me_t1["roles"][0]["name"] == "Owner"

    # Switch to Tenant 2
    switch_rs = client.post(
        "/v1/auth/switch-tenant",
        json={"tenant_id": 2},
        headers=_auth_headers(token),
    )
    new_token = switch_rs.json()["access_token"]

    # Active in Tenant 2 - no roles there, so /users/me shows empty roles
    me_t2 = client.get("/v1/users/me", headers=_auth_headers(new_token)).json()
    assert me_t2["roles"] == []


def test_cannot_switch_to_tenant_not_a_member_of(
    admin_authenticated: TestClient,
) -> None:
    response = admin_authenticated.post("/v1/auth/switch-tenant", json={"tenant_id": 2})
    assert response.status_code == 403


def test_switch_tenant_requires_auth(client: TestClient) -> None:
    response = client.post("/v1/auth/switch-tenant", json={"tenant_id": 1})
    assert response.status_code == 401


def test_switch_tenant_sets_refresh_token_cookie(
    client: TestClient,
    tenant2_admin_authenticated: TestClient,
) -> None:
    tenant2_admin_authenticated.post("/v1/tenants/2/users/1")
    token = _login(client, "admin@example.org")

    response = client.post(
        "/v1/auth/switch-tenant",
        json={"tenant_id": 2},
        headers=_auth_headers(token),
    )
    assert response.status_code == 200
    assert "refresh_token=" in response.headers.get("set-cookie", "")


def test_switch_tenant_rotates_refresh_token(
    client: TestClient,
    tenant2_admin_authenticated: TestClient,
) -> None:
    tenant2_admin_authenticated.post("/v1/tenants/2/users/1")

    # Login to get initial tokens
    login_rs = client.post(
        "/v1/auth/token",
        data={"username": "admin@example.org", "password": "password"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    old_refresh = login_rs.json()["refresh_token"]
    access_token = login_rs.json()["access_token"]

    # Switch tenant
    client.post(
        "/v1/auth/switch-tenant",
        json={"tenant_id": 2},
        headers=_auth_headers(access_token),
    )

    # Old refresh token must no longer work
    client.cookies.set("refresh_token", old_refresh)
    response = client.post("/v1/auth/refresh")
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# Login auto-selects most-recently-active tenant
# ---------------------------------------------------------------------------


def test_login_auto_selects_most_recently_active_tenant(
    client: TestClient,
    tenant2_admin_authenticated: TestClient,
) -> None:
    # Add admin to Tenant 2 (no roles there)
    tenant2_admin_authenticated.post("/v1/tenants/2/users/1")

    # Login and switch to Tenant 2 (updates last_active_at for Tenant 2)
    first_token = _login(client, "admin@example.org")
    switch_rs = client.post(
        "/v1/auth/switch-tenant",
        json={"tenant_id": 2},
        headers=_auth_headers(first_token),
    )
    assert switch_rs.status_code == 200

    # Re-login: should auto-select Tenant 2 (most recently active)
    # Tenant 2 has no roles for admin, so /users/me should return empty roles
    new_token = _login(client, "admin@example.org")
    me = client.get("/v1/users/me", headers=_auth_headers(new_token)).json()
    assert me["roles"] == []


def test_login_selects_first_tenant_when_none_active(
    client: TestClient,
) -> None:
    # admin@example.org only belongs to Tenant 1 with last_active_at set from seeding
    token = _login(client, "admin@example.org")
    response = client.get("/v1/tenants", headers=_auth_headers(token))
    assert response.status_code == 200
    rs = response.json()
    assert len(rs) == 1
    assert rs[0]["name"] == "Tenant 1"


# ---------------------------------------------------------------------------
# Roles are isolated per tenant
# ---------------------------------------------------------------------------


def test_roles_shown_are_scoped_to_active_tenant(
    client: TestClient,
    tenant2_admin_authenticated: TestClient,
) -> None:
    # Add admin (user 1) to Tenant 2
    tenant2_admin_authenticated.post("/v1/tenants/2/users/1")

    # While active in Tenant 1, /users/me shows Tenant 1 roles
    token_t1 = _login(client, "admin@example.org")
    me_t1 = client.get("/v1/users/me", headers=_auth_headers(token_t1)).json()
    assert all(r["tenant_id"] == 1 for r in me_t1["roles"])

    # After switching to Tenant 2, /users/me shows no roles (none assigned there)
    switch_rs = client.post(
        "/v1/auth/switch-tenant",
        json={"tenant_id": 2},
        headers=_auth_headers(token_t1),
    )
    token_t2 = switch_rs.json()["access_token"]
    me_t2 = client.get("/v1/users/me", headers=_auth_headers(token_t2)).json()
    assert me_t2["roles"] == []
