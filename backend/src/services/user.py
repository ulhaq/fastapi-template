import copy
from collections.abc import Callable
from typing import Annotated

from fastapi import Depends

from src.core.config import settings
from src.core.dependencies import authenticate
from src.core.exceptions import (
    AlreadyExistsException,
    NotFoundException,
    PermissionDeniedException,
)
from src.core.security import Auth, authenticate_user, hash_secret, sign
from src.enums import ErrorCode, Permission
from src.models.user import User
from src.repositories.repository_manager import RepositoryManager
from src.repositories.user import UserRepository
from src.schemas.user import (
    ChangePasswordIn,
    UserBase,
    UserIn,
    UserOut,
    UserPatch,
    UserRoleIn,
    UserTransferIn,
)
from src.services.base import ResourceService
from src.services.utils import send_email


class UserService(
    ResourceService[
        UserRepository, User, UserBase | UserIn | UserPatch | ChangePasswordIn, UserOut
    ]
):
    current_user: Auth

    def __init__(
        self,
        repos: Annotated[RepositoryManager, Depends()],
        current_user: Annotated[Auth, Depends(authenticate)],
    ):
        self.repo = repos.user
        self.repo.set_tenant_scope(current_user.tenant_id)
        self.current_user = current_user
        super().__init__(repos)

    async def _assert_not_last_admin(self, user: User) -> None:
        user_permissions = {p.name for role in user.roles for p in role.permissions}
        if Permission.MANAGE_USER_ROLE.value not in user_permissions:
            return
        if not await self.repo.has_other_user_with_permission(
            Permission.MANAGE_USER_ROLE.value, exclude_user_id=user.id
        ):
            raise PermissionDeniedException(
                "Cannot perform this action: tenant must retain at least one "
                "user with role management access"
            )

    async def get_authenticated_user(self) -> UserOut:
        return UserOut.model_validate(await self.get(self.current_user.id))

    async def update_profile(self, schema_in: UserBase) -> UserOut:
        async def validate() -> None:
            user = await self.repo.get_by_email(schema_in.email)
            if user and user.email != auth.email:
                raise AlreadyExistsException(
                    f"User already exists. [email={schema_in.email}]",
                    error_code=ErrorCode.EMAIL_ALREADY_EXISTS,
                )

        auth = self.current_user

        return UserOut.model_validate(
            await super().update(auth.id, schema_in, validate)
        )

    async def patch_profile(self, schema_in: UserPatch) -> UserOut:
        async def validate() -> None:
            if schema_in.email:
                user = await self.repo.get_by_email(schema_in.email)
                if user and user.email != self.current_user.email:
                    raise AlreadyExistsException(
                        f"User already exists. [email={schema_in.email}]",
                        error_code=ErrorCode.EMAIL_ALREADY_EXISTS,
                    )

        return UserOut.model_validate(
            await super().patch(self.current_user.id, schema_in, validate)
        )

    async def change_password(self, schema_in: ChangePasswordIn) -> UserOut:
        auth = self.current_user

        user = authenticate_user(
            schema_in.password, await self.repos.user.get_by_email(auth.email)
        )

        if not user:
            raise PermissionDeniedException("Incorrect password")

        hashed_pw = hash_secret(schema_in.new_password)

        return UserOut.model_validate(await self.repo.update(user, password=hashed_pw))

    async def get_user(self, identifier: int, include_deleted: bool = False) -> UserOut:
        return UserOut.model_validate(
            await super().get(identifier, include_deleted=include_deleted)
        )

    async def create_user(self, schema_in: UserIn, schedule_task: Callable) -> UserOut:
        async def validate() -> None:
            if await self.repo.get_by_email(schema_in.email):
                raise AlreadyExistsException(
                    f"User already exists. [email={schema_in.email}]",
                    error_code=ErrorCode.EMAIL_ALREADY_EXISTS,
                )

        hashed_pw = hash_secret(schema_in.password)
        await validate()

        user = await self.repo.create(
            name=schema_in.name,
            email=schema_in.email,
            password=hashed_pw,
            tenant_id=self.current_user.tenant_id,
        )

        user = copy.copy(user)

        token = sign(data=schema_in.email, salt="reset-password")

        await self.repos.user.delete_password_reset_token(commit=False, user=user)
        await self.repos.user.create_password_reset_token(
            commit=False, user=user, token=hash_secret(token)
        )

        await self.repos.commit()

        schedule_task(
            send_email,
            address=user.email,
            user_name=user.name,
            subject=f"Welcome to {settings.app_name}",
            email_template="new-user",
            data={
                "reset_url": f"{settings.frontend_url}/"
                + settings.frontend_password_reset_path
                + token,
                "expiration_minutes": settings.auth_password_reset_expiry // 60,
            },
        )

        return UserOut.model_validate(user)

    async def delete_user(self, identifier: int) -> None:
        user = await self.get(identifier)
        await self._assert_not_last_admin(user)
        await self.repo.delete(user)

    async def manage_roles(self, identifier: int, schema_in: UserRoleIn) -> UserOut:
        if self.current_user.id == identifier:
            raise PermissionDeniedException(
                "You are not allowed to manage your own roles"
            )

        user = await self.get(identifier)
        new_roles = []

        if schema_in.role_ids:
            self.repos.role.set_tenant_scope(self.current_user.tenant_id)
            new_roles = await self.repos.role.filter_by_ids(schema_in.role_ids)
            if len(new_roles) != len(schema_in.role_ids):
                raise PermissionDeniedException(
                    "One or more roles do not belong to your tenant"
                )

        manage_permission = Permission.MANAGE_USER_ROLE.value
        user_has_manage_permission = any(
            manage_permission in {p.name for p in role.permissions}
            for role in user.roles
        )
        new_roles_have_manage_permission = any(
            manage_permission in {p.name for p in role.permissions}
            for role in new_roles
        )
        if user_has_manage_permission and not new_roles_have_manage_permission:
            await self._assert_not_last_admin(user)

        current_roles = {role.id for role in user.roles}
        schema_in_role_ids = set(schema_in.role_ids)

        if roles_to_add := schema_in_role_ids - current_roles:
            await self.repo.add_roles(user, *roles_to_add)

        if roles_to_remove := current_roles - schema_in_role_ids:
            await self.repo.remove_roles(user, *roles_to_remove)

        return UserOut.model_validate(user)

    async def transfer_user(
        self, identifier: int, schema_in: UserTransferIn
    ) -> UserOut:
        if self.current_user.id == identifier:
            raise PermissionDeniedException("You are not allowed to transfer yourself")

        user = await self.get(identifier)
        await self._assert_not_last_admin(user)

        target_tenant = await self.repos.tenant.get(schema_in.tenant_id)
        if not target_tenant:
            raise NotFoundException(
                f"Tenant not found. [identifier={schema_in.tenant_id}]"
            )

        if user.tenant_id == schema_in.tenant_id:
            raise PermissionDeniedException("User already belongs to the target tenant")

        if user.roles:
            await self.repo.remove_roles(user, *[role.id for role in user.roles])

        user = await self.repo.update(user, tenant_id=schema_in.tenant_id)

        return UserOut.model_validate(user)
