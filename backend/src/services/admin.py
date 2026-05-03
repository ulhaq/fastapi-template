from collections.abc import Callable
from typing import Annotated

from fastapi import Depends

from src.core.config import settings
from src.core.context import client_ip_var
from src.core.dependencies import authenticate
from src.core.exceptions import (
    AlreadyExistsException,
    NotFoundException,
    PermissionDeniedException,
)
from src.core.security import Auth, hash_secret, sign
from src.enums import AuditAction, ErrorCode
from src.repositories.repository_manager import RepositoryManager
from src.schemas.admin import (
    AddMemberIn,
    AdminOrganizationCreate,
    AdminOrganizationOut,
    AdminUserOut,
    OrgMemberOut,
)
from src.schemas.audit_log import AuditLogOut
from src.schemas.common import PageQueryParams, PaginatedResponse
from src.schemas.organization import OrganizationOut, OrganizationPatch
from src.schemas.role import RoleOut
from src.schemas.user import UserPatch
from src.services.utils import send_email, setup_new_organization


class AdminService:
    def __init__(
        self,
        repos: Annotated[RepositoryManager, Depends()],
        current_user: Annotated[Auth, Depends(authenticate)],
    ) -> None:
        self.repos = repos
        self.current_user = current_user

    async def create_organization(
        self, schema_in: AdminOrganizationCreate
    ) -> OrganizationOut:
        existing = await self.repos.organization.get_one_by_name(
            schema_in.name, include_deleted=True
        )
        if existing is not None and existing.deleted_at is None:
            raise AlreadyExistsException(
                f"Organization already exists. [name={schema_in.name}]"
            )
        if existing is not None and existing.deleted_at is not None:
            organization = await self.repos.organization.restore(existing)
        else:
            organization = await self.repos.organization.create(name=schema_in.name)
        await setup_new_organization(self.repos, organization)
        await self.repos.audit_log.create(
            action=AuditAction.ORG_CREATE,
            organization_id=None,
            user_id=self.current_user.id,
            resource_type="organization",
            resource_id=organization.id,
            ip_address=client_ip_var.get(),
        )
        return OrganizationOut.model_validate(organization)

    async def list_organizations(
        self, page_query_params: PageQueryParams
    ) -> PaginatedResponse[AdminOrganizationOut]:
        items, total = await self.repos.organization.paginate(
            sort=page_query_params.sort,
            filters=page_query_params.filters,
            page_size=page_query_params.page_size,
            page_number=page_query_params.page_number,
        )
        org_ids = [org.id for org in items]
        sub_map = await self.repos.subscription.get_for_organizations(org_ids)
        result = []
        for org in items:
            sub = sub_map.get(org.id)
            plan_name: str | None = None
            if sub and sub.plan_price and sub.plan_price.plan:
                plan_name = sub.plan_price.plan.name
            result.append(
                AdminOrganizationOut(
                    **OrganizationOut.model_validate(org).model_dump(),
                    plan_name=plan_name,
                    subscription_status=sub.status if sub else None,
                )
            )
        return PaginatedResponse(
            items=result,
            page_number=page_query_params.page_number,
            page_size=page_query_params.page_size,
            total=total,
        )

    async def patch_organization(
        self, org_id: int, schema_in: OrganizationPatch
    ) -> OrganizationOut:
        org = await self.repos.organization.get(org_id)
        if not org:
            raise NotFoundException(f"Organization not found. [id={org_id}]")
        updated = await self.repos.organization.update(
            org, **schema_in.model_dump(exclude_none=True)
        )
        await self.repos.audit_log.create(
            action=AuditAction.ORG_UPDATE,
            organization_id=None,
            user_id=self.current_user.id,
            resource_type="organization",
            resource_id=org_id,
            ip_address=client_ip_var.get(),
        )
        return OrganizationOut.model_validate(updated)

    async def delete_organization(self, org_id: int) -> None:
        org = await self.repos.organization.get(org_id)
        if not org:
            raise NotFoundException(f"Organization not found. [id={org_id}]")

        subscription = await self.repos.subscription.get_active_for_organization(org_id)
        if subscription and subscription.external_subscription_id:
            raise PermissionDeniedException(
                "Cannot delete an organization with an active subscription."
                " Cancel the subscription first.",
                error_code=ErrorCode.SUBSCRIPTION_ALREADY_ACTIVE,
            )

        await self.repos.subscription.cancel_all_for_organization(org_id)

        repo = self.repos.user_organization
        memberships = await repo.get_all_members_of_organization(org_id)
        for membership in memberships:
            user = await self.repos.user.get(membership.user_id)
            if user:
                other_orgs = await repo.get_all_for_user(user.id)
                if len(other_orgs) <= 1:
                    await self.repos.refresh_token.delete_by_user(user)
                    await self.repos.user.delete(user)
            await self.repos.user_organization.force_delete(membership)

        await self.repos.organization.delete(org)
        await self.repos.audit_log.create(
            action=AuditAction.ORG_DELETE,
            organization_id=None,
            user_id=self.current_user.id,
            resource_type="organization",
            resource_id=org_id,
            ip_address=client_ip_var.get(),
        )

    async def list_org_members(self, org_id: int) -> list[OrgMemberOut]:
        org = await self.repos.organization.get(org_id)
        if not org:
            raise NotFoundException(f"Organization not found. [id={org_id}]")
        repo = self.repos.user_organization
        memberships = await repo.get_all_members_of_organization(org_id)
        result = []
        for membership in memberships:
            user = await self.repos.user.get(membership.user_id)
            if user:
                org_roles = [r for r in user.roles if r.organization_id == org_id]
                result.append(
                    OrgMemberOut(
                        user_id=user.id,
                        name=user.name,
                        email=user.email,
                        roles=[RoleOut.model_validate(r) for r in org_roles],
                    )
                )
        return result

    async def add_org_member(self, org_id: int, schema_in: AddMemberIn) -> OrgMemberOut:
        org = await self.repos.organization.get(org_id)
        if not org:
            raise NotFoundException(f"Organization not found. [id={org_id}]")
        user = await self.repos.user.get_by_email(schema_in.email)
        if not user:
            raise NotFoundException(f"User not found. [email={schema_in.email}]")
        existing = await self.repos.user_organization.get_by_user_and_organization(
            user_id=user.id, organization_id=org_id
        )
        if existing:
            raise AlreadyExistsException(
                "User is already a member of this organization."
                f" [email={schema_in.email}]",
                error_code=ErrorCode.EMAIL_ALREADY_EXISTS,
            )
        from datetime import UTC, datetime

        await self.repos.user_organization.create(
            user_id=user.id,
            organization_id=org_id,
            last_active_at=datetime.now(UTC),
        )
        if schema_in.role_ids:
            self.repos.role.set_organization_scope(org_id)
            valid_roles = await self.repos.role.filter_by_ids(schema_in.role_ids)
            if valid_roles:
                await self.repos.user.add_roles(user, *[r.id for r in valid_roles])
        await self.repos.audit_log.create(
            action=AuditAction.MEMBER_ADD,
            organization_id=None,
            user_id=self.current_user.id,
            resource_type="user",
            resource_id=user.id,
            ip_address=client_ip_var.get(),
            details={"organization_id": org_id, "email": schema_in.email},
        )
        user = await self.repos.user.get(user.id)
        if not user:
            raise NotFoundException("User not found after creation.")
        org_roles = [r for r in user.roles if r.organization_id == org_id]
        return OrgMemberOut(
            user_id=user.id,
            name=user.name,
            email=user.email,
            roles=[RoleOut.model_validate(r) for r in org_roles],
        )

    async def remove_org_member(self, org_id: int, user_id: int) -> None:
        org = await self.repos.organization.get(org_id)
        if not org:
            raise NotFoundException(f"Organization not found. [id={org_id}]")
        membership = await self.repos.user_organization.get_by_user_and_organization(
            user_id=user_id, organization_id=org_id
        )
        if not membership:
            raise NotFoundException(
                f"User is not a member of this organization. [user_id={user_id}]"
            )
        await self.repos.api_token.revoke_all_for_user_org(user_id, org_id)
        await self.repos.user_organization.force_delete(membership)
        await self.repos.audit_log.create(
            action=AuditAction.MEMBER_REMOVE,
            organization_id=None,
            user_id=self.current_user.id,
            resource_type="user",
            resource_id=user_id,
            ip_address=client_ip_var.get(),
            details={"organization_id": org_id},
        )

    async def list_users(
        self, page_query_params: PageQueryParams
    ) -> PaginatedResponse[AdminUserOut]:
        items, total = await self.repos.user.paginate(
            sort=page_query_params.sort,
            filters=page_query_params.filters,
            page_size=page_query_params.page_size,
            page_number=page_query_params.page_number,
        )
        return PaginatedResponse(
            items=[AdminUserOut.model_validate(item) for item in items],
            page_number=page_query_params.page_number,
            page_size=page_query_params.page_size,
            total=total,
        )

    async def patch_user(self, user_id: int, schema_in: UserPatch) -> AdminUserOut:
        user = await self.repos.user.get(user_id)
        if not user:
            raise NotFoundException(f"User not found. [id={user_id}]")
        if schema_in.email:
            existing = await self.repos.user.get_by_email(schema_in.email)
            if existing and existing.id != user_id:
                raise AlreadyExistsException(
                    f"User already exists. [email={schema_in.email}]",
                    error_code=ErrorCode.EMAIL_ALREADY_EXISTS,
                )
        updated = await self.repos.user.update(
            user, **schema_in.model_dump(exclude_none=True)
        )
        await self.repos.audit_log.create(
            action=AuditAction.USER_UPDATE,
            organization_id=None,
            user_id=self.current_user.id,
            resource_type="user",
            resource_id=user_id,
            ip_address=client_ip_var.get(),
        )
        return AdminUserOut.model_validate(updated)

    async def delete_user(self, user_id: int) -> None:
        user = await self.repos.user.get(user_id)
        if not user:
            raise NotFoundException(f"User not found. [id={user_id}]")

        memberships = await self.repos.user_organization.get_all_for_user(user_id)
        for membership in memberships:
            await self.repos.api_token.revoke_all_for_user_org(
                user_id, membership.organization_id
            )
            await self.repos.user_organization.force_delete(membership)

        await self.repos.refresh_token.delete_by_user(user)
        await self.repos.user.delete(user)
        await self.repos.audit_log.create(
            action=AuditAction.USER_DELETE,
            organization_id=None,
            user_id=self.current_user.id,
            resource_type="user",
            resource_id=user_id,
            ip_address=client_ip_var.get(),
        )

    async def list_audit_logs(
        self,
        page_size: int,
        page_number: int,
        action_filter: AuditAction | None = None,
    ) -> PaginatedResponse[AuditLogOut]:
        items, total = await self.repos.audit_log.paginate_all(
            page_size=page_size,
            page_number=page_number,
            action_filter=action_filter,
        )
        return PaginatedResponse(
            items=[AuditLogOut.model_validate(item) for item in items],
            page_size=page_size,
            page_number=page_number,
            total=total,
        )

    async def force_password_reset(self, user_id: int, schedule_task: Callable) -> None:
        user = await self.repos.user.get(user_id)
        if not user:
            raise NotFoundException(f"User not found. [id={user_id}]")
        token = sign(data=user.email, salt="reset-password")
        await self.repos.user.delete_password_reset_token(user=user)
        await self.repos.user.create_password_reset_token(
            user=user, token=hash_secret(token)
        )
        schedule_task(
            send_email,
            address=user.email,
            user_name=user.name,
            subject="Password Reset",
            email_template="reset-password",
            data={
                "reset_url": (
                    f"{settings.frontend_url}/"
                    f"{settings.frontend_password_reset_path}{token}"
                ),
                "expiration_minutes": settings.auth_password_reset_expiry // 60,
            },
        )
        await self.repos.audit_log.create(
            action=AuditAction.AUTH_FORCE_PASSWORD_RESET,
            organization_id=None,
            user_id=self.current_user.id,
            resource_type="user",
            resource_id=user_id,
            ip_address=client_ip_var.get(),
        )
