from typing import TYPE_CHECKING

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base
from src.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from src.models.user import User


# pylint: disable=too-few-public-methods


class Company(Base, TimestampMixin):
    __tablename__ = "company"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, index=True, nullable=False)

    users: Mapped[list["User"]] = relationship(back_populates="company", lazy="joined")
