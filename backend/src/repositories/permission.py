from abc import ABC
from typing import ClassVar

from sqlalchemy.ext.asyncio import AsyncSession

from src.models.permission import Permission
from src.repositories.abc import SoftDeleteRepositoryABC
from src.repositories.base import SoftDeleteRepository


class PermissionRepositoryABC(SoftDeleteRepositoryABC[Permission], ABC): ...


class PermissionRepository(SoftDeleteRepository[Permission], PermissionRepositoryABC):
    search_fields: ClassVar[list[str]] = ["name", "description"]

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(Permission, db)
