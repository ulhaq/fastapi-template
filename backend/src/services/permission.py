from typing import Annotated

from fastapi import Depends

from src.core.exceptions import AlreadyExistsException
from src.core.security import get_current_user
from src.models.permission import Permission
from src.repositories.permission import PermissionRepository
from src.repositories.repository_manager import RepositoryManager
from src.schemas.common import PageQueryParams, PaginatedResponse
from src.schemas.permission import PermissionIn, PermissionOut
from src.services.base import ResourceService


class PermissionService(
    ResourceService[PermissionRepository, Permission, PermissionIn, PermissionOut]
):
    def __init__(self, repos: Annotated[RepositoryManager, Depends()]):
        self.repo = repos.permission
        super().__init__(repos)

    async def paginate(
        self,
        schema_out: type[PermissionOut],
        page_query_params: PageQueryParams,
        include_deleted: bool = False,
    ) -> PaginatedResponse[PermissionOut]:
        get_current_user().authorize("read_permission")

        return await super().paginate(
            schema_out=schema_out,
            page_query_params=page_query_params,
            include_deleted=include_deleted,
        )

    async def create_permission(self, schema_in: PermissionIn) -> PermissionOut:
        async def validate() -> None:
            if await self.repo.get_one_by_name(schema_in.name):
                raise AlreadyExistsException(
                    f"Permission already exists. [name={schema_in.name}]"
                )

        get_current_user().authorize("create_permission")

        return PermissionOut.model_validate(await super().create(schema_in, validate))

    async def update_permission(
        self, identifier: int, schema_in: PermissionIn
    ) -> PermissionOut:
        async def validate() -> None:
            existing_permission = await self.repo.get_one_by_name(schema_in.name)

            if existing_permission and existing_permission.id != identifier:
                raise AlreadyExistsException(
                    f"Permission already exists. [name={schema_in.name}]"
                )

        get_current_user().authorize("update_permission")

        return PermissionOut.model_validate(
            await super().update(identifier, schema_in, validate)
        )

    async def get_permission(
        self, identifier: int, include_deleted: bool = False
    ) -> PermissionOut:
        get_current_user().authorize("read_permission")

        return PermissionOut.model_validate(
            await super().get(identifier, include_deleted=include_deleted)
        )

    async def delete_permission(
        self, identifier: int, force_delete: bool = False
    ) -> None:
        get_current_user().authorize("delete_permission")

        await super().delete(identifier, force_delete=force_delete)
