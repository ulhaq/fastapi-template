from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Integer, String, and_
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base
from src.models.mixins import DeleteTimestampMixin, TimestampMixin
from src.models.user import User
from src.models.user_organization import UserOrganization

if TYPE_CHECKING:
    from src.models.role import Role


class Organization(Base, DeleteTimestampMixin, TimestampMixin):
    __tablename__ = "organization"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, index=True, nullable=False)
    external_customer_id: Mapped[str | None] = mapped_column(
        String, nullable=True, index=True, unique=True
    )
    has_payment_method: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    trial_used: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    users: Mapped[list[User]] = relationship(
        User,
        secondary="user_organization",
        secondaryjoin=and_(
            UserOrganization.user_id == User.id, User.deleted_at.is_(None)
        ),
        back_populates="organizations",
        lazy="selectin",
        passive_deletes=True,
    )
    roles: Mapped[list["Role"]] = relationship(
        back_populates="organization", passive_deletes=True
    )
