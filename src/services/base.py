from typing import Awaitable, Callable, Generic, Sequence, TypeVar

from pydantic import BaseModel

from src.core.database import Base
from src.core.exceptions import NotFoundException, ValidationException
from src.repositories.base import ResourceRepository
from src.repositories.repository_manager import RepositoryManager
from src.schemas.common import Filters, PaginatedResponse


class BaseService:
    repos: RepositoryManager

    def __init__(self, repos: RepositoryManager):
        self.repos = repos


ResourceRepositoryType = TypeVar("ResourceRepositoryType", bound=ResourceRepository)  # pylint: disable=invalid-name
BaseType = TypeVar("BaseType", bound=Base)  # pylint: disable=invalid-name
SchemaInType = TypeVar("SchemaInType", bound=BaseModel)  # pylint: disable=invalid-name
SchemaOutType = TypeVar("SchemaOutType", bound=BaseModel)  # pylint: disable=invalid-name


class ResourceService(
    BaseService, Generic[ResourceRepositoryType, BaseType, SchemaInType, SchemaOutType]
):
    repo: ResourceRepositoryType

    async def get(self, identifier: int) -> BaseType:
        if rs := await self.repo.get(identifier):
            return rs

        raise NotFoundException(
            f"{self.repo.model.__name__} not found. [{identifier=}]"
        )

    async def get_all(self) -> Sequence[BaseType]:
        return await self.repo.get_all()

    async def paginate(
        self,
        schema_out: type[SchemaOutType],
        sort: list[str],
        filters: Filters,
        page_size: int,
        page_number: int,
    ) -> PaginatedResponse[SchemaOutType]:
        try:
            items, total = await self.repo.paginate(
                sort=sort,
                filters=filters.filters,
                page_size=page_size,
                page_number=page_number,
            )
            return PaginatedResponse(
                items=[schema_out.model_validate(item) for item in items],
                page_number=page_number,
                page_size=page_size,
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
    ) -> None:
        if model := await self.repo.get(identifier):
            if validation_callback:
                await validation_callback()

            await self.repo.delete(model)
