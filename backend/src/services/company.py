from typing import Annotated

from fastapi import Depends

from src.core.exceptions import AlreadyExistsException
from src.core.security import get_current_user
from src.models.company import Company
from src.repositories.company import CompanyRepository
from src.repositories.repository_manager import RepositoryManager
from src.schemas.common import PageQueryParams, PaginatedResponse
from src.schemas.company import CompanyBase, CompanyOut
from src.services.base import ResourceService


class CompanyService(
    ResourceService[CompanyRepository, Company, CompanyBase, CompanyOut]
):
    def __init__(self, repos: Annotated[RepositoryManager, Depends()]) -> None:
        self.repo = repos.company
        super().__init__(repos)

    async def paginate(
        self,
        schema_out: type[CompanyOut],
        page_query_params: PageQueryParams,
        include_deleted: bool = False,
    ) -> PaginatedResponse[CompanyOut]:
        get_current_user().authorize("read_company")

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

        get_current_user().authorize("create_company")

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

        get_current_user().authorize("update_company")

        return CompanyOut.model_validate(
            await super().update(identifier, schema_in, validate)
        )

    async def get_company(self, identifier: int) -> CompanyOut:
        get_current_user().authorize("read_company")

        return CompanyOut.model_validate(await super().get(identifier))

    async def delete_company(self, identifier: int, force_delete: bool = False) -> None:
        get_current_user().authorize("delete_company")

        await super().delete(identifier, force_delete=force_delete)
