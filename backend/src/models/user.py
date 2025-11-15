from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base
from src.models.company import Company
from src.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from src.models.role import Role


# pylint: disable=too-few-public-methods


class User(Base, TimestampMixin):
    __tablename__ = "user"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, index=True, nullable=False)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String, nullable=False)
    company_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("company.id", name="fk_user_company_id_company"),
        nullable=False,
    )

    company: Mapped["Company"] = relationship("Company", back_populates="users")
    roles: Mapped[list["Role"]] = relationship(
        "Role", secondary="user_role", back_populates="users", lazy="joined"
    )
