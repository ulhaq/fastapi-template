import logging
from collections.abc import Callable, Sequence
from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import Depends

from src.billing.dependencies import BillingProviderDep
from src.core.config import settings
from src.core.exceptions import (
    AlreadyExistsException,
    NotAuthenticatedException,
    NotFoundException,
    PermissionDeniedException,
    ValidationException,
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
from src.enums import OWNER_ROLE_NAME, ErrorCode
from src.repositories.repository_manager import RepositoryManager
from src.models.role import Role
from src.schemas.user import (
    CompleteInviteIn,
    CompleteRegistrationIn,
    EmailIn,
    InviteStatusOut,
    RegisterOut,
    ResetPasswordIn,
    SetupTokenOut,
    VerifyEmailIn,
)
from src.services.base import BaseService
from src.services.organization import _setup_new_organization
from src.services.utils import send_email

log = logging.getLogger(__name__)


def _filter_assignable_roles(roles: Sequence[Role]) -> list[Role]:
    return [r for r in roles if not (r.is_protected and r.name == OWNER_ROLE_NAME)]


class AuthService(BaseService):
    def __init__(
        self,
        repos: Annotated[RepositoryManager, Depends()],
        provider: BillingProviderDep,
    ) -> None:
        self.provider = provider
        super().__init__(repos)

    async def register_organization(
        self, email_in: EmailIn, schedule_task: Callable
    ) -> RegisterOut:
        if await self.repos.user.get_by_email(email_in.email):
            raise AlreadyExistsException(
                f"Account already exists. [email={email_in.email}]",
                error_code=ErrorCode.EMAIL_ALREADY_EXISTS,
            )

        token = sign(data=email_in.email, salt="email-verification")
        await self.repos.email_verification_token.delete_by_email(email_in.email)
        await self.repos.email_verification_token.create(
            email=email_in.email, token=hash_secret(token)
        )
        schedule_task(
            send_email,
            address=email_in.email,
            user_name=email_in.email,
            subject=f"Verify your email for {settings.app_name}",
            email_template="verify-email",
            data={
                "verify_url": (f"{settings.frontend_url}/verify-email?token={token}"),
                "expiration_hours": settings.email_verification_expiry // 3600,
            },
        )
        return RegisterOut(message="Check your email to verify your account.")

    async def verify_email(self, schema_in: VerifyEmailIn) -> SetupTokenOut:
        email: str = unsign(
            schema_in.token,
            salt="email-verification",
            max_age=settings.email_verification_expiry,
        )

        record = await self.repos.email_verification_token.get_by_email(email)
        if not record or not verify_secret(schema_in.token, record.token):
            raise NotAuthenticatedException(
                "Token invalid", error_code=ErrorCode.TOKEN_INVALID
            )

        await self.repos.email_verification_token.delete_by_email(email)

        setup_token = sign(data=email, salt="complete-registration")
        return SetupTokenOut(setup_token=setup_token)

    async def complete_registration(
        self, schema_in: CompleteRegistrationIn, schedule_task: Callable
    ) -> Token:
        email: str = unsign(
            schema_in.setup_token,
            salt="complete-registration",
            max_age=settings.complete_registration_expiry,
        )

        if await self.repos.user.get_by_email(email):
            raise AlreadyExistsException(
                f"Account already exists. [email={email}]",
                error_code=ErrorCode.EMAIL_ALREADY_EXISTS,
            )

        hashed_pw = hash_secret(schema_in.password)

        # Restore soft-deleted user (orphaned when their org was deleted) rather than
        # creating a duplicate row that would violate the email unique constraint.
        deleted_user = await self.repos.user.get_by_email(email, include_deleted=True)
        if deleted_user:
            user = await self.repos.user.restore(deleted_user)
            user = await self.repos.user.update(
                user, name=schema_in.name, password=hashed_pw
            )
        else:
            user = await self.repos.user.create(
                name=schema_in.name,
                email=email,
                password=hashed_pw,
            )

        organization = await self.repos.organization.create(
            name=f"{schema_in.name}'s Organization"
        )
        await self.repos.user_organization.create(
            user_id=user.id,
            organization_id=organization.id,
            last_active_at=datetime.now(UTC),
        )

        await _setup_new_organization(self.repos, organization, user)

        # Re-fetch user so roles assigned by _setup_new_organization are loaded
        user = await self.repos.user.get_one(user.id)

        schedule_task(
            send_email,
            address=email,
            user_name=schema_in.name,
            subject=f"Welcome to {settings.app_name}",
            email_template="welcome",
            data={"login_url": f"{settings.frontend_url}/login"},
        )

        access_token = create_token(
            user, settings.auth_access_token_expiry, organization_id=organization.id
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

        return Token(access_token=access_token, refresh_token=refresh_token)

    async def invite_status(self, token: str) -> InviteStatusOut:
        data: dict = unsign(token, salt="invite", max_age=settings.invite_expiry)
        email: str = data["email"]

        record = await self.repos.invite_token.get_by_email(email)
        if not record or not verify_secret(token, record.token):
            raise NotAuthenticatedException(
                "Token invalid", error_code=ErrorCode.TOKEN_INVALID
            )

        user_exists = await self.repos.user.get_by_email(email) is not None
        return InviteStatusOut(email=email, user_exists=user_exists)

    async def complete_invite(
        self, schema_in: CompleteInviteIn, schedule_task: Callable
    ) -> Token:
        data: dict = unsign(
            schema_in.invite_token,
            salt="invite",
            max_age=settings.invite_expiry,
        )
        email: str = data["email"]
        organization_id: int = data["organization_id"]
        role_ids: list[int] = data.get("role_ids", [])

        record = await self.repos.invite_token.get_by_email(email)
        if not record or not verify_secret(schema_in.invite_token, record.token):
            raise NotAuthenticatedException(
                "Token invalid", error_code=ErrorCode.TOKEN_INVALID
            )

        await self.repos.invite_token.delete_by_email(email)

        organization = await self.repos.organization.get(organization_id)
        if not organization or organization.deleted_at is not None:
            raise NotFoundException(
                "Organization not found or has been deleted. "
                f"[organization_id={organization_id}]"
            )

        existing_user = await self.repos.user.get_by_email(email)

        if existing_user:
            # Existing user from another org - add them to this org.
            membership = (
                await self.repos.user_organization.get_by_user_and_organization(
                    user_id=existing_user.id,
                    organization_id=organization_id,
                )
            )
            if membership:
                raise AlreadyExistsException(
                    "User is already a member of this organization.",
                    error_code=ErrorCode.EMAIL_ALREADY_EXISTS,
                )

            await self.repos.user_organization.create(
                user_id=existing_user.id,
                organization_id=organization_id,
                last_active_at=datetime.now(UTC),
            )

            if role_ids:
                self.repos.role.set_organization_scope(organization_id)
                valid_roles = _filter_assignable_roles(
                    await self.repos.role.filter_by_ids(role_ids)
                )
                if valid_roles:
                    await self.repos.user.add_roles(
                        existing_user, *[r.id for r in valid_roles]
                    )

            user = await self.repos.user.get_one(existing_user.id)

            schedule_task(
                send_email,
                address=email,
                user_name=user.name,
                subject=f"You've been added to {organization.name}",
                email_template="added-to-org",
                data={
                    "organization_name": organization.name,
                    "login_url": f"{settings.frontend_url}/login",
                },
            )
        else:
            # New user - require name and password to create an account.
            if not schema_in.name or not schema_in.password:
                raise ValidationException(
                    "Name and password are required for new accounts."
                )

            # Restore soft-deleted user rather than creating a duplicate that
            # would violate the email unique constraint.
            deleted_user = await self.repos.user.get_by_email(
                email, include_deleted=True
            )
            hashed_pw = hash_secret(schema_in.password)
            if deleted_user:
                user = await self.repos.user.restore(deleted_user)
                user = await self.repos.user.update(
                    user, name=schema_in.name, password=hashed_pw
                )
            else:
                user = await self.repos.user.create(
                    name=schema_in.name,
                    email=email,
                    password=hashed_pw,
                )

            await self.repos.user_organization.create(
                user_id=user.id,
                organization_id=organization_id,
                last_active_at=datetime.now(UTC),
            )

            if role_ids:
                self.repos.role.set_organization_scope(organization_id)
                valid_roles = _filter_assignable_roles(
                    await self.repos.role.filter_by_ids(role_ids)
                )
                if valid_roles:
                    await self.repos.user.add_roles(user, *[r.id for r in valid_roles])

            user = await self.repos.user.get_one(user.id)

        access_token = create_token(
            user, settings.auth_access_token_expiry, organization_id=organization_id
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

        return Token(access_token=access_token, refresh_token=refresh_token)

    async def get_access_token(self, username: str, password: str) -> Token:
        user = authenticate_user(
            password, await self.repos.user.get_by_email(username.lower())
        )

        if not user:
            raise NotAuthenticatedException(
                error_code=ErrorCode.LOGIN_FAILED,
                headers=BEARER_HEADERS,
            )

        membership = (
            await self.repos.user_organization.get_active_organization_for_user(user.id)
        )
        if not membership:
            raise NotAuthenticatedException(
                error_code=ErrorCode.LOGIN_FAILED,
                headers=BEARER_HEADERS,
            )

        await self.repos.user_organization.update_last_active(membership)

        access_token = create_token(
            user,
            settings.auth_access_token_expiry,
            organization_id=membership.organization_id,
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

        membership = (
            await self.repos.user_organization.get_active_organization_for_user(user.id)
        )
        if not membership:
            raise NotAuthenticatedException(headers=BEARER_HEADERS)

        await self.repos.refresh_token.delete_by_user(user)

        new_access_token = create_token(
            user,
            settings.auth_access_token_expiry,
            organization_id=membership.organization_id,
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

        return Token(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
        )

    async def switch_organization(
        self, current_user: Auth, organization_id: int
    ) -> Token:
        user = await self.repos.user.get(current_user.id)
        if not user:
            raise NotAuthenticatedException(headers=BEARER_HEADERS)

        membership = await self.repos.user_organization.get_by_user_and_organization(
            current_user.id, organization_id
        )
        if not membership:
            raise PermissionDeniedException("You are not a member of this organization")

        await self.repos.user_organization.update_last_active(membership)

        access_token = create_token(
            user, settings.auth_access_token_expiry, organization_id=organization_id
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

        await self.repos.user.delete_password_reset_token(user=user)
        await self.repos.user.create_password_reset_token(
            user=user, token=hash_secret(token)
        )

        user_email, user_name = user.email, user.name

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

            await self.repos.user.delete_password_reset_token(user=user)
            await self.repos.refresh_token.delete_by_user(user)

            hashed_pw = hash_secret(reset_password_in.password)

            await self.repos.user.update(user, password=hashed_pw)

            return None

        raise NotFoundException(f"User not found. [{email=}]")
