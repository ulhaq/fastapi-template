from datetime import UTC, datetime

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.refresh_token import RefreshToken
from src.models.user import User


class RefreshTokenRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create(
        self, user: User, hashed_token: str, expires_at: datetime
    ) -> RefreshToken:
        instance = RefreshToken(
            user_id=user.id, token=hashed_token, expires_at=expires_at
        )
        self.db.add(instance)
        await self.db.flush()
        await self.db.refresh(instance)
        return instance

    async def get_by_user(self, user: User) -> RefreshToken | None:
        stmt = (
            select(RefreshToken)
            .where(RefreshToken.user_id == user.id)
            .where(RefreshToken.expires_at > datetime.now(UTC))
        )
        rs = await self.db.execute(stmt)
        return rs.unique().scalar_one_or_none()

    async def delete_by_user(self, user: User) -> None:
        stmt = delete(RefreshToken).where(RefreshToken.user_id == user.id)
        await self.db.execute(stmt)
