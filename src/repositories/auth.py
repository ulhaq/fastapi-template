from sqlalchemy.ext.asyncio import AsyncSession

from src.models.auth import Permission, Role
from src.repositories.base import ResourceRepository


class RoleRepository(ResourceRepository[Role]):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(Role, db)

    async def add_permissions(self, role: Role, *permission_ids: int) -> None:
        await self.add_relationship(role, Permission, "permissions", *permission_ids)

    async def remove_permissions(self, role: Role, *permission_ids: int) -> None:
        await self.remove_relationship(role, "permissions", *permission_ids)


class PermissionRepository(ResourceRepository[Permission]):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(Permission, db)
