from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base
from src.models.mixins import DeleteTimestampMixin, TimestampMixin

if TYPE_CHECKING:
    from src.models.organization import Organization


class Plan(Base, DeleteTimestampMixin, TimestampMixin):
    __tablename__ = "billing_plan"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, index=True, nullable=False)
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    external_product_id: Mapped[str | None] = mapped_column(
        String, nullable=True, index=True, unique=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    prices: Mapped[list["PlanPrice"]] = relationship(
        back_populates="plan", passive_deletes=True, lazy="selectin"
    )
    plan_features: Mapped[list["PlanFeature"]] = relationship(
        back_populates="plan", passive_deletes=True, lazy="selectin"
    )


class PlanPrice(Base, DeleteTimestampMixin, TimestampMixin):
    __tablename__ = "billing_plan_price"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    plan_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("billing_plan.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    interval: Mapped[str] = mapped_column(String, nullable=False)
    interval_count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    external_price_id: Mapped[str | None] = mapped_column(
        String, nullable=True, index=True, unique=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    plan: Mapped["Plan"] = relationship(back_populates="prices")


class PlanFeature(Base, TimestampMixin):
    __tablename__ = "billing_plan_feature"
    __table_args__ = (
        UniqueConstraint("plan_id", "feature", name="uq_billing_plan_feature"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    plan_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("billing_plan.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    feature: Mapped[str] = mapped_column(String, nullable=False, index=True)

    plan: Mapped["Plan"] = relationship(back_populates="plan_features")


class Subscription(Base, DeleteTimestampMixin, TimestampMixin):
    __tablename__ = "billing_subscription"
    __table_args__ = (
        CheckConstraint(
            "status IN ('incomplete', 'incomplete_expired', 'active', 'trialing', 'past_due', 'canceled', 'unpaid', 'paused')",  # noqa: E501
            name="ck_billing_subscription_status",
        ),
        Index(
            "uq_billing_subscription_active_organization",
            "organization_id",
            unique=True,
            postgresql_where=text("status != 'canceled' AND deleted_at IS NULL"),
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    organization_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("organization.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    plan_price_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("billing_plan_price.id", ondelete="SET NULL"),
        nullable=True,
    )
    external_subscription_id: Mapped[str | None] = mapped_column(
        String, nullable=True, index=True, unique=True
    )
    status: Mapped[str] = mapped_column(String, nullable=False, default="incomplete")
    current_period_start: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    current_period_end: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    cancel_at_period_end: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    canceled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    cancel_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    trial_end: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    organization: Mapped["Organization"] = relationship()
    plan_price: Mapped["PlanPrice | None"] = relationship(lazy="selectin")


class WebhookEvent(Base, TimestampMixin):
    __tablename__ = "billing_webhook_event"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    external_event_id: Mapped[str] = mapped_column(
        String, unique=True, nullable=False, index=True
    )
    event_type: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False, default="received")
    error: Mapped[str | None] = mapped_column(String, nullable=True)
    processed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
