from collections.abc import Awaitable, Callable, Sequence

from pydantic import BaseModel

from src.core.exceptions import NotFoundException, PlanFeatureUnavailableException
from src.enums import PlanFeature
from src.repositories.abc import ResourceRepositoryABC
from src.repositories.repository_manager import RepositoryManager
from src.schemas.common import PageQueryParams, PaginatedResponse


class BaseService:
    repos: RepositoryManager

    def __init__(self, repos: RepositoryManager):
        self.repos = repos

    async def _require_feature(
        self, feature: PlanFeature, organization_id: int
    ) -> None:
        features = await self.repos.plan_feature.get_features_for_organization(
            organization_id
        )
        if feature not in features:
            raise PlanFeatureUnavailableException


class ResourceService[
    ResourceRepositoryType: ResourceRepositoryABC,
    BaseType,
    SchemaInType: BaseModel,
    SchemaOutType: BaseModel,
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
        model = await self.get(identifier)

        if validation_callback:
            await validation_callback()

        return await self.repo.update(model, **schema_in.model_dump())

    async def patch(
        self,
        identifier: int,
        schema_in: SchemaInType,
        validation_callback: Callable[[], Awaitable] | None = None,
    ) -> BaseType:
        model = await self.get(identifier)

        if validation_callback:
            await validation_callback()

        return await self.repo.update(model, **schema_in.model_dump(exclude_unset=True))

    async def delete(
        self,
        identifier: int,
        validation_callback: Callable[[], Awaitable] | None = None,
        force_delete: bool = False,
    ) -> None:
        model = await self.get(identifier)

        if validation_callback:
            await validation_callback()

        if force_delete is False:
            await self.repo.delete(model)
        else:
            await self.repo.force_delete(model)
