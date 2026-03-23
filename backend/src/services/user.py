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
from src.enums import ErrorCode
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
        self.current_user = current_user
        super().__init__(repos)

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

    async def create_user(self, schema_in: UserIn, schedule_task: Callable) -> UserOut:
        async def validate() -> None:
            if await self.repo.get_by_email(schema_in.email):
                raise AlreadyExistsException(
                    f"User already exists. [email={schema_in.email}]",
                    error_code=ErrorCode.EMAIL_ALREADY_EXISTS,
                )

            if not await self.repos.company.get(schema_in.company_id):
                raise NotFoundException(
                    f"Company not found. [id={schema_in.company_id}]",
                    error_code=ErrorCode.RESOURCE_NOT_FOUND,
                )

        hashed_pw = hash_secret(schema_in.password)
        await validate()

        user = await self.repo.create(
            name=schema_in.name,
            email=schema_in.email,
            password=hashed_pw,
            company_id=schema_in.company_id,
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
        await super().delete(identifier)

    async def manage_roles(self, identifier: int, schema_in: UserRoleIn) -> UserOut:
        if self.current_user.id == identifier:
            raise PermissionDeniedException(
                "You are not allowed to manage your own roles"
            )

        user = await self.get(identifier)

        current_roles = {role.id for role in user.roles}
        schema_in_role_ids = set(schema_in.role_ids)

        if roles_to_add := schema_in_role_ids - current_roles:
            await self.repo.add_roles(user, *roles_to_add)

        if roles_to_remove := current_roles - schema_in_role_ids:
            await self.repo.remove_roles(user, *roles_to_remove)

        return UserOut.model_validate(user)
