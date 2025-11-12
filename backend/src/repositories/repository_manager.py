from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.repositories.company import CompanyRepository
from src.repositories.permission import PermissionRepository
from src.repositories.role import RoleRepository
from src.repositories.user import UserRepository


class RepositoryManager:
    db: AsyncSession

    def __init__(self, db: Annotated[AsyncSession, Depends(get_db)]) -> None:
        self.db = db

    @property
    def company(self) -> CompanyRepository:
        return CompanyRepository(self.db)

    @property
    def user(self) -> UserRepository:
        return UserRepository(self.db)

    @property
    def role(self) -> RoleRepository:
        return RoleRepository(self.db)

    @property
    def permission(self) -> PermissionRepository:
        return PermissionRepository(self.db)
