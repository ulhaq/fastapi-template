from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.role import Role
from src.models.user import User
from src.repositories.base import ResourceRepository


class UserRepository(ResourceRepository[User]):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(User, db)

    async def get_by_email(self, email: str) -> User | None:
        stmt = select(User).where(User.email == email)
        rs = await self.db.execute(stmt)
        return rs.unique().scalar_one_or_none()

    async def add_roles(self, user: User, *role_ids: int) -> None:
        await self.add_relationship(user, Role, "roles", *role_ids)

    async def remove_roles(self, user: User, *role_ids: int) -> None:
        await self.remove_relationship(user, "roles", *role_ids)
