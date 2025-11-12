from typing import Awaitable, Callable, Sequence

from pydantic import BaseModel

from src.core.database import Base
from src.core.exceptions import NotFoundException, ValidationException
from src.repositories.abc import ResourceRepositoryABC
from src.repositories.repository_manager import RepositoryManager
from src.schemas.common import PageQueryParams, PaginatedResponse


class BaseService:  # pylint: disable=too-few-public-methods
    repos: RepositoryManager

    def __init__(self, repos: RepositoryManager):
        self.repos = repos


class ResourceService[
    ResourceRepositoryType: ResourceRepositoryABC,  # pylint: disable=invalid-name
    BaseType: Base,  # pylint: disable=invalid-name
    SchemaInType: BaseModel,  # pylint: disable=invalid-name
    SchemaOutType: BaseModel,  # pylint: disable=invalid-name
](BaseService):
    repo: ResourceRepositoryType

    async def get(self, identifier: int, include_deleted: bool = False) -> BaseType:
        if rs := await self.repo.get(identifier, include_deleted=include_deleted):
            return rs

        raise NotFoundException(
            f"{self.repo.model.__name__} not found. [{identifier=}]"
        )

    async def get_all(self, include_deleted: bool = False) -> Sequence[BaseType]:
        return await self.repo.get_all(include_deleted=include_deleted)

    async def paginate(
        self,
        schema_out: type[SchemaOutType],
        page_query_params: PageQueryParams,
        include_deleted: bool = False,
    ) -> PaginatedResponse[SchemaOutType]:
        try:
            items, total = await self.repo.paginate(
                sort=page_query_params.sort,
                filters=page_query_params.filters,
                page_size=page_query_params.page_size,
                page_number=page_query_params.page_number,
                include_deleted=include_deleted,
            )
            return PaginatedResponse(
                items=[schema_out.model_validate(item) for item in items],
                page_number=page_query_params.page_number,
                page_size=page_query_params.page_size,
                total=total,
            )
        except ValueError as exc:
            raise ValidationException(exc) from exc

    async def create(
        self,
        schema_in: SchemaInType,
        validation_callback: Callable[[], Awaitable] | None = None,
    ) -> BaseType:
        if validation_callback:
            await validation_callback()

        return await self.repo.create(**schema_in.model_dump())

    async def update(
        self,
        identifier: int,
        schema_in: SchemaInType,
        validation_callback: Callable[[], Awaitable] | None = None,
    ) -> BaseType:
        if model := await self.repo.get(identifier):
            if validation_callback:
                await validation_callback()

            return await self.repo.update(model, **schema_in.model_dump())

        raise NotFoundException(
            f"{self.repo.model.__name__} not found. [{identifier=}]"
        )

    async def delete(
        self,
        identifier: int,
        validation_callback: Callable[[], Awaitable] | None = None,
        include_deleted: bool = False,
    ) -> None:
        if model := await self.repo.get(identifier):
            if validation_callback:
                await validation_callback()

            if include_deleted is False:
                await self.repo.delete(model)
            else:
                await self.repo.force_delete(model)

            return

        raise NotFoundException(
            f"{self.repo.model.__name__} not found. [{identifier=}]"
        )
