from typing import Annotated

from fastapi import Depends

from src.core.dependencies import authenticate
from src.core.exceptions import AlreadyExistsException
from src.core.security import Auth
from src.models.role import Role
from src.repositories.repository_manager import RepositoryManager
from src.repositories.role import RoleRepository
from src.schemas.common import PageQueryParams, PaginatedResponse
from src.schemas.role import RoleIn, RoleOut, RolePatch, RolePermissionIn
from src.services.base import ResourceService


class RoleService(ResourceService[RoleRepository, Role, RoleIn | RolePatch, RoleOut]):
    current_user: Auth

    def __init__(
        self,
        repos: Annotated[RepositoryManager, Depends()],
        current_user: Annotated[Auth, Depends(authenticate)],
    ) -> None:
        self.repo = repos.role
        self.repo.set_company_scope(current_user.company_id)
        self.current_user = current_user
        super().__init__(repos)

    async def paginate(
        self,
        schema_out: type[RoleOut],
        page_query_params: PageQueryParams,
        include_deleted: bool = False,
    ) -> PaginatedResponse[RoleOut]:
        return await super().paginate(
            schema_out=schema_out,
            page_query_params=page_query_params,
            include_deleted=include_deleted,
        )

    async def create_role(self, schema_in: RoleIn) -> RoleOut:
        async def validate() -> None:
            if await self.repo.get_one_by_name(schema_in.name):
                raise AlreadyExistsException(
                    f"Role already exists. [name={schema_in.name}]"
                )

        return RoleOut.model_validate(await super().create(schema_in, validate))

    async def update_role(self, identifier: int, schema_in: RoleIn) -> RoleOut:
        async def validate() -> None:
            existing_role = await self.repo.get_one_by_name(schema_in.name)

            if existing_role and existing_role.id != identifier:
                raise AlreadyExistsException(
                    f"Role already exists. [name={schema_in.name}]"
                )

        return RoleOut.model_validate(
            await super().update(identifier, schema_in, validate)
        )

    async def patch_role(self, identifier: int, schema_in: RolePatch) -> RoleOut:
        async def validate() -> None:
            if schema_in.name:
                existing_role = await self.repo.get_one_by_name(schema_in.name)
                if existing_role and existing_role.id != identifier:
                    raise AlreadyExistsException(
                        f"Role already exists. [name={schema_in.name}]"
                    )

        return RoleOut.model_validate(
            await super().patch(identifier, schema_in, validate)
        )

    async def get_role(self, identifier: int, include_deleted: bool = False) -> RoleOut:
        return RoleOut.model_validate(
            await super().get(identifier, include_deleted=include_deleted)
        )

    async def delete_role(self, identifier: int, force_delete: bool = False) -> None:
        await super().delete(identifier, force_delete=force_delete)

    async def manage_permissions(
        self, identifier: int, schema_in: RolePermissionIn
    ) -> RoleOut:
        role = await self.get(identifier)

        current_permissions = {permission.id for permission in role.permissions}
        schema_in_permission_ids = set(schema_in.permission_ids)

        if permissions_to_add := schema_in_permission_ids - current_permissions:
            await self.repo.add_permissions(role, *permissions_to_add)

        if permissions_to_remove := current_permissions - schema_in_permission_ids:
            await self.repo.remove_permissions(role, *permissions_to_remove)

        return RoleOut.model_validate(role)
