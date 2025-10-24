from typing import Annotated

from fastapi import Depends

from src.core.exceptions import AlreadyExistsException
from src.core.security import get_current_user
from src.models.role import Role
from src.repositories.repository_manager import RepositoryManager
from src.repositories.role import RoleRepository
from src.schemas.common import PageQueryParams, PaginatedResponse
from src.schemas.role import RoleIn, RoleOut, RolePermissionIn
from src.services.base import ResourceService


class RoleService(ResourceService[RoleRepository, Role, RoleIn, RoleOut]):
    def __init__(self, repos: Annotated[RepositoryManager, Depends()]) -> None:
        self.repo = repos.role
        super().__init__(repos)

    async def paginate(
        self, schema_out: type[RoleOut], page_query_params: PageQueryParams
    ) -> PaginatedResponse[RoleOut]:
        get_current_user().authorize("read_role")

        return await super().paginate(
            schema_out=schema_out, page_query_params=page_query_params
        )

    async def create_role(self, schema_in: RoleIn) -> RoleOut:
        async def validate() -> None:
            if await self.repo.get_one_by_name(schema_in.name):
                raise AlreadyExistsException(
                    f"Role already exists. [name={schema_in.name}]"
                )

        get_current_user().authorize("create_role")

        return RoleOut.model_validate(await super().create(schema_in, validate))

    async def update_role(self, identifier: int, schema_in: RoleIn) -> RoleOut:
        async def validate() -> None:
            existing_role = await self.repo.get_one_by_name(schema_in.name)

            if existing_role and existing_role.id != identifier:
                raise AlreadyExistsException(
                    f"Role already exists. [name={schema_in.name}]"
                )

        get_current_user().authorize("update_role")

        return RoleOut.model_validate(
            await super().update(identifier, schema_in, validate)
        )

    async def get_role(self, identifier: int) -> RoleOut:
        get_current_user().authorize("read_role")

        return RoleOut.model_validate(await super().get(identifier))

    async def delete_role(self, identifier: int) -> None:
        get_current_user().authorize("delete_role")

        await super().delete(identifier)

    async def manage_permissions(
        self, identifier: int, schema_in: RolePermissionIn
    ) -> RoleOut:
        get_current_user().authorize("manage_role_permission")

        role = await self.get(identifier)

        current_permissions = {permission.id for permission in role.permissions}
        schema_in_permission_ids = set(schema_in.permission_ids)

        if permissions_to_add := schema_in_permission_ids - current_permissions:
            await self.repo.add_permissions(role, *permissions_to_add)

        if permissions_to_remove := current_permissions - schema_in_permission_ids:
            await self.repo.remove_permissions(role, *permissions_to_remove)

        return RoleOut.model_validate(role)
