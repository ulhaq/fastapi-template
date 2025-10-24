from typing import Annotated

from fastapi import Depends
from jwt import ExpiredSignatureError, InvalidTokenError, decode
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.core.database import get_db
from src.core.exceptions import NotAuthenticatedException
from src.core.security import Auth, current_user, oauth2_scheme
from src.enums import ErrorCode
from src.models.user import User


async def authenticate(
    db: Annotated[AsyncSession, Depends(get_db)],
    token: Annotated[str, Depends(oauth2_scheme)],
) -> None:
    credentials_exception = NotAuthenticatedException(
        headers={"WWW-Authenticate": "Bearer"}
    )

    try:
        payload = decode(
            token,
            settings.app_secret,
            algorithms=[settings.auth_algorithm],
            audience=settings.app_name,
        )
        email = payload.get("email")
    except ExpiredSignatureError as exc:
        raise NotAuthenticatedException(
            "Token expired",
            error_code=ErrorCode.TOKEN_EXPIRED,
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
    except InvalidTokenError as exc:
        raise credentials_exception from exc

    user = await db.scalar(select(User).where(User.email == email))

    if not user:
        raise credentials_exception

    current_user.set(Auth.from_user_model(user))
