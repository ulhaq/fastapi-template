from collections.abc import Callable
from typing import Annotated

from fastapi import Depends

from src.billing.dependencies import BillingProviderDep
from src.core.config import settings
from src.core.dependencies import authenticate
from src.core.exceptions import (
    AlreadyExistsException,
    NotFoundException,
    PermissionDeniedException,
)
from src.core.security import Auth, authenticate_user, hash_secret, sign
from src.enums import OWNER_ROLE_NAME, ErrorCode, Permission
from src.models.role import Role
from src.models.user import User
from src.repositories.repository_manager import RepositoryManager
from src.repositories.user import UserRepository
from src.schemas.common import PageQueryParams, PaginatedResponse
from src.schemas.user import (
    ChangePasswordIn,
    InviteUserIn,
    UserOut,
    UserPatch,
    UserRoleIn,
)
from src.services.base import ResourceService
from src.services.utils import send_email


class UserService(
    ResourceService[UserRepository, User, UserPatch | ChangePasswordIn, UserOut]
):
    current_user: Auth

    def __init__(
        self,
        repos: Annotated[RepositoryManager, Depends()],
        current_user: Annotated[Auth, Depends(authenticate)],
        provider: BillingProviderDep,
    ):
        self.repo = repos.user
        self.repo.set_tenant_scope(current_user.tenant_id)
        self.current_user = current_user
        self.provider = provider
        super().__init__(repos)

    def _user_out(self, user: User) -> UserOut:
        tenant_roles = [
            r for r in user.roles if r.tenant_id == self.current_user.tenant_id
        ]
        return UserOut.model_validate(
            {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "created_at": user.created_at,
                "updated_at": user.updated_at,
                "roles": tenant_roles,
            }
        )

    async def _assert_not_last_owner(self, user: User, new_roles: list) -> None:
        tenant_roles = [
            r for r in user.roles if r.tenant_id == self.current_user.tenant_id
        ]
        owner_role = next(
            (r for r in tenant_roles if r.is_protected and r.name == OWNER_ROLE_NAME),
            None,
        )
        if owner_role is None:
            return
        if any(r.id == owner_role.id for r in new_roles):
            return
        if not await self.repo.has_other_user_with_role(
            owner_role.id, exclude_user_id=user.id
        ):
            raise PermissionDeniedException(
                "Cannot remove the last Owner from a tenant",
                error_code=ErrorCode.LAST_OWNER_REMOVAL,
            )

    async def _assert_not_last_admin(self, user: User) -> None:
        tenant_roles = [
            r for r in user.roles if r.tenant_id == self.current_user.tenant_id
        ]
        user_permissions = {p.name for role in tenant_roles for p in role.permissions}
        if Permission.MANAGE_USER_ROLE.value not in user_permissions:
            return
        if not await self.repo.has_other_user_with_permission(
            Permission.MANAGE_USER_ROLE.value, exclude_user_id=user.id
        ):
            raise PermissionDeniedException(
                "Cannot perform this action: tenant must retain at least one "
                "user with role management access"
            )

    async def paginate(
        self,
        schema_out: type[UserOut],
        page_query_params: PageQueryParams,
        include_deleted: bool = False,
    ) -> PaginatedResponse[UserOut]:
        items, total = await self.repo.paginate(
            sort=page_query_params.sort,
            filters=page_query_params.filters,
            page_size=page_query_params.page_size,
            page_number=page_query_params.page_number,
            include_deleted=include_deleted,
        )
        return PaginatedResponse(
            items=[self._user_out(item) for item in items],
            page_number=page_query_params.page_number,
            page_size=page_query_params.page_size,
            total=total,
        )

    async def get_authenticated_user(self) -> UserOut:
        return self._user_out(await self.get(self.current_user.id))

    async def patch_profile(self, schema_in: UserPatch) -> UserOut:
        async def validate() -> None:
            if schema_in.email:
                user = await self.repo.get_by_email(schema_in.email)
                if user and user.email != self.current_user.email:
                    raise AlreadyExistsException(
                        f"User already exists. [email={schema_in.email}]",
                        error_code=ErrorCode.EMAIL_ALREADY_EXISTS,
                    )

        user = await super().patch(self.current_user.id, schema_in, validate)

        if schema_in.email:
            tenant_roles = [
                r for r in user.roles if r.tenant_id == self.current_user.tenant_id
            ]
            is_owner = any(
                r.is_protected and r.name == OWNER_ROLE_NAME for r in tenant_roles
            )
            if is_owner:
                tenant = await self.repos.tenant.get(self.current_user.tenant_id)
                if tenant and tenant.external_customer_id:
                    await self.provider.update_customer(
                        tenant.external_customer_id, email=schema_in.email
                    )

        return self._user_out(user)

    async def change_password(self, schema_in: ChangePasswordIn) -> UserOut:
        auth = self.current_user

        user = authenticate_user(
            schema_in.password, await self.repos.user.get_by_email(auth.email)
        )

        if not user:
            raise PermissionDeniedException("Incorrect password")

        hashed_pw = hash_secret(schema_in.new_password)

        return self._user_out(await self.repo.update(user, password=hashed_pw))

    async def get_user(self, identifier: int, include_deleted: bool = False) -> UserOut:
        return self._user_out(
            await super().get(identifier, include_deleted=include_deleted)
        )

    async def invite_user(
        self, invite_in: InviteUserIn, schedule_task: Callable
    ) -> None:
        existing = await self.repo.get_by_email(invite_in.email)
        if existing:
            membership = await self.repos.user_tenant.get_by_user_and_tenant(
                user_id=existing.id, tenant_id=self.current_user.tenant_id
            )
            if membership:
                raise AlreadyExistsException(
                    f"User already exists in this tenant. [email={invite_in.email}]",
                    error_code=ErrorCode.EMAIL_ALREADY_EXISTS,
                )

        token = sign(
            data={
                "email": invite_in.email,
                "tenant_id": self.current_user.tenant_id,
                "role_ids": invite_in.role_ids,
            },
            salt="invite",
        )

        await self.repos.email_verification_token.delete_by_email(invite_in.email)
        await self.repos.email_verification_token.create(
            email=invite_in.email, token=hash_secret(token)
        )

        tenant = await self.repos.tenant.get(self.current_user.tenant_id)
        if not tenant:
            raise NotFoundException("Tenant not found.")

        schedule_task(
            send_email,
            address=invite_in.email,
            user_name=invite_in.email,
            subject=f"You've been invited to {tenant.name}",
            email_template="invite-user",
            data={
                "invite_url": (
                    f"{settings.frontend_url}/{settings.frontend_invite_path}{token}"
                ),
                "tenant_name": tenant.name,
                "expiration_days": settings.invite_expiry // (60 * 60 * 24),
            },
        )

    async def delete_user(self, identifier: int) -> None:
        user = await self.get(identifier)
        await self._assert_not_last_admin(user)
        await self._assert_not_last_owner(user, [])
        await self.repo.delete(user)

    async def manage_roles(self, identifier: int, schema_in: UserRoleIn) -> UserOut:
        if self.current_user.id == identifier:
            raise PermissionDeniedException(
                "You are not allowed to manage your own roles"
            )

        user = await self.get(identifier)
        new_roles: list[Role] = []

        if schema_in.role_ids:
            self.repos.role.set_tenant_scope(self.current_user.tenant_id)
            new_roles = list(await self.repos.role.filter_by_ids(schema_in.role_ids))
            if len(new_roles) != len(schema_in.role_ids):
                raise PermissionDeniedException(
                    "One or more roles do not belong to your tenant"
                )

        manage_permission = Permission.MANAGE_USER_ROLE.value
        tenant_user_roles = [
            r for r in user.roles if r.tenant_id == self.current_user.tenant_id
        ]
        user_has_manage_permission = any(
            manage_permission in {p.name for p in role.permissions}
            for role in tenant_user_roles
        )
        new_roles_have_manage_permission = any(
            manage_permission in {p.name for p in role.permissions}
            for role in new_roles
        )
        if user_has_manage_permission and not new_roles_have_manage_permission:
            await self._assert_not_last_admin(user)

        await self._assert_not_last_owner(user, new_roles)

        current_roles = {role.id for role in tenant_user_roles}
        schema_in_role_ids = set(schema_in.role_ids)

        if roles_to_add := schema_in_role_ids - current_roles:
            await self.repo.add_roles(user, *roles_to_add)

        if roles_to_remove := current_roles - schema_in_role_ids:
            await self.repo.remove_roles(user, *roles_to_remove)

        return self._user_out(user)
