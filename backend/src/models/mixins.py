from datetime import UTC, datetime

from sqlalchemy import DateTime
from sqlalchemy.orm import Mapped, mapped_column


class TimestampMixin:
    created_at: Mapped[DateTime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC), nullable=False
    )
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )


class DeleteTimestampMixin:
    deleted_at: Mapped[DateTime] = mapped_column(DateTime, default=None, nullable=True)
