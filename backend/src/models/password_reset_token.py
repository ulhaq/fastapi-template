from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base

if TYPE_CHECKING:
    from src.models.user import User


class PasswordResetToken(Base):
    __tablename__ = "password_reset_token"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("user.id", ondelete="CASCADE")
    )
    token: Mapped[str] = mapped_column(String, unique=True)
    created_at: Mapped[DateTime] = mapped_column(
        DateTime, default=datetime.now(UTC), nullable=False
    )

    user: Mapped["User"] = relationship(
        "User", back_populates="password_reset_token", passive_deletes=True
    )
