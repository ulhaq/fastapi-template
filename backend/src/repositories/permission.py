from abc import ABC

from sqlalchemy.ext.asyncio import AsyncSession

from src.models.permission import Permission
from src.repositories.abc import SoftDeleteRepositoryABC
from src.repositories.base import SoftDeleteRepository


class PermissionRepositoryABC(SoftDeleteRepositoryABC[Permission], ABC): ...


class PermissionRepository(SoftDeleteRepository[Permission], PermissionRepositoryABC):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(Permission, db)
