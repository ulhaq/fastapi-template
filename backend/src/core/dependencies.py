import hashlib
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.core.database import get_db
from src.core.exceptions import (
    NotAuthenticatedException,
    PermissionDeniedException,
    PlanFeatureUnavailableException,
)
from src.core.security import BEARER_HEADERS, Auth, decode_token, oauth2_scheme
from src.enums import OWNER_ROLE_NAME, ErrorCode, Permission, PlanFeature
from src.repositories.api_token import ApiTokenRepository
from src.repositories.billing import PlanFeatureRepository
from src.repositories.user import UserRepository


async def _authenticate_api_token(token: str, db: AsyncSession) -> Auth:
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    repo = ApiTokenRepository(db)
    api_token = await repo.get_by_hash(token_hash)

    if not api_token:
        raise NotAuthenticatedException(headers=BEARER_HEADERS)

    if api_token.expires_at is not None:
        expires = api_token.expires_at
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=UTC)
        if expires < datetime.now(UTC):
            raise NotAuthenticatedException(
                "Token expired",
                error_code=ErrorCode.TOKEN_EXPIRED,
                headers=BEARER_HEADERS,
            )

    user_repo = UserRepository(db)
    user_repo.set_organization_scope(api_token.organization_id)
    user = await user_repo.get(api_token.user_id)
    if not user:
        raise NotAuthenticatedException(headers=BEARER_HEADERS)

    await repo.touch_last_used(api_token.id, api_token.organization_id)

    auth = Auth.from_user_model(user, api_token.organization_id)
    token_perms = set(api_token.permissions)
    auth.permissions = [p for p in auth.permissions if p in token_perms]
    return auth


async def authenticate(
    db: Annotated[AsyncSession, Depends(get_db)],
    token: Annotated[str | None, Depends(oauth2_scheme)],
) -> Auth:
    if not settings.auth_enabled:
        return Auth(
            id=0,
            name="",
            email="",
            organization_id=0,
            permissions=[p.value for p in Permission],
            roles=[],
        )

    if not token:
        raise NotAuthenticatedException(headers=BEARER_HEADERS)

    if token.startswith("sk_"):
        return await _authenticate_api_token(token, db)

    payload = decode_token(token)
    user_id = int(payload.get("sub", 0))
    organization_id = int(payload.get("oid", 0))

    if not organization_id:
        raise NotAuthenticatedException(headers=BEARER_HEADERS)

    user = await UserRepository(db).get(user_id)

    if not user:
        raise NotAuthenticatedException(headers=BEARER_HEADERS)

    return Auth.from_user_model(user, organization_id)


def require_permission(permission: Permission) -> Callable:
    async def _check(
        current_user: Annotated[Auth, Depends(authenticate)],
    ) -> Auth:
        current_user.authorize(permission)
        return current_user

    return _check


def require_plan_feature(feature: PlanFeature) -> Callable:
    async def _check(
        current_user: Annotated[Auth, Depends(authenticate)],
        db: Annotated[AsyncSession, Depends(get_db)],
    ) -> Auth:
        if not settings.auth_enabled:
            return current_user
        features = await PlanFeatureRepository(db).get_features_for_organization(
            current_user.organization_id
        )
        if feature not in features:
            raise PlanFeatureUnavailableException
        return current_user

    return _check


def require_owner() -> Callable:
    async def _check(
        current_user: Annotated[Auth, Depends(authenticate)],
    ) -> Auth:
        if not settings.auth_enabled or OWNER_ROLE_NAME in current_user.roles:
            return current_user
        raise PermissionDeniedException

    return _check
