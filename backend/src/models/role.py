from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base
from src.models.mixins import DeleteTimestampMixin, TimestampMixin

if TYPE_CHECKING:
    from src.models.permission import Permission
    from src.models.tenant import Tenant
    from src.models.user import User


# pylint: disable=too-few-public-methods


class Role(Base, DeleteTimestampMixin, TimestampMixin):
    __tablename__ = "role"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, index=True, nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=True)
    tenant_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("tenant.id", name="fk_role_tenant_id_tenant", ondelete="CASCADE"),
        nullable=False,
    )
    is_protected: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="0"
    )

    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="roles")
    permissions: Mapped[list["Permission"]] = relationship(
        "Permission",
        secondary="role_permission",
        back_populates="roles",
        lazy="joined",
        passive_deletes=True,
    )
    users: Mapped[list["User"]] = relationship(
        "User", secondary="user_role", back_populates="roles", passive_deletes=True
    )


class UserRole(Base, TimestampMixin):
    __tablename__ = "user_role"
    __table_args__ = (UniqueConstraint("user_id", "role_id", name="uq_user_role"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("user.id", ondelete="CASCADE")
    )
    role_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("role.id", ondelete="CASCADE")
    )
