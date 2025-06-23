from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base
from src.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from src.models.role import Role


# pylint: disable=too-few-public-methods
class Permission(Base, TimestampMixin):
    __tablename__ = "permission"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, index=True, nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=True)

    roles: Mapped[list["Role"]] = relationship(
        "Role", secondary="role_permission", back_populates="permissions", lazy="joined"
    )


class RolePermission(Base, TimestampMixin):
    __tablename__ = "role_permission"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    role_id: Mapped[int] = mapped_column(Integer, ForeignKey("role.id"))
    permission_id: Mapped[int] = mapped_column(Integer, ForeignKey("permission.id"))
