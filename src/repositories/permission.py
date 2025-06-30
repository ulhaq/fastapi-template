from abc import ABC

from sqlalchemy.ext.asyncio import AsyncSession

from src.models.permission import Permission
from src.repositories.abc import ResourceRepositoryABC
from src.repositories.base import SQLResourceRepository


class PermissionRepositoryABC(ResourceRepositoryABC[Permission], ABC): ...


class PermissionRepository(SQLResourceRepository[Permission], PermissionRepositoryABC):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(Permission, db)
