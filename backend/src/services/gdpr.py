import asyncio
import logging
from datetime import UTC, datetime, timedelta
from typing import Any, cast

from sqlalchemy import delete, select
from sqlalchemy.engine import CursorResult
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.models.email_verification_token import EmailVerificationToken
from src.models.invite_token import InviteToken
from src.models.password_reset_token import PasswordResetToken
from src.models.user import User

log = logging.getLogger(__name__)


async def purge_expired_tokens(db: AsyncSession) -> int:
    now = datetime.now(UTC)
    cutoff_buffer = timedelta(days=settings.gdpr_token_purge_days)

    password_reset_cutoff = (
        now - timedelta(seconds=settings.auth_password_reset_expiry) - cutoff_buffer
    )
    email_verify_cutoff = (
        now - timedelta(seconds=settings.email_verification_expiry) - cutoff_buffer
    )
    invite_cutoff = now - timedelta(seconds=settings.invite_expiry) - cutoff_buffer

    r1 = await db.execute(
        delete(PasswordResetToken).where(
            PasswordResetToken.created_at < password_reset_cutoff
        )
    )
    r2 = await db.execute(
        delete(EmailVerificationToken).where(
            EmailVerificationToken.created_at < email_verify_cutoff
        )
    )
    r3 = await db.execute(
        delete(InviteToken).where(InviteToken.created_at < invite_cutoff)
    )
    return (
        cast(CursorResult[Any], r1).rowcount
        + cast(CursorResult[Any], r2).rowcount
        + cast(CursorResult[Any], r3).rowcount
    )


async def purge_soft_deleted_users(db: AsyncSession) -> int:
    cutoff = datetime.now(UTC) - timedelta(days=settings.gdpr_retention_days)
    stmt = select(User).where(
        User.deleted_at.is_not(None),
        User.deleted_at < cutoff,
    )
    rs = await db.execute(stmt)
    users = rs.scalars().unique().all()
    for user in users:
        await db.delete(user)
    return len(users)


async def run_gdpr_retention_loop(session_factory: Any) -> None:
    while True:
        await asyncio.sleep(24 * 60 * 60)
        try:
            async with session_factory() as session:
                async with session.begin():
                    token_count = await purge_expired_tokens(session)
                    user_count = await purge_soft_deleted_users(session)
                    log.info(
                        "GDPR retention: purged %d token(s), %d user(s)",
                        token_count,
                        user_count,
                    )
        except Exception as exc:
            log.error("GDPR retention loop error: %s", exc, exc_info=True)
