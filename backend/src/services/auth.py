import logging
from typing import Annotated

from fastapi import BackgroundTasks, Depends, Response
from fastapi.security import OAuth2PasswordRequestForm
from jwt import ExpiredSignatureError, InvalidTokenError, decode

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
    create_refresh_token,
    hash_password,
    sign,
    unsign,
)
from src.enums import ErrorCode
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
                f"Account already exists. [email={user_in.email}]",
                error_code=ErrorCode.EMAIL_ALREADY_EXISTS,
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

    async def get_access_token(
        self, auth_data: OAuth2PasswordRequestForm, response: Response
    ) -> Token:
        user = authenticate_user(
            auth_data, await self.repos.user.get_by_email(auth_data.username)
        )

        if not user:
            raise NotAuthenticatedException(headers={"WWW-Authenticate": "Bearer"})

        access_token = create_access_token(user)
        refresh_token = create_refresh_token(user)

        self._set_refresh_token_cookie(refresh_token=refresh_token, response=response)

        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
        )

    async def refresh_access_token(
        self, refresh_token: str | None, response: Response
    ) -> Token:
        if not refresh_token:
            raise NotAuthenticatedException(
                "Refresh token invalid",
                error_code=ErrorCode.TOKEN_INVALID,
                headers={"WWW-Authenticate": "Bearer"},
            )

        try:
            payload = decode(
                refresh_token,
                settings.app_secret,
                algorithms=[settings.auth_algorithm],
                audience=settings.app_name,
            )
            user_id = payload.get("sub")
        except ExpiredSignatureError as exc:
            raise NotAuthenticatedException(
                "Token expired",
                error_code=ErrorCode.TOKEN_EXPIRED,
                headers={"WWW-Authenticate": "Bearer"},
            ) from exc
        except InvalidTokenError as exc:
            raise NotAuthenticatedException(
                "Token invalid",
                error_code=ErrorCode.TOKEN_INVALID,
                headers={"WWW-Authenticate": "Bearer"},
            ) from exc

        credentials_exception = NotAuthenticatedException(
            headers={"WWW-Authenticate": "Bearer"}
        )

        if not user_id:
            raise credentials_exception

        user = await self.repos.user.get(user_id)
        if not user:
            raise credentials_exception

        self._set_refresh_token_cookie(refresh_token=refresh_token, response=response)

        return Token(
            access_token=create_access_token(user),
            refresh_token=refresh_token,
        )

    async def logout(self, response: Response) -> None:
        self._delete_refresh_token_cookie(response=response)

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
                "reset_url": f"{settings.frontend_url}/"
                f"{settings.frontend_password_reset_path}/{token}",
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

    def _set_refresh_token_cookie(
        self,
        refresh_token: str,
        response: Response,
    ) -> None:
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            expires=settings.auth_refresh_token_expiry,
            # secure=True,  # Only over HTTPS
            # samesite="strict",  # or "lax" depending on use case
            path="/auth/refresh",
        )

    def _delete_refresh_token_cookie(self, response: Response) -> None:
        response.delete_cookie(
            key="refresh_token",
            httponly=True,
            # secure=True,  # Only over HTTPS
            # samesite="strict",  # or "lax" depending on use case
            path="/auth/refresh",
        )
