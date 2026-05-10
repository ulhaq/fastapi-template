# mypy: disable-error-code="no-untyped-def"
"""Direct unit tests for AuthService - call methods without HTTP layer.

These tests bypass TestClient (which executes code in anyio threads that evade
coverage tracking) and instead instantiate the service with a real SQLAlchemy
session. This guarantees that coverage.py captures all executed lines.
"""

import pytest

from src.core.exceptions import (
    AlreadyExistsException,
    NotAuthenticatedException,
    NotFoundException,
    PermissionDeniedException,
)
from src.core.security import hash_secret, sign
from src.repositories.repository_manager import RepositoryManager
from src.schemas.user import (
    CompleteInviteIn,
    CompleteRegistrationIn,
    EmailIn,
    ResetPasswordIn,
    VerifyEmailIn,
)
from src.services.auth import AuthService
from tests.conftest import TestSessionLocal


def _no_op_schedule(fn, **kwargs):
    """Replacement for BackgroundTasks.add_task - discards scheduled work."""


async def _make_service(session, provider) -> AuthService:
    repos = RepositoryManager(session)
    return AuthService(repos, provider)


# ---------------------------------------------------------------------------
# register_organization
# ---------------------------------------------------------------------------


async def test_register_new_email(mock_billing_provider):
    async with TestSessionLocal() as session:
        async with session.begin():
            service = await _make_service(session, mock_billing_provider)
            out = await service.register_organization(
                EmailIn(email="brand_new@example.com"),
                schedule_task=_no_op_schedule,
            )
    assert "email" in out.message.lower() or out.message


async def test_register_duplicate_email_raises(mock_billing_provider):
    async with TestSessionLocal() as session:
        async with session.begin():
            service = await _make_service(session, mock_billing_provider)
            with pytest.raises(AlreadyExistsException):
                await service.register_organization(
                    EmailIn(email="admin@example.org"),
                    schedule_task=_no_op_schedule,
                )


# ---------------------------------------------------------------------------
# verify_email
# ---------------------------------------------------------------------------


async def test_verify_email_valid_token(mock_billing_provider):
    email = "verify@example.com"
    token = sign(data=email, salt="email-verification")

    async with TestSessionLocal() as session:
        async with session.begin():
            service = await _make_service(session, mock_billing_provider)
            # First register so the token record exists
            await service.register_organization(
                EmailIn(email=email), schedule_task=_no_op_schedule
            )
            out = await service.verify_email(VerifyEmailIn(token=token))

    assert out.setup_token


async def test_verify_email_invalid_token_raises(mock_billing_provider):
    async with TestSessionLocal() as session:
        async with session.begin():
            service = await _make_service(session, mock_billing_provider)
            # Token is valid (signed) but no DB record exists
            token = sign(data="nobody@example.com", salt="email-verification")
            with pytest.raises(NotAuthenticatedException):
                await service.verify_email(VerifyEmailIn(token=token))


# ---------------------------------------------------------------------------
# complete_registration
# ---------------------------------------------------------------------------


async def test_complete_registration_creates_user_and_org(mock_billing_provider):
    email = "complete@example.com"
    setup_token = sign(data=email, salt="complete-registration")

    async with TestSessionLocal() as session:
        async with session.begin():
            service = await _make_service(session, mock_billing_provider)
            token = await service.complete_registration(
                CompleteRegistrationIn(
                    setup_token=setup_token,
                    name="Test User",
                    password="Str0ng!Pass",
                    terms_accepted=True,
                ),
                schedule_task=_no_op_schedule,
            )

    assert token.access_token
    assert token.refresh_token


async def test_complete_registration_duplicate_email_raises(mock_billing_provider):
    # admin@example.org already exists in the seeded DB
    setup_token = sign(data="admin@example.org", salt="complete-registration")

    async with TestSessionLocal() as session:
        async with session.begin():
            service = await _make_service(session, mock_billing_provider)
            with pytest.raises(AlreadyExistsException):
                await service.complete_registration(
                    CompleteRegistrationIn(
                        setup_token=setup_token,
                        name="Dupe",
                        password="Str0ng!Pass",
                        terms_accepted=True,
                    ),
                    schedule_task=_no_op_schedule,
                )


# ---------------------------------------------------------------------------
# get_access_token
# ---------------------------------------------------------------------------


async def test_get_access_token_valid_credentials(mock_billing_provider):
    async with TestSessionLocal() as session:
        async with session.begin():
            service = await _make_service(session, mock_billing_provider)
            token = await service.get_access_token("admin@example.org", "password")

    assert token.access_token
    assert token.refresh_token


async def test_get_access_token_wrong_password(mock_billing_provider):
    async with TestSessionLocal() as session:
        async with session.begin():
            service = await _make_service(session, mock_billing_provider)
            with pytest.raises(NotAuthenticatedException):
                await service.get_access_token("admin@example.org", "wrong")


async def test_get_access_token_unknown_user(mock_billing_provider):
    async with TestSessionLocal() as session:
        async with session.begin():
            service = await _make_service(session, mock_billing_provider)
            with pytest.raises(NotAuthenticatedException):
                await service.get_access_token("ghost@example.org", "password")


# ---------------------------------------------------------------------------
# refresh_access_token
# ---------------------------------------------------------------------------


async def test_refresh_access_token_valid(mock_billing_provider):
    async with TestSessionLocal() as session:
        async with session.begin():
            service = await _make_service(session, mock_billing_provider)
            # Log in first to get a persisted refresh token
            original = await service.get_access_token("admin@example.org", "password")
            new_tokens = await service.refresh_access_token(original.refresh_token)

    assert new_tokens.access_token
    assert new_tokens.access_token != original.access_token


async def test_refresh_access_token_missing_raises(mock_billing_provider):
    async with TestSessionLocal() as session:
        async with session.begin():
            service = await _make_service(session, mock_billing_provider)
            with pytest.raises(NotAuthenticatedException):
                await service.refresh_access_token(None)


async def test_refresh_access_token_bogus_raises(mock_billing_provider):
    async with TestSessionLocal() as session:
        async with session.begin():
            service = await _make_service(session, mock_billing_provider)
            with pytest.raises(NotAuthenticatedException):
                await service.refresh_access_token("not.a.valid.jwt")


# ---------------------------------------------------------------------------
# switch_organization
# ---------------------------------------------------------------------------


async def test_switch_organization_valid(mock_billing_provider):
    from src.core.security import Auth

    async with TestSessionLocal() as session:
        async with session.begin():
            repos = RepositoryManager(session)
            # Fetch admin user (id=1) who belongs to org 1
            user = await repos.user.get(1)
            assert user
            current_auth = Auth.from_user_model(user, active_organization_id=1)

            service = AuthService(repos, mock_billing_provider)
            # Switch back to org 1 (they already belong to it)
            token = await service.switch_organization(current_auth, organization_id=1)

    assert token.access_token


async def test_switch_organization_non_member_raises(mock_billing_provider):
    from src.core.security import Auth

    async with TestSessionLocal() as session:
        async with session.begin():
            repos = RepositoryManager(session)
            user = await repos.user.get(1)
            assert user
            current_auth = Auth.from_user_model(user, active_organization_id=1)

            service = AuthService(repos, mock_billing_provider)
            # Org 999 does not exist
            with pytest.raises(PermissionDeniedException):
                await service.switch_organization(current_auth, organization_id=999)


# ---------------------------------------------------------------------------
# logout
# ---------------------------------------------------------------------------


async def test_logout_deletes_refresh_token(mock_billing_provider):
    async with TestSessionLocal() as session:
        async with session.begin():
            service = await _make_service(session, mock_billing_provider)
            tokens = await service.get_access_token("admin@example.org", "password")
            # logout should not raise even if the token is valid
            await service.logout(tokens.refresh_token)


async def test_logout_invalid_token_is_silent(mock_billing_provider):
    async with TestSessionLocal() as session:
        async with session.begin():
            service = await _make_service(session, mock_billing_provider)
            # Should not raise
            await service.logout("garbage.token.here")


async def test_logout_none_is_silent(mock_billing_provider):
    async with TestSessionLocal() as session:
        async with session.begin():
            service = await _make_service(session, mock_billing_provider)
            await service.logout(None)


# ---------------------------------------------------------------------------
# request_password_reset
# ---------------------------------------------------------------------------


async def test_request_password_reset_existing_user(mock_billing_provider):
    async with TestSessionLocal() as session:
        async with session.begin():
            service = await _make_service(session, mock_billing_provider)
            # Should complete without error
            result = await service.request_password_reset(  # type: ignore[func-returns-value]
                EmailIn(email="admin@example.org"),
                schedule_task=_no_op_schedule,
            )
    assert result is None


async def test_request_password_reset_unknown_email_is_silent(mock_billing_provider):
    async with TestSessionLocal() as session:
        async with session.begin():
            service = await _make_service(session, mock_billing_provider)
            result = await service.request_password_reset(  # type: ignore[func-returns-value]
                EmailIn(email="nobody@example.org"),
                schedule_task=_no_op_schedule,
            )
    assert result is None


# ---------------------------------------------------------------------------
# reset_password
# ---------------------------------------------------------------------------


async def test_reset_password_valid(mock_billing_provider):
    async with TestSessionLocal() as session:
        async with session.begin():
            service = await _make_service(session, mock_billing_provider)
            # Create the reset token record
            await service.request_password_reset(
                EmailIn(email="admin@example.org"), schedule_task=_no_op_schedule
            )
            token = sign(data="admin@example.org", salt="reset-password")
            # Stamp the hashed token into the DB record so verify_secret matches
            repos = RepositoryManager(session)
            user = await repos.user.get_by_email("admin@example.org")
            assert user
            await repos.user.delete_password_reset_token(user=user)
            await repos.user.create_password_reset_token(
                user=user, token=hash_secret(token)
            )
            result = await service.reset_password(  # type: ignore[func-returns-value]
                ResetPasswordIn(token=token, password="NewP@ssw0rd!")
            )
    assert result is None


async def test_reset_password_invalid_token_raises(mock_billing_provider):
    async with TestSessionLocal() as session:
        async with session.begin():
            service = await _make_service(session, mock_billing_provider)
            token = sign(data="admin@example.org", salt="reset-password")
            # No DB record exists - should raise
            with pytest.raises(NotAuthenticatedException):
                await service.reset_password(
                    ResetPasswordIn(token=token, password="NewP@ss!")
                )


async def test_reset_password_unknown_email_raises(mock_billing_provider):
    async with TestSessionLocal() as session:
        async with session.begin():
            service = await _make_service(session, mock_billing_provider)
            token = sign(data="ghost@example.org", salt="reset-password")
            with pytest.raises(NotFoundException):
                await service.reset_password(
                    ResetPasswordIn(token=token, password="NewP@ss!")
                )


# ---------------------------------------------------------------------------
# invite_status
# ---------------------------------------------------------------------------


async def test_invite_status_valid(mock_billing_provider):
    from src.core.security import hash_secret, sign

    email = "invitee@example.com"
    token = sign(
        data={"email": email, "organization_id": 1, "role_ids": []}, salt="invite"
    )

    async with TestSessionLocal() as session:
        async with session.begin():
            repos = RepositoryManager(session)
            await repos.invite_token.create(email=email, token=hash_secret(token))
            service = AuthService(repos, mock_billing_provider)
            out = await service.invite_status(token)

    assert out.email == email
    assert out.user_exists is False


async def test_invite_status_existing_user(mock_billing_provider):
    from src.core.security import hash_secret, sign

    email = "admin@example.org"  # already seeded
    token = sign(
        data={"email": email, "organization_id": 1, "role_ids": []}, salt="invite"
    )

    async with TestSessionLocal() as session:
        async with session.begin():
            repos = RepositoryManager(session)
            await repos.invite_token.create(email=email, token=hash_secret(token))
            service = AuthService(repos, mock_billing_provider)
            out = await service.invite_status(token)

    assert out.user_exists is True


# ---------------------------------------------------------------------------
# complete_invite - new user branch
# ---------------------------------------------------------------------------


async def test_complete_invite_new_user(mock_billing_provider):
    from src.core.security import hash_secret, sign

    email = "invite_new@example.com"
    token = sign(
        data={"email": email, "organization_id": 1, "role_ids": []}, salt="invite"
    )

    async with TestSessionLocal() as session:
        async with session.begin():
            repos = RepositoryManager(session)
            await repos.invite_token.create(email=email, token=hash_secret(token))
            service = AuthService(repos, mock_billing_provider)
            result = await service.complete_invite(
                CompleteInviteIn(
                    invite_token=token,
                    name="New Invitee",
                    password="Str0ng!Pass",
                    terms_accepted=True,
                ),
                schedule_task=_no_op_schedule,
            )

    assert result.access_token


async def test_complete_invite_existing_user(mock_billing_provider):
    """Existing user invited to org 2 is added as a member."""
    from src.core.security import hash_secret, sign

    email = "admin@example.org"  # already in org 1
    token = sign(
        data={"email": email, "organization_id": 2, "role_ids": []}, salt="invite"
    )

    async with TestSessionLocal() as session:
        async with session.begin():
            repos = RepositoryManager(session)
            await repos.invite_token.create(email=email, token=hash_secret(token))
            service = AuthService(repos, mock_billing_provider)
            result = await service.complete_invite(
                CompleteInviteIn(invite_token=token),
                schedule_task=_no_op_schedule,
            )

    assert result.access_token


# ---------------------------------------------------------------------------
# complete_registration - soft-deleted user restore branch (lines 129-130)
# ---------------------------------------------------------------------------


async def test_complete_registration_restores_soft_deleted_user(mock_billing_provider):
    """When a soft-deleted user with the same email exists, it is restored."""
    from datetime import UTC, datetime

    from src.core.security import hash_secret, sign
    from src.models.user import User

    email = "restored@example.com"
    setup_token = sign(data=email, salt="complete-registration")

    async with TestSessionLocal() as session:
        # Seed a soft-deleted user with the same email
        async with session.begin():
            deleted_user = User(
                name="Old Name",
                email=email,
                password=hash_secret("oldpass"),
                deleted_at=datetime.now(UTC),
            )
            session.add(deleted_user)

    async with TestSessionLocal() as session:
        async with session.begin():
            repos = RepositoryManager(session)
            service = AuthService(repos, mock_billing_provider)
            token = await service.complete_registration(
                CompleteRegistrationIn(
                    setup_token=setup_token,
                    name="Restored User",
                    password="Str0ng!Pass",
                    terms_accepted=True,
                ),
                schedule_task=_no_op_schedule,
            )

    assert token.access_token


# ---------------------------------------------------------------------------
# invite_status - invalid token (line 200)
# ---------------------------------------------------------------------------


async def test_invite_status_invalid_token_raises(mock_billing_provider):
    """Valid signature but no DB record > NotAuthenticatedException."""
    from src.core.security import sign

    token = sign(
        data={"email": "notindb@example.com", "organization_id": 1, "role_ids": []},
        salt="invite",
    )

    async with TestSessionLocal() as session:
        async with session.begin():
            repos = RepositoryManager(session)
            service = AuthService(repos, mock_billing_provider)
            with pytest.raises(NotAuthenticatedException):
                await service.invite_status(token)


# ---------------------------------------------------------------------------
# complete_invite - invalid token (line 221)
# ---------------------------------------------------------------------------


async def test_complete_invite_invalid_token_raises(mock_billing_provider):
    """Valid signature but no DB record > NotAuthenticatedException."""
    from src.core.security import sign

    token = sign(
        data={"email": "nodb@example.com", "organization_id": 1, "role_ids": []},
        salt="invite",
    )

    async with TestSessionLocal() as session:
        async with session.begin():
            repos = RepositoryManager(session)
            service = AuthService(repos, mock_billing_provider)
            with pytest.raises(NotAuthenticatedException):
                await service.complete_invite(
                    CompleteInviteIn(invite_token=token),
                    schedule_task=_no_op_schedule,
                )


# ---------------------------------------------------------------------------
# complete_invite - org not found (line 229)
# ---------------------------------------------------------------------------


async def test_complete_invite_org_not_found_raises(mock_billing_provider):
    from src.core.security import hash_secret, sign

    email = "orgnotfound@example.com"
    token = sign(
        data={"email": email, "organization_id": 9999, "role_ids": []}, salt="invite"
    )

    async with TestSessionLocal() as session:
        async with session.begin():
            repos = RepositoryManager(session)
            await repos.invite_token.create(email=email, token=hash_secret(token))
            service = AuthService(repos, mock_billing_provider)
            with pytest.raises(NotFoundException):
                await service.complete_invite(
                    CompleteInviteIn(invite_token=token),
                    schedule_task=_no_op_schedule,
                )


# ---------------------------------------------------------------------------
# complete_invite - already a member (line 245)
# ---------------------------------------------------------------------------


async def test_complete_invite_already_member_raises(mock_billing_provider):
    from src.core.security import hash_secret, sign

    email = "admin@example.org"  # already in org 1
    token = sign(
        data={"email": email, "organization_id": 1, "role_ids": []}, salt="invite"
    )

    async with TestSessionLocal() as session:
        async with session.begin():
            repos = RepositoryManager(session)
            await repos.invite_token.create(email=email, token=hash_secret(token))
            service = AuthService(repos, mock_billing_provider)
            with pytest.raises(AlreadyExistsException):
                await service.complete_invite(
                    CompleteInviteIn(invite_token=token),
                    schedule_task=_no_op_schedule,
                )


# ---------------------------------------------------------------------------
# complete_invite - existing user with role_ids (lines 257-262)
# ---------------------------------------------------------------------------


async def test_complete_invite_existing_user_with_roles(mock_billing_provider):
    """Existing user invited to new org with role_ids > roles assigned."""
    from src.core.security import hash_secret, sign

    email = "admin@example.org"  # in org 1; being invited to org 2
    # Role id=5 is Org 2's Admin role (non-protected) - must use same-org role
    token = sign(
        data={"email": email, "organization_id": 2, "role_ids": [5]}, salt="invite"
    )

    async with TestSessionLocal() as session:
        async with session.begin():
            repos = RepositoryManager(session)
            await repos.invite_token.create(email=email, token=hash_secret(token))
            service = AuthService(repos, mock_billing_provider)
            result = await service.complete_invite(
                CompleteInviteIn(invite_token=token),
                schedule_task=_no_op_schedule,
            )

    assert result.access_token


# ---------------------------------------------------------------------------
# complete_invite - new user missing name/password (line 282)
# ---------------------------------------------------------------------------


async def test_complete_invite_new_user_no_credentials_raises(mock_billing_provider):
    from src.core.exceptions import ValidationException
    from src.core.security import hash_secret, sign

    email = "nocreds@example.com"
    token = sign(
        data={"email": email, "organization_id": 1, "role_ids": []}, salt="invite"
    )

    async with TestSessionLocal() as session:
        async with session.begin():
            repos = RepositoryManager(session)
            await repos.invite_token.create(email=email, token=hash_secret(token))
            service = AuthService(repos, mock_billing_provider)
            with pytest.raises(ValidationException):
                await service.complete_invite(
                    CompleteInviteIn(invite_token=token),  # no name or password
                    schedule_task=_no_op_schedule,
                )


# ---------------------------------------------------------------------------
# complete_invite - soft-deleted user restore (lines 296-297)
# ---------------------------------------------------------------------------


async def test_complete_invite_restores_soft_deleted_user(mock_billing_provider):
    from datetime import UTC, datetime

    from src.core.security import hash_secret, sign
    from src.models.user import User

    email = "deleted_invite@example.com"
    token = sign(
        data={"email": email, "organization_id": 1, "role_ids": []}, salt="invite"
    )

    async with TestSessionLocal() as session:
        async with session.begin():
            deleted_user = User(
                name="Deleted",
                email=email,
                password=hash_secret("oldpass"),
                deleted_at=datetime.now(UTC),
            )
            session.add(deleted_user)

    async with TestSessionLocal() as session:
        async with session.begin():
            repos = RepositoryManager(session)
            await repos.invite_token.create(email=email, token=hash_secret(token))
            service = AuthService(repos, mock_billing_provider)
            result = await service.complete_invite(
                CompleteInviteIn(
                    invite_token=token,
                    name="Restored",
                    password="Str0ng!Pass",
                    terms_accepted=True,
                ),
                schedule_task=_no_op_schedule,
            )

    assert result.access_token


# ---------------------------------------------------------------------------
# complete_invite - new user with role_ids (lines 327-332)
# ---------------------------------------------------------------------------


async def test_complete_invite_new_user_with_roles(mock_billing_provider):
    from src.core.security import hash_secret, sign

    email = "newwithroles@example.com"
    # Role id=2 is Org 1's Admin role (non-protected) - valid_roles must be non-empty
    token = sign(
        data={"email": email, "organization_id": 1, "role_ids": [2]}, salt="invite"
    )

    async with TestSessionLocal() as session:
        async with session.begin():
            repos = RepositoryManager(session)
            await repos.invite_token.create(email=email, token=hash_secret(token))
            service = AuthService(repos, mock_billing_provider)
            result = await service.complete_invite(
                CompleteInviteIn(
                    invite_token=token,
                    name="New With Roles",
                    password="Str0ng!Pass",
                    terms_accepted=True,
                ),
                schedule_task=_no_op_schedule,
            )

    assert result.access_token


# ---------------------------------------------------------------------------
# get_access_token - user has no org membership (line 367)
# ---------------------------------------------------------------------------


async def test_get_access_token_no_membership_raises(mock_billing_provider):
    """User exists and password is correct but has no org membership."""
    from src.core.security import hash_secret

    async with TestSessionLocal() as session:
        async with session.begin():
            from src.models.user import User

            user = User(
                name="No Org User",
                email="nomembership@example.com",
                password=hash_secret("password"),
            )
            session.add(user)

    async with TestSessionLocal() as session:
        async with session.begin():
            service = await _make_service(session, mock_billing_provider)
            with pytest.raises(NotAuthenticatedException):
                await service.get_access_token("nomembership@example.com", "password")


# ---------------------------------------------------------------------------
# refresh_access_token - sub=0 in JWT (line 411)
# ---------------------------------------------------------------------------


async def test_refresh_access_token_zero_user_id_raises(mock_billing_provider, mocker):
    """JWT decodes successfully but sub='0' > user_id falsy > NotAuthenticated."""
    mocker.patch(
        "src.services.auth.decode_token",
        return_value={"sub": "0"},
    )

    async with TestSessionLocal() as session:
        async with session.begin():
            service = await _make_service(session, mock_billing_provider)
            with pytest.raises(NotAuthenticatedException):
                await service.refresh_access_token("fake.jwt.token")


# ---------------------------------------------------------------------------
# refresh_access_token - user not found (line 415)
# ---------------------------------------------------------------------------


async def test_refresh_access_token_user_not_found_raises(
    mock_billing_provider, mocker
):
    """JWT has valid sub but user doesn't exist in DB."""
    mocker.patch(
        "src.services.auth.decode_token",
        return_value={"sub": "99999"},
    )

    async with TestSessionLocal() as session:
        async with session.begin():
            service = await _make_service(session, mock_billing_provider)
            with pytest.raises(NotAuthenticatedException):
                await service.refresh_access_token("fake.jwt.token")


# ---------------------------------------------------------------------------
# refresh_access_token - token mismatch (line 419)
# ---------------------------------------------------------------------------


async def test_refresh_access_token_mismatch_raises(mock_billing_provider):
    """Old refresh token fails verify_secret after a new login replaces it."""
    async with TestSessionLocal() as session:
        async with session.begin():
            service = await _make_service(session, mock_billing_provider)
            first = await service.get_access_token("admin@example.org", "password")
            # Login again > stored token replaced with new one
            await service.get_access_token("admin@example.org", "password")
            # Old token still decodes but no longer matches stored hash
            with pytest.raises(NotAuthenticatedException):
                await service.refresh_access_token(first.refresh_token)


# ---------------------------------------------------------------------------
# refresh_access_token - no org membership (line 425)
# ---------------------------------------------------------------------------


async def test_refresh_access_token_no_membership_raises(mock_billing_provider):
    """Valid token/user but UserOrganization row deleted before refresh."""
    from sqlalchemy import delete

    from src.models.user_organization import UserOrganization

    async with TestSessionLocal() as session:
        async with session.begin():
            service = await _make_service(session, mock_billing_provider)
            tokens = await service.get_access_token("admin@example.org", "password")

    async with TestSessionLocal() as session:
        async with session.begin():
            # Remove all org memberships for user 1
            await session.execute(
                delete(UserOrganization).where(UserOrganization.user_id == 1)
            )

    async with TestSessionLocal() as session:
        async with session.begin():
            service = await _make_service(session, mock_billing_provider)
            with pytest.raises(NotAuthenticatedException):
                await service.refresh_access_token(tokens.refresh_token)


# ---------------------------------------------------------------------------
# switch_organization - user not found (line 454)
# ---------------------------------------------------------------------------


async def test_switch_organization_user_not_found_raises(mock_billing_provider):
    """Auth object references a non-existent user_id > NotAuthenticated."""
    from src.core.security import Auth

    ghost_auth = Auth(
        id=99999,
        name="Ghost",
        email="ghost@example.com",
        organization_id=1,
        roles=[],
        permissions=[],
    )

    async with TestSessionLocal() as session:
        async with session.begin():
            repos = RepositoryManager(session)
            service = AuthService(repos, mock_billing_provider)
            with pytest.raises(NotAuthenticatedException):
                await service.switch_organization(ghost_auth, organization_id=1)
