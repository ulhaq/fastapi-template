from typing import Annotated

from fastapi import Depends

from src.core.dependencies import authenticate
from src.core.exceptions import AlreadyExistsException, PermissionDeniedException
from src.core.security import Auth
from src.models.tenant import Tenant
from src.repositories.repository_manager import RepositoryManager
from src.repositories.tenant import TenantRepository
from src.schemas.common import PageQueryParams, PaginatedResponse
from src.schemas.tenant import TenantBase, TenantOut, TenantPatch
from src.services.base import ResourceService


class TenantService(
    ResourceService[TenantRepository, Tenant, TenantBase | TenantPatch, TenantOut]
):
    current_user: Auth

    def __init__(
        self,
        repos: Annotated[RepositoryManager, Depends()],
        current_user: Annotated[Auth, Depends(authenticate)],
    ) -> None:
        self.repo = repos.tenant
        self.current_user = current_user
        super().__init__(repos)

    async def get(self, identifier: int, include_deleted: bool = False) -> Tenant:
        if identifier != self.current_user.tenant_id:
            raise PermissionDeniedException(
                "You are not allowed to access other tenants"
            )
        return await super().get(identifier, include_deleted=include_deleted)

    async def paginate(
        self,
        schema_out: type[TenantOut],
        page_query_params: PageQueryParams,
        include_deleted: bool = False,
    ) -> PaginatedResponse[TenantOut]:
        tenant = await self.get(
            self.current_user.tenant_id, include_deleted=include_deleted
        )
        items = (
            [schema_out.model_validate(tenant)]
            if page_query_params.page_number == 1
            else []
        )
        return PaginatedResponse(
            items=items,
            page_number=page_query_params.page_number,
            page_size=page_query_params.page_size,
            total=1,
        )

    async def create_tenant(self, schema_in: TenantBase) -> TenantOut:
        async def validate() -> None:
            if await self.repo.get_one_by_name(schema_in.name):
                raise AlreadyExistsException(
                    f"Tenant already exists. [name={schema_in.name}]"
                )

        return TenantOut.model_validate(await super().create(schema_in, validate))

    async def update_tenant(self, identifier: int, schema_in: TenantBase) -> TenantOut:
        async def validate() -> None:
            existing_tenant = await self.repo.get_one_by_name(schema_in.name)

            if existing_tenant and existing_tenant.id != identifier:
                raise AlreadyExistsException(
                    f"Tenant already exists. [name={schema_in.name}]"
                )

        return TenantOut.model_validate(
            await super().update(identifier, schema_in, validate)
        )

    async def patch_tenant(self, identifier: int, schema_in: TenantPatch) -> TenantOut:
        async def validate() -> None:
            if schema_in.name:
                existing_tenant = await self.repo.get_one_by_name(schema_in.name)
                if existing_tenant and existing_tenant.id != identifier:
                    raise AlreadyExistsException(
                        f"Tenant already exists. [name={schema_in.name}]"
                    )

        return TenantOut.model_validate(
            await super().patch(identifier, schema_in, validate)
        )

    async def get_tenant(self, identifier: int) -> TenantOut:
        return TenantOut.model_validate(await self.get(identifier))

    async def delete_tenant(self, identifier: int, force_delete: bool = False) -> None:
        await super().delete(identifier, force_delete=force_delete)
