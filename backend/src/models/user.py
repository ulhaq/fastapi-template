from typing import TYPE_CHECKING

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base
from src.models.mixins import DeleteTimestampMixin, TimestampMixin

if TYPE_CHECKING:
    from src.models.organization import Organization
    from src.models.password_reset_token import PasswordResetToken
    from src.models.refresh_token import RefreshToken
    from src.models.role import Role


# pylint: disable=too-few-public-methods


class User(Base, DeleteTimestampMixin, TimestampMixin):
    __tablename__ = "user"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, index=True, nullable=False)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String, nullable=False)

    organizations: Mapped[list["Organization"]] = relationship(
        "Organization",
        secondary="user_organization",
        back_populates="users",
        lazy="selectin",
        passive_deletes=True,
    )
    roles: Mapped[list["Role"]] = relationship(
        "Role",
        secondary="user_role",
        back_populates="users",
        lazy="joined",
        passive_deletes=True,
    )
    password_reset_token: Mapped["PasswordResetToken"] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
