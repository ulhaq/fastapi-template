from abc import ABC, abstractmethod
from typing import Any, Sequence

from sqlalchemy import BinaryExpression
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import Base

# pylint: disable=invalid-name,too-few-public-methods


class RepositoryABC[ModelType: Base](ABC):
    model: type[ModelType]
    db: AsyncSession

    def __init__(self, model: type[ModelType], db: AsyncSession) -> None:
        self.model = model
        self.db = db


class ResourceRepositoryABC[ModelType: Base](RepositoryABC[ModelType], ABC):
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
    async def create(self, *, commit: bool = True, **kwargs: Any) -> ModelType: ...

    @abstractmethod
    async def update(
        self, model: ModelType, *, commit: bool = True, **kwargs: Any
    ) -> ModelType: ...

    @abstractmethod
    async def delete(self, model: ModelType, *, commit: bool = True) -> None: ...

    @abstractmethod
    async def force_delete(self, model: ModelType, *, commit: bool = True) -> None: ...

    @abstractmethod
    async def paginate(  # pylint: disable=too-many-arguments,too-many-positional-arguments
        self,
        sort: list[str],
        filters: dict[str, dict],
        page_size: int,
        page_number: int,
        include_deleted: bool = False,
    ) -> tuple[Sequence[ModelType], int]: ...

    @abstractmethod
    async def get_total(
        self, *filter_expressions: BinaryExpression, include_deleted: bool = False
    ) -> int: ...

    @abstractmethod
    async def add_relationship(
        self,
        target_model: ModelType,
        related_model: Any,
        relationship_attr: str,
        *related_ids: int,
        commit: bool = True,
    ) -> None: ...

    @abstractmethod
    async def remove_relationship(
        self,
        target_model: ModelType,
        relationship_attr: str,
        *related_ids: int,
        commit: bool = True,
    ) -> None: ...
