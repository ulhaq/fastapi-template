from sqlalchemy.ext.asyncio import AsyncSession

from src.models.permission import Permission
from src.repositories.base import ResourceRepository


class PermissionRepository(ResourceRepository[Permission]):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(Permission, db)
