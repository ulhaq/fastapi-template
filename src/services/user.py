from typing import Annotated

from fastapi import Depends

from src.core.exceptions import AlreadyExistsException
from src.core.security import get_current_user, hash_password
from src.models.user import User
from src.repositories.repository_manager import RepositoryManager
from src.repositories.user import UserRepository
from src.schemas.user import UserIn, UserOut, UserRoleIn
from src.services.base import ResourceService


class UserService(ResourceService[UserRepository, User, UserIn, UserOut]):
    def __init__(self, repos: Annotated[RepositoryManager, Depends()]):
        self.repo = repos.user
        super().__init__(repos)

    async def get_authenticated_user(self) -> UserOut:
        return UserOut.model_validate(await self.get(get_current_user().id))

    async def create_user(self, schema_in: UserIn) -> UserOut:
        async def validate() -> None:
            if await self.repo.get_by_email(schema_in.email):
                raise AlreadyExistsException(
                    detail=f"User already exists. [email={schema_in.email}]"
                )

        get_current_user().authorize("create_user")

        schema_in.password = hash_password(schema_in.password)

        return UserOut.model_validate(await super().create(schema_in, validate))

    async def delete_user(self, identifier: int) -> None:
        get_current_user().authorize("delete_user")

        await super().delete(identifier)

    async def manage_roles(self, identifier: int, schema_in: UserRoleIn) -> UserOut:
        get_current_user().authorize("manage_user_role")

        user = await self.get(identifier)

        current_roles = {role.id for role in user.roles}
        schema_in_role_ids = set(schema_in.role_ids)

        if roles_to_add := schema_in_role_ids - current_roles:
            await self.repo.add_roles(user, *roles_to_add)

        if roles_to_remove := current_roles - schema_in_role_ids:
            await self.repo.remove_roles(user, *roles_to_remove)

        return UserOut.model_validate(user)
