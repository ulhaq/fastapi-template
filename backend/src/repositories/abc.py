from abc import ABC, abstractmethod
from collections.abc import Sequence
from typing import Any

from src.models.mixins import ResourceModel


class RepositoryABC[ModelType](ABC):
    model: type[ModelType]
    db: Any

    def __init__(self, model: type[ModelType], db: Any) -> None:
        self.model = model
        self.db = db


class ResourceRepositoryABC[ModelType](RepositoryABC[ModelType], ABC):
    @abstractmethod
    async def get_one(
        self, identifier: int, include_deleted: bool = False
    ) -> ModelType: ...

    @abstractmethod
    async def get(
        self, identifier: int, include_deleted: bool = False
    ) -> ModelType | None: ...

    @abstractmethod
    async def get_one_by_name(
        self, name: str, include_deleted: bool = False
    ) -> ModelType | None: ...

    @abstractmethod
    async def get_all(self, include_deleted: bool = False) -> Sequence[ModelType]: ...

    @abstractmethod
    async def filter_by(
        self, include_deleted: bool = False, **kwargs: Any
    ) -> Sequence[ModelType]: ...

    @abstractmethod
    async def filter_by_ids(
        self, identifiers: list[int], include_deleted: bool = False
    ) -> Sequence[ModelType]: ...

    @abstractmethod
    async def exists(self, identifier: int, include_deleted: bool = False) -> bool: ...

    @abstractmethod
    async def create(self, **kwargs: Any) -> ModelType: ...

    @abstractmethod
    async def update(self, model: ModelType, **kwargs: Any) -> ModelType: ...

    @abstractmethod
    async def force_delete(self, model: ModelType) -> None: ...

    @abstractmethod
    async def paginate(
        self,
        sort: list[str],
        filters: dict[str, dict],
        page_size: int,
        page_number: int,
        include_deleted: bool = False,
    ) -> tuple[Sequence[ModelType], int]: ...

    @abstractmethod
    async def get_total(
        self, *filter_expressions: Any, include_deleted: bool = False
    ) -> int: ...


class SoftDeleteRepositoryABC[ModelType: ResourceModel](
    ResourceRepositoryABC[ModelType], ABC
):
    @abstractmethod
    async def delete(self, model: ModelType) -> None: ...

    @abstractmethod
    async def restore(self, model: ModelType) -> ModelType: ...
