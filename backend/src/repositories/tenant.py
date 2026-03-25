from abc import ABC

from sqlalchemy.ext.asyncio import AsyncSession

from src.models.tenant import Tenant
from src.repositories.abc import ResourceRepositoryABC
from src.repositories.base import SQLResourceRepository


class TenantRepositoryABC(ResourceRepositoryABC[Tenant], ABC): ...


class TenantRepository(SQLResourceRepository[Tenant], TenantRepositoryABC):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(Tenant, db)
