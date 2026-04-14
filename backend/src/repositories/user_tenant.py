from collections.abc import Sequence
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.user_tenant import UserTenant
from src.repositories.base import SQLResourceRepository


class UserTenantRepository(SQLResourceRepository[UserTenant]):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(UserTenant, db)

    async def get_by_user_and_tenant(
        self, user_id: int, tenant_id: int
    ) -> UserTenant | None:
        stmt = select(UserTenant).where(
            UserTenant.user_id == user_id,
            UserTenant.tenant_id == tenant_id,
        )
        rs = await self.db.execute(stmt)
        return rs.scalar_one_or_none()

    async def get_all_for_user(self, user_id: int) -> Sequence[UserTenant]:
        stmt = (
            select(UserTenant)
            .where(UserTenant.user_id == user_id)
            .order_by(
                UserTenant.last_active_at.desc().nulls_last(),
                UserTenant.created_at.asc(),
            )
        )
        rs = await self.db.execute(stmt)
        return rs.scalars().all()

    async def get_active_tenant_for_user(self, user_id: int) -> UserTenant | None:
        """
        Return the most-recently-active membership row.

        Falls back to earliest created if none has ever been active.
        Returns None if the user has no tenant memberships.
        """
        rows = await self.get_all_for_user(user_id)
        return rows[0] if rows else None

    async def update_last_active(self, membership: UserTenant) -> UserTenant:
        return await self.update(membership, last_active_at=datetime.now(UTC))
