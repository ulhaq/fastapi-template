import logging
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import Depends
from pydantic import BaseModel

from src.core.config import settings
from src.core.exceptions import (
    AlreadyExistsException,
    NotAuthenticatedException,
    NotFoundException,
    PermissionDeniedException,
)
from src.core.security import (
    BEARER_HEADERS,
    Auth,
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
from src.schemas.user import EmailIn, ResetPasswordIn, UserIn, UserOut
from src.services.base import BaseService
from src.services.utils import send_email

log = logging.getLogger(__name__)


class AuthService(BaseService):
    def __init__(self, repos: Annotated[RepositoryManager, Depends()]) -> None:
        super().__init__(repos)

    async def register_tenant(
        self, user_in: UserIn, schedule_task: Callable
    ) -> UserOut:
        if await self.repos.user.get_by_email(user_in.email):
            raise AlreadyExistsException(
                f"Account already exists. [email={user_in.email}]",
                error_code=ErrorCode.EMAIL_ALREADY_EXISTS,
            )

        tenant = await self.repos.tenant.create(
            commit=False, name=f"{user_in.name}'s Tenant"
        )

        hashed_pw = hash_secret(user_in.password)

        user = await self.repos.user.create(
            commit=False,
            name=user_in.name,
            email=user_in.email,
            password=hashed_pw,
        )

        await self.repos.user_tenant.create(
            commit=False,
            user_id=user.id,
            tenant_id=tenant.id,
            last_active_at=datetime.now(UTC),
        )

        permissions = await self.repos.permission.get_all()

        admin_role = await self.repos.role.create(
            commit=False,
            name="Admin",
            description="Full access to all system features and settings.",
            tenant=tenant,
        )
        await self.repos.role.add_permissions(
            admin_role, *[p.id for p in permissions], commit=False
        )
        await self.repos.user.add_roles(user, admin_role.id, commit=False)

        user_out = UserOut.model_validate(user)
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

        return user_out

    async def get_access_token(self, username: str, password: str) -> Token:
        user = authenticate_user(
            password, await self.repos.user.get_by_email(username.lower())
        )

        if not user:
            raise NotAuthenticatedException(
                error_code=ErrorCode.LOGIN_FAILED,
                headers=BEARER_HEADERS,
            )

        membership = await self.repos.user_tenant.get_active_tenant_for_user(user.id)
        if not membership:
            raise NotAuthenticatedException(
                error_code=ErrorCode.LOGIN_FAILED,
                headers=BEARER_HEADERS,
            )

        await self.repos.user_tenant.update_last_active(membership, commit=False)

        access_token = create_token(
            user, settings.auth_access_token_expiry, tenant_id=membership.tenant_id
        )
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

        membership = await self.repos.user_tenant.get_active_tenant_for_user(user.id)
        if not membership:
            raise NotAuthenticatedException(headers=BEARER_HEADERS)

        await self.repos.refresh_token.delete_by_user(user)

        new_access_token = create_token(
            user, settings.auth_access_token_expiry, tenant_id=membership.tenant_id
        )
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

    async def switch_tenant(self, current_user: Auth, tenant_id: int) -> Token:
        user = await self.repos.user.get(current_user.id)
        if not user:
            raise NotAuthenticatedException(headers=BEARER_HEADERS)

        membership = await self.repos.user_tenant.get_by_user_and_tenant(
            current_user.id, tenant_id
        )
        if not membership:
            raise PermissionDeniedException("You are not a member of this tenant")

        await self.repos.user_tenant.update_last_active(membership, commit=False)

        access_token = create_token(
            user, settings.auth_access_token_expiry, tenant_id=tenant_id
        )
        new_refresh_token = create_token(
            user, settings.auth_refresh_token_expiry, include_user_claims=False
        )

        expires_at = datetime.now(UTC) + timedelta(
            seconds=settings.auth_refresh_token_expiry
        )
        await self.repos.refresh_token.delete_by_user(user)
        await self.repos.refresh_token.create(
            user, hash_secret(new_refresh_token), expires_at
        )
        await self.repos.commit()

        return Token(
            access_token=access_token,
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
            await self.repos.refresh_token.delete_by_user(user)

            hashed_pw = hash_secret(reset_password_in.password)

            await self.repos.user.update(user, password=hashed_pw)

            return None

        raise NotFoundException(f"User not found. [{email=}]")
