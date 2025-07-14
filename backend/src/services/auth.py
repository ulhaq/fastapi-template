import logging
from typing import Annotated

from fastapi import BackgroundTasks, Depends
from fastapi.security import OAuth2PasswordRequestForm

from src.core.config import settings
from src.core.exceptions import (
    AlreadyExistsException,
    NotAuthenticatedException,
    NotFoundException,
)
from src.core.security import (
    Token,
    authenticate_user,
    create_access_token,
    hash_password,
    sign,
    unsign,
)
from src.repositories.repository_manager import RepositoryManager
from src.schemas.user import EmailIn, NewPasswordIn, UserIn, UserOut
from src.services.base import BaseService
from src.services.utils import send_email

log = logging.getLogger(__name__)


class AuthService(BaseService):
    def __init__(self, repos: Annotated[RepositoryManager, Depends()]) -> None:
        super().__init__(repos)

    async def register_user(
        self, user_in: UserIn, bg_tasks: BackgroundTasks
    ) -> UserOut:
        if await self.repos.user.get_by_email(user_in.email):
            raise AlreadyExistsException(
                detail=f"Account already exists. [email={user_in.email}]"
            )

        user_in.password = hash_password(user_in.password)

        user = await self.repos.user.create(**user_in.model_dump())

        bg_tasks.add_task(
            send_email,
            address=user.email,
            user_name=user.name,
            subject=f"Welcome to {settings.app_name}",
            email_template="welcome",
            data={
                "login_url": f"{settings.frontend_url}/login",
            },
        )

        return UserOut.model_validate(user)

    async def get_access_token(self, auth_data: OAuth2PasswordRequestForm) -> Token:
        user = authenticate_user(
            auth_data, await self.repos.user.get_by_email(auth_data.username)
        )

        if not user:
            raise NotAuthenticatedException(headers={"WWW-Authenticate": "Bearer"})

        return Token(access_token=create_access_token(user))

    async def request_password_reset(
        self, email_in: EmailIn, bg_tasks: BackgroundTasks
    ) -> None:
        user = await self.repos.user.get_by_email(email_in.email)
        if not user:
            log.info("Password reset request failed. [email=%s]", email_in.email)
            return None

        token = sign(data=email_in.email, salt="reset-password")

        bg_tasks.add_task(
            send_email,
            address=user.email,
            user_name=user.name,
            subject="Password Reset",
            email_template="reset-password",
            data={
                "reset_url": f"{settings.frontend_url}/password-reset/{token}",
                "expiration_minutes": settings.auth_password_reset_expiry,
            },
        )

        return None

    async def reset_password(self, new_password_in: NewPasswordIn, token: str) -> None:
        email = unsign(
            token=token,
            salt="reset-password",
            max_age=settings.auth_password_reset_expiry,
        )
        if model := await self.repos.user.get_by_email(email):
            new_password_in.password = hash_password(new_password_in.password)

            await self.repos.user.update(model, password=new_password_in.password)
            return None

        raise NotFoundException(f"User not found. [{email=}]")
