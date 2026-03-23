from collections.abc import Callable
from typing import Annotated

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.core.database import get_db
from src.core.exceptions import NotAuthenticatedException
from src.core.security import BEARER_HEADERS, Auth, decode_token, oauth2_scheme
from src.enums import Permission
from src.models.user import User


async def authenticate(
    db: Annotated[AsyncSession, Depends(get_db)],
    token: Annotated[str | None, Depends(oauth2_scheme)],
) -> Auth:
    if not settings.auth_enabled:
        return Auth(
            id=0, name="", email="", company_id=0, permissions=[p.value for p in Permission], roles=[]
        )

    if not token:
        raise NotAuthenticatedException(headers=BEARER_HEADERS)

    payload = decode_token(token)
    user_id = int(payload.get("sub", 0))

    user = await db.scalar(select(User).where(User.id == user_id))

    if not user:
        raise NotAuthenticatedException(headers=BEARER_HEADERS)

    return Auth.from_user_model(user)


def require_permission(permission: Permission) -> Callable:
    async def _check(
        current_user: Annotated[Auth, Depends(authenticate)],
    ) -> Auth:
        current_user.authorize(permission)
        return current_user

    return _check
