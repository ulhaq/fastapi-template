from abc import ABC, abstractmethod

from sqlalchemy.ext.asyncio import AsyncSession

from src.models.permission import Permission
from src.models.role import Role
from src.repositories.abc import ResourceRepositoryABC
from src.repositories.base import SQLResourceRepository


class RoleRepositoryABC(ResourceRepositoryABC[Role], ABC):
    @abstractmethod
    async def add_permissions(self, role: Role, *permission_ids: int) -> None: ...

    @abstractmethod
    async def remove_permissions(self, role: Role, *permission_ids: int) -> None: ...


class RoleRepository(SQLResourceRepository[Role], RoleRepositoryABC):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(Role, db)

    async def add_permissions(
        self, role: Role, *permission_ids: int, commit: bool = True
    ) -> None:
        await self.add_relationship(
            role, Permission, "permissions", *permission_ids, commit=commit
        )

    async def remove_permissions(
        self, role: Role, *permission_ids: int, commit: bool = True
    ) -> None:
        await self.remove_relationship(
            role, "permissions", *permission_ids, commit=commit
        )
