from abc import ABC, abstractmethod
from typing import Any, Sequence

from sqlalchemy import BinaryExpression

from src.core.database import Base

# pylint: disable=invalid-name,too-few-public-methods


class RepositoryABC(ABC): ...


class ResourceRepositoryABC[ModelType: Base](RepositoryABC, ABC):
    @abstractmethod
    async def get_one(self, identifier: int) -> ModelType: ...

    @abstractmethod
    async def get(self, identifier: int) -> ModelType | None: ...

    @abstractmethod
    async def get_all(self) -> Sequence[ModelType]: ...

    @abstractmethod
    async def get_one_by_name(self, name: str) -> ModelType | None: ...

    @abstractmethod
    async def filter_by(self, **kwargs: Any) -> Sequence[ModelType]: ...

    @abstractmethod
    async def filter_by_ids(self, identifiers: list[int]) -> Sequence[ModelType]: ...

    @abstractmethod
    async def exists(self, identifier: int) -> bool: ...

    @abstractmethod
    async def create(self, **kwargs: Any) -> ModelType: ...

    @abstractmethod
    async def update(self, model: ModelType, **kwargs: Any) -> ModelType: ...

    @abstractmethod
    async def delete(self, model: ModelType) -> None: ...

    @abstractmethod
    async def paginate(
        self,
        sort: list[str],
        filters: dict[str, dict],
        page_size: int,
        page_number: int,
    ) -> tuple[Sequence[ModelType], int]: ...

    @abstractmethod
    async def get_total(self, *filter_expressions: BinaryExpression) -> int: ...

    @abstractmethod
    async def add_relationship(
        self,
        target_model: ModelType,
        related_model: Any,
        relationship_attr: str,
        *related_ids: int,
    ) -> None: ...

    @abstractmethod
    async def remove_relationship(
        self, target_model: ModelType, relationship_attr: str, *related_ids: int
    ) -> None: ...
