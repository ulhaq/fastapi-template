from typing import Annotated

from fastapi import Depends
from fastapi.security import OAuth2PasswordRequestForm

from src.core.exceptions import AlreadyExistsException, NotAuthenticatedException
from src.core.security import (
    Token,
    authenticate_user,
    create_access_token,
    hash_password,
)
from src.models.auth import Permission, Role
from src.models.user import User
from src.repositories.auth import PermissionRepository, RoleRepository
from src.repositories.repository_manager import RepositoryManager
from src.schemas.auth import (
    PermissionIn,
    PermissionOut,
    RoleIn,
    RoleOut,
    RolePermissionIn,
)
from src.schemas.user import UserIn
from src.services.base import BaseService, ResourceService


class AuthService(BaseService):
    def __init__(self, repos: Annotated[RepositoryManager, Depends()]) -> None:
        super().__init__(repos)

    async def register_user(self, user_in: UserIn) -> User:
        if await self.repos.user.get_by_email(user_in.email):
            raise AlreadyExistsException(detail="Email is already registered.")

        user_in.password = hash_password(user_in.password)

        return await self.repos.user.create(**user_in.model_dump())

    async def get_access_token(self, auth_data: OAuth2PasswordRequestForm) -> Token:
        user = authenticate_user(
            auth_data, await self.repos.user.get_by_email(auth_data.username)
        )

        if not user:
            raise NotAuthenticatedException(
                detail="Authentication failed.", headers={"WWW-Authenticate": "Bearer"}
            )

        return Token(access_token=create_access_token(user))


class RoleService(ResourceService[RoleRepository, Role, RoleIn, RoleOut]):
    def __init__(self, repos: Annotated[RepositoryManager, Depends()]) -> None:
        self.repo = repos.role
        super().__init__(repos)

    async def create_role(self, schema_in: RoleIn) -> Role:
        async def validate():
            if await self.repo.get_one_by_name(schema_in.name):
                raise AlreadyExistsException(
                    detail=f"Role already exists. [name={schema_in.name}]"
                )

        return await super().create(schema_in, validate)

    async def update_role(self, identifier: int, schema_in: RoleIn) -> Role:
        async def validate():
            existing_role = await self.repo.get_one_by_name(schema_in.name)

            if existing_role and existing_role.id != identifier:
                raise AlreadyExistsException(
                    detail=f"Role already exists. [name={schema_in.name}]"
                )

        return await super().update(identifier, schema_in, validate)

    async def add_permissions(self, identifier: int, schema_in: RolePermissionIn):
        role = await self.get(identifier)

        await self.repo.add_permissions(role, *schema_in.permission_ids)

        return await self.repo.get_one(identifier)

    async def remove_permissions(self, identifier: int, schema_in: RolePermissionIn):
        role = await self.get(identifier)

        await self.repo.remove_permissions(role, *schema_in.permission_ids)

        return await self.repo.get_one(identifier)


class PermissionService(
    ResourceService[PermissionRepository, Permission, PermissionIn, PermissionOut]
):
    def __init__(self, repos: Annotated[RepositoryManager, Depends()]):
        self.repo = repos.permission
        super().__init__(repos)

    async def create_permission(self, schema_in: PermissionIn):
        async def validate():
            if await self.repo.get_one_by_name(schema_in.name):
                raise AlreadyExistsException(
                    detail=f"Permission already exists. [name={schema_in.name}]"
                )

        return await super().create(schema_in, validate)

    async def update_permission(
        self, identifier: int, schema_in: PermissionIn
    ) -> Permission:
        async def validate():
            existing_permission = await self.repo.get_one_by_name(schema_in.name)

            if existing_permission and existing_permission.id != identifier:
                raise AlreadyExistsException(
                    detail=f"Permission already exists. [name={schema_in.name}]"
                )

        return await super().update(identifier, schema_in, validate)
