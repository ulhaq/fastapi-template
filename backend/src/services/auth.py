import logging
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import Depends

from src.core.config import settings
from src.core.exceptions import (
    AlreadyExistsException,
    NotAuthenticatedException,
    NotFoundException,
)
from src.core.security import (
    BEARER_HEADERS,
    Token,
    authenticate_user,
    create_token,
    decode_token,
    hash_secret,
    sign,
    unsign,
    verify_secret,
)
from src.enums import ErrorCode
from src.repositories.repository_manager import RepositoryManager
from src.schemas.company import CompanyIn, CompanyOut
from src.schemas.user import EmailIn, ResetPasswordIn
from src.services.base import BaseService
from src.services.utils import send_email

log = logging.getLogger(__name__)


class AuthService(BaseService):
    def __init__(self, repos: Annotated[RepositoryManager, Depends()]) -> None:
        super().__init__(repos)

    async def register_company(
        self, company_in: CompanyIn, schedule_task: Callable
    ) -> CompanyOut:
        if await self.repos.user.get_by_email(company_in.email):
            raise AlreadyExistsException(
                f"Account already exists. [email={company_in.email}]",
                error_code=ErrorCode.EMAIL_ALREADY_EXISTS,
            )

        company = await self.repos.company.create(
            commit=False, **company_in.model_dump(include={"name"})
        )

        hashed_pw = hash_secret(company_in.password)

        user = await self.repos.user.create(
            commit=False,
            name=company_in.name,
            email=company_in.email,
            password=hashed_pw,
            company=company,
        )

        company_out = CompanyOut.model_validate(company)
        user_email, user_name = user.email, user.name

        await self.repos.commit()

        schedule_task(
            send_email,
            address=user_email,
            user_name=user_name,
            subject=f"Welcome to {settings.app_name}",
            email_template="welcome",
            data={
                "login_url": f"{settings.frontend_url}/login",
            },
        )

        return company_out

    async def get_access_token(self, username: str, password: str) -> Token:
        user = authenticate_user(password, await self.repos.user.get_by_email(username))

        if not user:
            raise NotAuthenticatedException(
                error_code=ErrorCode.LOGIN_FAILED,
                headers=BEARER_HEADERS,
            )

        access_token = create_token(user, settings.auth_access_token_expiry)
        refresh_token = create_token(
            user, settings.auth_refresh_token_expiry, include_user_claims=False
        )

        expires_at = datetime.now(UTC) + timedelta(
            seconds=settings.auth_refresh_token_expiry
        )
        await self.repos.refresh_token.delete_by_user(user)
        await self.repos.refresh_token.create(
            user, hash_secret(refresh_token), expires_at
        )
        await self.repos.commit()

        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
        )

    async def refresh_access_token(self, refresh_token: str | None) -> Token:
        if not refresh_token:
            raise NotAuthenticatedException(headers=BEARER_HEADERS)

        payload = decode_token(refresh_token)
        user_id = int(payload.get("sub", 0))

        if not user_id:
            raise NotAuthenticatedException(headers=BEARER_HEADERS)

        user = await self.repos.user.get(user_id)
        if not user:
            raise NotAuthenticatedException(headers=BEARER_HEADERS)

        stored_token = await self.repos.refresh_token.get_by_user(user)
        if not stored_token or not verify_secret(refresh_token, stored_token.token):
            raise NotAuthenticatedException(headers=BEARER_HEADERS)

        await self.repos.refresh_token.delete_by_user(user)

        new_access_token = create_token(user, settings.auth_access_token_expiry)
        new_refresh_token = create_token(
            user, settings.auth_refresh_token_expiry, include_user_claims=False
        )
        expires_at = datetime.now(UTC) + timedelta(
            seconds=settings.auth_refresh_token_expiry
        )
        await self.repos.refresh_token.create(
            user, hash_secret(new_refresh_token), expires_at
        )
        await self.repos.commit()

        return Token(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
        )

    async def logout(self, refresh_token: str | None) -> None:
        if refresh_token:
            try:
                payload = decode_token(refresh_token)
                user_id = int(payload.get("sub", 0))
                if user_id and (user := await self.repos.user.get(user_id)):
                    await self.repos.refresh_token.delete_by_user(user)
                    await self.repos.commit()
            except Exception:  # pylint: disable=broad-except
                pass

    async def request_password_reset(
        self, email_in: EmailIn, schedule_task: Callable
    ) -> None:
        user = await self.repos.user.get_by_email(email_in.email)
        if not user:
            log.info("Password reset request failed. [email=%s]", email_in.email)
            return None

        token = sign(data=email_in.email, salt="reset-password")

        await self.repos.user.delete_password_reset_token(commit=False, user=user)
        await self.repos.user.create_password_reset_token(
            commit=False, user=user, token=hash_secret(token)
        )

        user_email, user_name = user.email, user.name

        await self.repos.commit()

        schedule_task(
            send_email,
            address=user_email,
            user_name=user_name,
            subject="Password Reset",
            email_template="reset-password",
            data={
                "reset_url": f"{settings.frontend_url}/"
                + settings.frontend_password_reset_path
                + token,
                "expiration_minutes": settings.auth_password_reset_expiry // 60,
            },
        )

        return None

    async def reset_password(self, reset_password_in: ResetPasswordIn) -> None:
        email = unsign(
            token=reset_password_in.token,
            salt="reset-password",
            max_age=settings.auth_password_reset_expiry,
        )
        if user := await self.repos.user.get_by_email(email):
            token = await self.repos.user.get_password_reset_token(user)

            if not token or not verify_secret(reset_password_in.token, token.token):
                raise NotAuthenticatedException(
                    "Token invalid", error_code=ErrorCode.TOKEN_INVALID
                )

            await self.repos.user.delete_password_reset_token(commit=False, user=user)

            hashed_pw = hash_secret(reset_password_in.password)

            await self.repos.user.update(user, password=hashed_pw)

            return None

        raise NotFoundException(f"User not found. [{email=}]")
