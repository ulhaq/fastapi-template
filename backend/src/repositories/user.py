from abc import ABC, abstractmethod
from datetime import UTC, datetime

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.password_reset_token import PasswordResetToken
from src.models.role import Role
from src.models.user import User
from src.repositories.abc import ResourceRepositoryABC
from src.repositories.base import SQLResourceRepository


class UserRepositoryABC(ResourceRepositoryABC[User], ABC):
    @abstractmethod
    async def get_by_email(self, email: str) -> User | None: ...

    @abstractmethod
    async def add_roles(
        self, user: User, *role_ids: int, commit: bool = True
    ) -> None: ...

    @abstractmethod
    async def remove_roles(
        self, user: User, *role_ids: int, commit: bool = True
    ) -> None: ...

    @abstractmethod
    async def get_password_reset_token(
        self, user: User
    ) -> PasswordResetToken | None: ...

    @abstractmethod
    async def create_password_reset_token(
        self, *, commit: bool = True, user: User, token: str
    ) -> PasswordResetToken: ...

    @abstractmethod
    async def delete_password_reset_token(
        self, *, commit: bool = True, user: User
    ) -> None: ...


class UserRepository(SQLResourceRepository[User], UserRepositoryABC):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(User, db)

    async def get_by_email(self, email: str) -> User | None:
        stmt = select(User).where(User.email == email)
        rs = await self.db.execute(stmt)
        return rs.unique().scalar_one_or_none()

    async def add_roles(self, user: User, *role_ids: int, commit: bool = True) -> None:
        await self.add_relationship(user, Role, "roles", *role_ids, commit=commit)

    async def remove_roles(
        self, user: User, *role_ids: int, commit: bool = True
    ) -> None:
        await self.remove_relationship(user, "roles", *role_ids, commit=commit)

    async def get_password_reset_token(self, user: User) -> PasswordResetToken | None:
        stmt = select(PasswordResetToken).filter(PasswordResetToken.user_id == user.id)

        rs = await self.db.execute(stmt)
        return rs.unique().scalar_one_or_none()

    async def create_password_reset_token(
        self, *, commit: bool = True, user: User, token: str
    ) -> PasswordResetToken:
        await self.delete_password_reset_token(commit=commit, user=user)

        instance = PasswordResetToken(
            user_id=user.id, token=token, created_at=datetime.now(UTC)
        )

        self.db.add(instance)

        return await self.save(instance, commit=commit)

    async def delete_password_reset_token(
        self, *, commit: bool = True, user: User
    ) -> None:
        stmt = delete(PasswordResetToken).filter(PasswordResetToken.user_id == user.id)

        await self.db.execute(stmt)

        await self.save(commit=commit)
