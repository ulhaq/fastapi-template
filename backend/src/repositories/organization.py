from abc import ABC

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.organization import Organization
from src.repositories.abc import ResourceRepositoryABC
from src.repositories.base import SQLResourceRepository


class OrganizationRepositoryABC(ResourceRepositoryABC[Organization], ABC): ...


class OrganizationRepository(
    SQLResourceRepository[Organization], OrganizationRepositoryABC
):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(Organization, db)

    async def get_by_external_customer_id(
        self, external_customer_id: str
    ) -> Organization | None:
        stmt = select(self.model).filter(
            self.model.external_customer_id == external_customer_id,
            self.model.deleted_at.is_(None),
        )
        rs = await self.db.execute(stmt)
        return rs.unique().scalar_one_or_none()

    async def get_by_external_customer_id_locked(
        self, external_customer_id: str
    ) -> Organization | None:
        """
        Like get_by_external_customer_id but acquires a row lock (SELECT FOR UPDATE).
        Use in webhook handlers to prevent concurrent
        processing on the same organization.
        """
        stmt = (
            select(self.model)
            .filter(
                self.model.external_customer_id == external_customer_id,
                self.model.deleted_at.is_(None),
            )
            .with_for_update()
        )
        rs = await self.db.execute(stmt)
        return rs.unique().scalar_one_or_none()
