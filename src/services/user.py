from typing import Annotated

from fastapi import Depends

from src.core.exceptions import AlreadyExistsException
from src.core.security import hash_password
from src.models.user import User
from src.repositories.repository_manager import RepositoryManager
from src.repositories.user import UserRepository
from src.schemas.user import UserIn, UserOut, UserRoleIn
from src.services.base import ResourceService


class UserService(ResourceService[UserRepository, User, UserIn, UserOut]):
    def __init__(self, repos: Annotated[RepositoryManager, Depends()]):
        self.repo = repos.user
        super().__init__(repos)

    async def create_user(self, schema_in: UserIn):
        async def validate():
            if await self.repo.get_by_email(schema_in.email):
                raise AlreadyExistsException(
                    detail=f"User already exists. [email={schema_in.email}]"
                )

        schema_in.password = hash_password(schema_in.password)

        return super().create(schema_in, validate)

    async def add_roles(self, identifier: int, schema_in: UserRoleIn):
        user = await self.get(identifier)

        await self.repo.add_roles(user, *schema_in.role_ids)

        return await self.repo.get(identifier)

    async def remove_roles(self, identifier: int, schema_in: UserRoleIn):
        user = await self.get(identifier)

        await self.repo.remove_roles(user, *schema_in.role_ids)

        return await self.repo.get(identifier)
