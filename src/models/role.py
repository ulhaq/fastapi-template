from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base
from src.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from src.models.permission import Permission
    from src.models.user import User


# pylint: disable=too-few-public-methods
class Role(Base, TimestampMixin):
    __tablename__ = "role"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, index=True, nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=True)

    permissions: Mapped[list["Permission"]] = relationship(
        "Permission", secondary="role_permission", back_populates="roles", lazy="joined"
    )
    users: Mapped[list["User"]] = relationship(
        "User", secondary="user_role", back_populates="roles", lazy="joined"
    )


class UserRole(Base, TimestampMixin):
    __tablename__ = "user_role"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("user.id"))
    role_id: Mapped[int] = mapped_column(Integer, ForeignKey("role.id"))
