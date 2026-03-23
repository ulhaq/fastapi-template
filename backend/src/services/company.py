from typing import Annotated

from fastapi import Depends

from src.core.exceptions import AlreadyExistsException
from src.models.company import Company
from src.repositories.company import CompanyRepository
from src.repositories.repository_manager import RepositoryManager
from src.schemas.common import PageQueryParams, PaginatedResponse
from src.schemas.company import CompanyBase, CompanyOut, CompanyPatch
from src.services.base import ResourceService


class CompanyService(
    ResourceService[CompanyRepository, Company, CompanyBase | CompanyPatch, CompanyOut]
):
    def __init__(
        self,
        repos: Annotated[RepositoryManager, Depends()],
    ) -> None:
        self.repo = repos.company
        super().__init__(repos)

    async def paginate(
        self,
        schema_out: type[CompanyOut],
        page_query_params: PageQueryParams,
        include_deleted: bool = False,
    ) -> PaginatedResponse[CompanyOut]:
        return await super().paginate(
            schema_out=schema_out,
            page_query_params=page_query_params,
            include_deleted=include_deleted,
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
        return CompanyOut.model_validate(await super().get(identifier))

    async def delete_company(self, identifier: int, force_delete: bool = False) -> None:
        await super().delete(identifier, force_delete=force_delete)
