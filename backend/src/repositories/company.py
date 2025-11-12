from abc import ABC

from sqlalchemy.ext.asyncio import AsyncSession

from src.models.company import Company
from src.repositories.abc import ResourceRepositoryABC
from src.repositories.base import SQLResourceRepository


class CompanyRepositoryABC(ResourceRepositoryABC[Company], ABC): ...


class CompanyRepository(SQLResourceRepository[Company], CompanyRepositoryABC):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(Company, db)
