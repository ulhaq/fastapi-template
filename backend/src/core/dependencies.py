from collections.abc import Callable
from typing import Annotated

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.core.database import get_db
from src.core.exceptions import NotAuthenticatedException, PermissionDeniedException
from src.core.security import BEARER_HEADERS, Auth, decode_token, oauth2_scheme
from src.enums import OWNER_ROLE_NAME, Permission
from src.models.user import User


async def authenticate(
    db: Annotated[AsyncSession, Depends(get_db)],
    token: Annotated[str | None, Depends(oauth2_scheme)],
) -> Auth:
    if not settings.auth_enabled:
        return Auth(
            id=0,
            name="",
            email="",
            tenant_id=0,
            permissions=[p.value for p in Permission],
            roles=[],
        )

    if not token:
        raise NotAuthenticatedException(headers=BEARER_HEADERS)

    payload = decode_token(token)
    user_id = int(payload.get("sub", 0))
    tenant_id = int(payload.get("tid", 0))

    if not tenant_id:
        raise NotAuthenticatedException(headers=BEARER_HEADERS)

    user = await db.scalar(
        select(User).where(User.id == user_id, User.deleted_at.is_(None))
    )

    if not user:
        raise NotAuthenticatedException(headers=BEARER_HEADERS)

    return Auth.from_user_model(user, tenant_id)


def require_permission(permission: Permission) -> Callable:
    async def _check(
        current_user: Annotated[Auth, Depends(authenticate)],
    ) -> Auth:
        current_user.authorize(permission)
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
