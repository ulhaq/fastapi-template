from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.repositories.billing import (
    PlanPriceRepository,
    PlanRepository,
    SubscriptionRepository,
    WebhookEventRepository,
)
from src.repositories.permission import PermissionRepository
from src.repositories.refresh_token import RefreshTokenRepository
from src.repositories.role import RoleRepository
from src.repositories.tenant import TenantRepository
from src.repositories.user import UserRepository
from src.repositories.user_tenant import UserTenantRepository


class RepositoryManager:  # pylint: disable=too-many-instance-attributes
    db: AsyncSession

    def __init__(self, db: Annotated[AsyncSession, Depends(get_db)]) -> None:
        self.db = db
        self._tenant: TenantRepository | None = None
        self._user: UserRepository | None = None
        self._role: RoleRepository | None = None
        self._permission: PermissionRepository | None = None
        self._refresh_token: RefreshTokenRepository | None = None
        self._user_tenant: UserTenantRepository | None = None
        self._plan: PlanRepository | None = None
        self._plan_price: PlanPriceRepository | None = None
        self._subscription: SubscriptionRepository | None = None
        self._webhook_event: WebhookEventRepository | None = None

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

    @property
    def user_tenant(self) -> UserTenantRepository:
        if self._user_tenant is None:
            self._user_tenant = UserTenantRepository(self.db)
        return self._user_tenant

    @property
    def plan(self) -> PlanRepository:
        if self._plan is None:
            self._plan = PlanRepository(self.db)
        return self._plan

    @property
    def plan_price(self) -> PlanPriceRepository:
        if self._plan_price is None:
            self._plan_price = PlanPriceRepository(self.db)
        return self._plan_price

    @property
    def subscription(self) -> SubscriptionRepository:
        if self._subscription is None:
            self._subscription = SubscriptionRepository(self.db)
        return self._subscription

    @property
    def webhook_event(self) -> WebhookEventRepository:
        if self._webhook_event is None:
            self._webhook_event = WebhookEventRepository(self.db)
        return self._webhook_event

    @asynccontextmanager
    async def savepoint(self) -> AsyncGenerator[None]:
        async with self.db.begin_nested():
            yield
