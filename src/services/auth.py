from typing import Annotated

from fastapi import Depends
from fastapi.security import OAuth2PasswordRequestForm

from src.core.exceptions import AlreadyExistsException, NotAuthenticatedException
from src.core.security import (
    Token,
    authenticate_user,
    create_access_token,
    hash_password,
)
from src.repositories.repository_manager import RepositoryManager
from src.schemas.user import UserIn, UserOut
from src.services.base import BaseService


class AuthService(BaseService):
    def __init__(self, repos: Annotated[RepositoryManager, Depends()]) -> None:
        super().__init__(repos)

    async def register_user(self, user_in: UserIn) -> UserOut:
        if await self.repos.user.get_by_email(user_in.email):
            raise AlreadyExistsException(
                detail=f"Account already exists. [email={user_in.email}]"
            )

        user_in.password = hash_password(user_in.password)

        return UserOut.model_validate(
            await self.repos.user.create(**user_in.model_dump())
        )

    async def get_access_token(self, auth_data: OAuth2PasswordRequestForm) -> Token:
        user = authenticate_user(
            auth_data, await self.repos.user.get_by_email(auth_data.username)
        )

        if not user:
            raise NotAuthenticatedException(headers={"WWW-Authenticate": "Bearer"})

        return Token(access_token=create_access_token(user))
