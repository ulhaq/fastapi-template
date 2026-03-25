from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.repositories.permission import PermissionRepository
from src.repositories.refresh_token import RefreshTokenRepository
from src.repositories.role import RoleRepository
from src.repositories.tenant import TenantRepository
from src.repositories.user import UserRepository


class RepositoryManager:
    db: AsyncSession

    def __init__(self, db: Annotated[AsyncSession, Depends(get_db)]) -> None:
        self.db = db
        self._tenant: TenantRepository | None = None
        self._user: UserRepository | None = None
        self._role: RoleRepository | None = None
        self._permission: PermissionRepository | None = None
        self._refresh_token: RefreshTokenRepository | None = None

    @property
    def tenant(self) -> TenantRepository:
        if self._tenant is None:
            self._tenant = TenantRepository(self.db)
        return self._tenant

    @property
    def user(self) -> UserRepository:
        if self._user is None:
            self._user = UserRepository(self.db)
        return self._user

    @property
    def role(self) -> RoleRepository:
        if self._role is None:
            self._role = RoleRepository(self.db)
        return self._role

    @property
    def permission(self) -> PermissionRepository:
        if self._permission is None:
            self._permission = PermissionRepository(self.db)
        return self._permission

    @property
    def refresh_token(self) -> RefreshTokenRepository:
        if self._refresh_token is None:
            self._refresh_token = RefreshTokenRepository(self.db)
        return self._refresh_token

    async def commit(self) -> None:
        await self.db.commit()
