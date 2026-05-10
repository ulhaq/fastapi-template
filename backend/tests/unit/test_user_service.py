# mypy: disable-error-code="no-untyped-def"
"""Direct unit tests for UserService."""

import pytest

from src.core.exceptions import AlreadyExistsException, PermissionDeniedException
from src.core.security import Auth
from src.enums import Permission as PermEnum
from src.repositories.repository_manager import RepositoryManager
from src.schemas.user import ChangePasswordIn, InviteUserIn, UserPatch, UserRoleIn
from src.services.user import UserService
from tests.conftest import TestSessionLocal


def _admin_auth(user_id: int = 1, org_id: int = 1) -> Auth:
    return Auth(
        id=user_id,
        name="Alice Owner",
        email="admin@example.org",
        organization_id=org_id,
        roles=["Owner"],
        permissions=[p.value for p in PermEnum],
    )


def _standard_auth(user_id: int = 2, org_id: int = 1) -> Auth:
    return Auth(
        id=user_id,
        name="Bob Member",
        email="standard@example.org",
        organization_id=org_id,
        roles=["Member"],
        permissions=[],
    )


def _no_op_schedule(fn, **kwargs):
    pass


def _make_service(session, auth: Auth, provider) -> UserService:
    repos = RepositoryManager(session)
    return UserService(repos, auth, provider)


# ---------------------------------------------------------------------------
# get_authenticated_user
# ---------------------------------------------------------------------------


async def test_get_authenticated_user(mock_billing_provider):
    async with TestSessionLocal() as session:
        async with session.begin():
            service = _make_service(session, _admin_auth(), mock_billing_provider)
            user_out = await service.get_authenticated_user()
    assert user_out.email == "admin@example.org"


# ---------------------------------------------------------------------------
# patch_profile
# ---------------------------------------------------------------------------


async def test_patch_profile_updates_name(mock_billing_provider):
    async with TestSessionLocal() as session:
        async with session.begin():
            service = _make_service(session, _admin_auth(), mock_billing_provider)
            out = await service.patch_profile(UserPatch(name="New Name"))
    assert out.name == "New Name"


async def test_patch_profile_duplicate_email_raises(mock_billing_provider):
    async with TestSessionLocal() as session:
        async with session.begin():
            # standard@example.org already exists; try to take it as admin
            service = _make_service(session, _admin_auth(), mock_billing_provider)
            with pytest.raises(AlreadyExistsException):
                await service.patch_profile(UserPatch(email="standard@example.org"))


async def test_patch_profile_owner_syncs_stripe_customer(mock_billing_provider):
    async with TestSessionLocal() as session:
        async with session.begin():
            repos = RepositoryManager(session)
            org = await repos.organization.get(1)
            assert org
            await repos.organization.update(org, external_customer_id="cus_sync")

    async with TestSessionLocal() as session:
        async with session.begin():
            service = _make_service(session, _admin_auth(), mock_billing_provider)
            await service.patch_profile(UserPatch(email="new_owner@example.org"))

    mock_billing_provider.update_customer.assert_called()


# ---------------------------------------------------------------------------
# change_password
# ---------------------------------------------------------------------------


async def test_change_password_success(mock_billing_provider):
    async with TestSessionLocal() as session:
        async with session.begin():
            service = _make_service(session, _admin_auth(), mock_billing_provider)
            out = await service.change_password(
                ChangePasswordIn(
                    password="password",
                    new_password="NewP@ss123!",
                    confirm_password="NewP@ss123!",
                )
            )
    assert out.email == "admin@example.org"


async def test_change_password_wrong_current_raises(mock_billing_provider):
    async with TestSessionLocal() as session:
        async with session.begin():
            service = _make_service(session, _admin_auth(), mock_billing_provider)
            with pytest.raises(PermissionDeniedException):
                await service.change_password(
                    ChangePasswordIn(
                        password="wrong",
                        new_password="NewP@ss123!",
                        confirm_password="NewP@ss123!",
                    )
                )


# ---------------------------------------------------------------------------
# get_user / patch_user
# ---------------------------------------------------------------------------


async def test_get_user_returns_user(mock_billing_provider):
    async with TestSessionLocal() as session:
        async with session.begin():
            service = _make_service(session, _admin_auth(), mock_billing_provider)
            out = await service.get_user(2)  # standard user
    assert out.email == "standard@example.org"


async def test_patch_user_updates_name(mock_billing_provider):
    async with TestSessionLocal() as session:
        async with session.begin():
            service = _make_service(session, _admin_auth(), mock_billing_provider)
            out = await service.patch_user(2, UserPatch(name="Patched Name"))
    assert out.name == "Patched Name"


async def test_patch_user_duplicate_email_raises(mock_billing_provider):
    async with TestSessionLocal() as session:
        async with session.begin():
            service = _make_service(session, _admin_auth(), mock_billing_provider)
            with pytest.raises(AlreadyExistsException):
                await service.patch_user(2, UserPatch(email="admin@example.org"))


# ---------------------------------------------------------------------------
# invite_user
# ---------------------------------------------------------------------------


async def test_invite_user_new_email(mock_billing_provider):
    async with TestSessionLocal() as session:
        async with session.begin():
            service = _make_service(session, _admin_auth(), mock_billing_provider)
            # Should complete without raising
            await service.invite_user(
                InviteUserIn(email="newinvitee@example.com"),
                schedule_task=_no_op_schedule,
            )


async def test_invite_user_owner_role_raises(mock_billing_provider):
    """Inviting with the Owner role_id raises PermissionDeniedException."""
    # Role id=1 is org 1's Owner (protected)
    async with TestSessionLocal() as session:
        async with session.begin():
            service = _make_service(session, _admin_auth(), mock_billing_provider)
            with pytest.raises(PermissionDeniedException):
                await service.invite_user(
                    InviteUserIn(email="newperson@example.com", role_ids=[1]),
                    schedule_task=_no_op_schedule,
                )


async def test_invite_user_already_member_raises(mock_billing_provider):
    async with TestSessionLocal() as session:
        async with session.begin():
            service = _make_service(session, _admin_auth(), mock_billing_provider)
            with pytest.raises(AlreadyExistsException):
                await service.invite_user(
                    InviteUserIn(email="standard@example.org"),
                    schedule_task=_no_op_schedule,
                )


# ---------------------------------------------------------------------------
# remove_user
# ---------------------------------------------------------------------------


async def test_remove_user_success(mock_billing_provider):
    """Remove standard user (id=2) from org 1."""
    async with TestSessionLocal() as session:
        async with session.begin():
            service = _make_service(session, _admin_auth(), mock_billing_provider)
            await service.remove_user(2)


async def test_remove_owner_raises(mock_billing_provider):
    """Removing the owner should raise PermissionDeniedException."""
    async with TestSessionLocal() as session:
        async with session.begin():
            # Admin (id=1) tries to remove themselves (the Owner)
            service = _make_service(session, _standard_auth(), mock_billing_provider)
            with pytest.raises(PermissionDeniedException):
                await service.remove_user(1)


# ---------------------------------------------------------------------------
# manage_roles
# ---------------------------------------------------------------------------


async def test_manage_roles_self_raises(mock_billing_provider):
    async with TestSessionLocal() as session:
        async with session.begin():
            service = _make_service(session, _admin_auth(), mock_billing_provider)
            with pytest.raises(PermissionDeniedException):
                await service.manage_roles(1, UserRoleIn(role_ids=[]))


async def test_manage_roles_clears_roles(mock_billing_provider):
    async with TestSessionLocal() as session:
        async with session.begin():
            service = _make_service(session, _admin_auth(), mock_billing_provider)
            out = await service.manage_roles(2, UserRoleIn(role_ids=[]))
    assert out.roles == []


# ---------------------------------------------------------------------------
# delete_me
# ---------------------------------------------------------------------------


async def test_delete_me_non_owner(mock_billing_provider):
    """Standard user can delete themselves."""
    from src.schemas.user import DeleteMeIn

    async with TestSessionLocal() as session:
        async with session.begin():
            service = _make_service(session, _standard_auth(), mock_billing_provider)
            await service.delete_me(
                DeleteMeIn(current_password="password"),
                schedule_task=_no_op_schedule,
            )


async def test_delete_me_wrong_password_raises(mock_billing_provider):
    from src.schemas.user import DeleteMeIn

    async with TestSessionLocal() as session:
        async with session.begin():
            service = _make_service(session, _standard_auth(), mock_billing_provider)
            with pytest.raises(PermissionDeniedException):
                await service.delete_me(
                    DeleteMeIn(current_password="wrongpass"),
                    schedule_task=_no_op_schedule,
                )


async def test_delete_me_owner_raises(mock_billing_provider):
    """Owner cannot delete themselves without transferring ownership first."""
    from src.schemas.user import DeleteMeIn

    async with TestSessionLocal() as session:
        async with session.begin():
            service = _make_service(session, _admin_auth(), mock_billing_provider)
            with pytest.raises(PermissionDeniedException):
                await service.delete_me(
                    DeleteMeIn(current_password="password"),
                    schedule_task=_no_op_schedule,
                )


# ---------------------------------------------------------------------------
# paginate
# ---------------------------------------------------------------------------


async def test_paginate_returns_paginated_response(mock_billing_provider):
    from src.schemas.common import PageQueryParams
    from src.schemas.user import UserOut

    async with TestSessionLocal() as session:
        async with session.begin():
            service = _make_service(session, _admin_auth(), mock_billing_provider)
            result = await service.paginate(
                UserOut,
                PageQueryParams(page_number=1, page_size=10, sort=[], filters=[]),
            )

    assert result.total >= 1
    assert isinstance(result.items, list)


# ---------------------------------------------------------------------------
# patch_user - owner email sync (lines 182-195)
# ---------------------------------------------------------------------------


async def test_patch_user_owner_syncs_stripe_customer(mock_billing_provider):
    """patch_user updates Stripe customer email when patching an owner's email."""
    async with TestSessionLocal() as session:
        async with session.begin():
            repos = RepositoryManager(session)
            org = await repos.organization.get(1)
            assert org
            await repos.organization.update(org, external_customer_id="cus_sync_user")

    async with TestSessionLocal() as session:
        async with session.begin():
            service = _make_service(session, _admin_auth(), mock_billing_provider)
            # Patch user 1 (owner) email
            await service.patch_user(1, UserPatch(email="owner_new@example.org"))

    mock_billing_provider.update_customer.assert_called()


# ---------------------------------------------------------------------------
# invite_user - org not found (line 260)
# ---------------------------------------------------------------------------


async def test_invite_user_org_not_found_raises(mock_billing_provider):
    """When current_user.organization_id doesn't exist, NotFoundException is raised."""
    from src.core.exceptions import NotFoundException

    ghost_auth = Auth(
        id=1,
        name="Ghost",
        email="admin@example.org",
        organization_id=9999,
        roles=["Owner"],
        permissions=[p.value for p in PermEnum],
    )

    async with TestSessionLocal() as session:
        async with session.begin():
            service = _make_service(session, ghost_auth, mock_billing_provider)
            with pytest.raises(NotFoundException):
                await service.invite_user(
                    InviteUserIn(email="fresh_invite@example.com"),
                    schedule_task=_no_op_schedule,
                )


# ---------------------------------------------------------------------------
# manage_roles - role not in org (lines 329-332)
# ---------------------------------------------------------------------------


async def test_manage_roles_unknown_role_raises(mock_billing_provider):
    """role_ids referencing a different org's role raises PermissionDeniedException."""
    # Role id=4 belongs to org 2's Owner, not org 1
    async with TestSessionLocal() as session:
        async with session.begin():
            service = _make_service(session, _admin_auth(), mock_billing_provider)
            with pytest.raises(PermissionDeniedException):
                await service.manage_roles(2, UserRoleIn(role_ids=[4]))


# ---------------------------------------------------------------------------
# manage_roles - owner role protection (line 361)
# ---------------------------------------------------------------------------


async def test_manage_roles_assign_owner_raises(mock_billing_provider):
    """Trying to assign Owner role to a non-owner raises PermissionDeniedException."""
    # Role id=1 is org 1's Owner (protected)
    async with TestSessionLocal() as session:
        async with session.begin():
            service = _make_service(session, _admin_auth(), mock_billing_provider)
            with pytest.raises(PermissionDeniedException):
                # User 2 (Member) > assign Owner role >
                # owner_role_in_new=True, current=False
                await service.manage_roles(2, UserRoleIn(role_ids=[1]))


# ---------------------------------------------------------------------------
# manage_roles - add roles path (line 371) and _assert_not_last_admin (line 351)
# ---------------------------------------------------------------------------


async def test_manage_roles_adds_role(mock_billing_provider):
    """Assigning a new (non-owner) role to a user hits the add_roles branch."""
    # Role id=2 is org 1's Admin role; user 2 currently has only Member (id=3)
    async with TestSessionLocal() as session:
        async with session.begin():
            service = _make_service(session, _admin_auth(), mock_billing_provider)
            out = await service.manage_roles(2, UserRoleIn(role_ids=[2]))

    assert any(r["name"] for r in out.model_dump()["roles"])


async def test_manage_roles_removing_manage_permission_calls_assert(
    mock_billing_provider,
):
    """Removing MANAGE_USER_ROLE from a user calls _assert_not_last_admin (line 351)."""
    # First give user 2 the Admin role (has MANAGE_USER_ROLE)
    async with TestSessionLocal() as session:
        async with session.begin():
            repos = RepositoryManager(session)
            user2 = await repos.user.get(2)
            assert user2
            await repos.user.add_roles(user2, 2)  # role 2 = org1 Admin

    # Now remove it (set to Member only) - user 1 still has it via Owner, so no raise
    async with TestSessionLocal() as session:
        async with session.begin():
            service = _make_service(session, _admin_auth(), mock_billing_provider)
            out = await service.manage_roles(2, UserRoleIn(role_ids=[3]))

    assert out is not None


# ---------------------------------------------------------------------------
# _assert_not_last_admin raises (line 83)
# ---------------------------------------------------------------------------


async def test_remove_user_last_admin_raises(mock_billing_provider):
    """Removing the last user with MANAGE_USER_ROLE in an org raises."""
    from datetime import UTC, datetime

    from src.enums import Permission as PermEnum2
    from src.models.organization import Organization
    from src.models.role import Role
    from src.models.user import User
    from src.models.user_organization import UserOrganization

    async with TestSessionLocal() as session:
        async with session.begin():
            repos = RepositoryManager(session)

            # Fresh org with no pre-existing users
            org = Organization(name="Solo Admin Org")
            session.add(org)
            await session.flush()

            # Role with only MANAGE_USER_ROLE permission
            permissions = await repos.permission.get_all()
            manage_perm = next(
                p for p in permissions if p.name == PermEnum2.MANAGE_USER_ROLE.value
            )
            admin_role = Role(
                name="SoloAdmin",
                description="Solo admin",
                is_protected=False,
                organization_id=org.id,
                permissions=[manage_perm],
            )
            session.add(admin_role)
            await session.flush()

            # Pre-populate roles on the User to avoid lazy-load issues
            target = User(
                name="Last Admin",
                email="lastadmin_solo@example.com",
                password="hashed",
                roles=[admin_role],
            )
            session.add(target)
            await session.flush()

            session.add(
                UserOrganization(
                    user_id=target.id,
                    organization_id=org.id,
                    last_active_at=datetime.now(UTC),
                )
            )
            await session.flush()

            target_id = target.id
            org_id = org.id

    async with TestSessionLocal() as session:
        async with session.begin():
            caller_auth = Auth(
                id=999,  # Caller not in DB
                name="Caller",
                email="caller_solo@example.com",
                organization_id=org_id,
                roles=["Owner"],
                permissions=[p.value for p in PermEnum],
            )
            service = _make_service(session, caller_auth, mock_billing_provider)
            with pytest.raises(PermissionDeniedException):
                await service.remove_user(target_id)


# ---------------------------------------------------------------------------
# export_me
# ---------------------------------------------------------------------------


async def test_export_me_returns_data(mock_billing_provider):
    async with TestSessionLocal() as session:
        async with session.begin():
            service = _make_service(session, _admin_auth(), mock_billing_provider)
            out = await service.export_me()

    assert out.user["email"] == "admin@example.org"
    assert isinstance(out.organizations, list)
    assert isinstance(out.audit_logs, list)
