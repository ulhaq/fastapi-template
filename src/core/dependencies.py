from typing import Annotated

from fastapi import Depends
from jwt import InvalidTokenError, decode

from src.core.config import settings
from src.core.exceptions import NotAuthenticatedException
from src.core.security import TokenData, oauth2_scheme
from src.repositories.user import UserRepository


def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    user_repository: UserRepository = UserRepository()

    credentials_exception = NotAuthenticatedException(
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode(
            token,
            settings.app_secret,
            algorithms=[settings.auth_algorithm],
            audience=settings.app_name,
        )
        email = payload.get("email")
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email)
    except InvalidTokenError:
        raise credentials_exception
    user = user_repository.get_by_email(token_data.email)
    if user is None:
        raise credentials_exception
    return user
