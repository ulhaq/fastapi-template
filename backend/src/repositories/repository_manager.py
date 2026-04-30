from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.repositories.api_token import ApiTokenRepository
from src.repositories.billing import (
    PlanFeatureRepository,
    PlanPriceRepository,
    PlanRepository,
    SubscriptionRepository,
    WebhookEventRepository,
)
from src.repositories.email_verification_token import EmailVerificationTokenRepository
from src.repositories.invite_token import InviteTokenRepository
from src.repositories.organization import OrganizationRepository
from src.repositories.permission import PermissionRepository
from src.repositories.refresh_token import RefreshTokenRepository
from src.repositories.role import RoleRepository
from src.repositories.user import UserRepository
from src.repositories.user_organization import UserOrganizationRepository


class RepositoryManager:
    db: AsyncSession

    def __init__(self, db: Annotated[AsyncSession, Depends(get_db)]) -> None:
        self.db = db
        self._api_token: ApiTokenRepository | None = None
        self._organization: OrganizationRepository | None = None
        self._user: UserRepository | None = None
        self._role: RoleRepository | None = None
        self._permission: PermissionRepository | None = None
        self._refresh_token: RefreshTokenRepository | None = None
        self._user_organization: UserOrganizationRepository | None = None
        self._plan: PlanRepository | None = None
        self._plan_price: PlanPriceRepository | None = None
        self._plan_feature: PlanFeatureRepository | None = None
        self._subscription: SubscriptionRepository | None = None
        self._webhook_event: WebhookEventRepository | None = None
        self._email_verification_token: EmailVerificationTokenRepository | None = None
        self._invite_token: InviteTokenRepository | None = None

    @property
    def api_token(self) -> ApiTokenRepository:
        if self._api_token is None:
            self._api_token = ApiTokenRepository(self.db)
        return self._api_token

    @property
    def organization(self) -> OrganizationRepository:
        if self._organization is None:
            self._organization = OrganizationRepository(self.db)
        return self._organization

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
    def user_organization(self) -> UserOrganizationRepository:
        if self._user_organization is None:
            self._user_organization = UserOrganizationRepository(self.db)
        return self._user_organization

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
    def plan_feature(self) -> PlanFeatureRepository:
        if self._plan_feature is None:
            self._plan_feature = PlanFeatureRepository(self.db)
        return self._plan_feature

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

    @property
    def email_verification_token(self) -> EmailVerificationTokenRepository:
        if self._email_verification_token is None:
            self._email_verification_token = EmailVerificationTokenRepository(self.db)
        return self._email_verification_token

    @property
    def invite_token(self) -> InviteTokenRepository:
        if self._invite_token is None:
            self._invite_token = InviteTokenRepository(self.db)
        return self._invite_token

    @asynccontextmanager
    async def savepoint(self) -> AsyncGenerator[None]:
        async with self.db.begin_nested():
            yield
