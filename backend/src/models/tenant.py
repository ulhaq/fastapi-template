from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base
from src.models.mixins import DeleteTimestampMixin, TimestampMixin

if TYPE_CHECKING:
    from src.models.role import Role
    from src.models.user import User


# pylint: disable=too-few-public-methods


class Tenant(Base, DeleteTimestampMixin, TimestampMixin):
    __tablename__ = "tenant"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, index=True, nullable=False)
    external_customer_id: Mapped[str | None] = mapped_column(
        String, nullable=True, index=True, unique=True
    )
    has_payment_method: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    trial_used: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    users: Mapped[list["User"]] = relationship(
        "User",
        secondary="user_tenant",
        back_populates="tenants",
        lazy="selectin",
        passive_deletes=True,
    )
    roles: Mapped[list["Role"]] = relationship(
        back_populates="tenant", passive_deletes=True
    )
