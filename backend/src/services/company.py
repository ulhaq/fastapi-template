from typing import Annotated

from fastapi import Depends

from src.core.dependencies import authenticate
from src.core.exceptions import AlreadyExistsException, PermissionDeniedException
from src.core.security import Auth
from src.models.company import Company
from src.repositories.company import CompanyRepository
from src.repositories.repository_manager import RepositoryManager
from src.schemas.common import PageQueryParams, PaginatedResponse
from src.schemas.company import CompanyBase, CompanyOut, CompanyPatch
from src.services.base import ResourceService


class CompanyService(
    ResourceService[CompanyRepository, Company, CompanyBase | CompanyPatch, CompanyOut]
):
    current_user: Auth

    def __init__(
        self,
        repos: Annotated[RepositoryManager, Depends()],
        current_user: Annotated[Auth, Depends(authenticate)],
    ) -> None:
        self.repo = repos.company
        self.current_user = current_user
        super().__init__(repos)

    async def get(self, identifier: int, include_deleted: bool = False) -> Company:
        if identifier != self.current_user.company_id:
            raise PermissionDeniedException(
                "You are not allowed to access other companies"
            )
        return await super().get(identifier, include_deleted=include_deleted)

    async def paginate(
        self,
        schema_out: type[CompanyOut],
        page_query_params: PageQueryParams,
        include_deleted: bool = False,
    ) -> PaginatedResponse[CompanyOut]:
        company = await self.get(
            self.current_user.company_id, include_deleted=include_deleted
        )
        items = (
            [schema_out.model_validate(company)]
            if page_query_params.page_number == 1
            else []
        )
        return PaginatedResponse(
            items=items,
            page_number=page_query_params.page_number,
            page_size=page_query_params.page_size,
            total=1,
        )

    async def create_company(self, schema_in: CompanyBase) -> CompanyOut:
        async def validate() -> None:
            if await self.repo.get_one_by_name(schema_in.name):
                raise AlreadyExistsException(
                    f"Company already exists. [name={schema_in.name}]"
                )

        return CompanyOut.model_validate(await super().create(schema_in, validate))

    async def update_company(
        self, identifier: int, schema_in: CompanyBase
    ) -> CompanyOut:
        async def validate() -> None:
            existing_company = await self.repo.get_one_by_name(schema_in.name)

            if existing_company and existing_company.id != identifier:
                raise AlreadyExistsException(
                    f"Company already exists. [name={schema_in.name}]"
                )

        return CompanyOut.model_validate(
            await super().update(identifier, schema_in, validate)
        )

    async def patch_company(
        self, identifier: int, schema_in: CompanyPatch
    ) -> CompanyOut:
        async def validate() -> None:
            if schema_in.name:
                existing_company = await self.repo.get_one_by_name(schema_in.name)
                if existing_company and existing_company.id != identifier:
                    raise AlreadyExistsException(
                        f"Company already exists. [name={schema_in.name}]"
                    )

        return CompanyOut.model_validate(
            await super().patch(identifier, schema_in, validate)
        )

    async def get_company(self, identifier: int) -> CompanyOut:
        return CompanyOut.model_validate(await self.get(identifier))

    async def delete_company(self, identifier: int, force_delete: bool = False) -> None:
        await super().delete(identifier, force_delete=force_delete)
