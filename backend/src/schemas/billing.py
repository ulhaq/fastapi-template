from datetime import datetime

from pydantic import BaseModel, ConfigDict, computed_field

from src.core.config import settings


class CheckoutIn(BaseModel):
    plan_price_id: int


class SwitchPlanIn(BaseModel):
    plan_price_id: int


class StartTrialIn(BaseModel):
    plan_price_id: int


class PlanPriceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    plan_id: int
    amount: int
    currency: str
    interval: str
    interval_count: int
    is_active: bool

    @computed_field  # type: ignore[prop-decorator]
    @property
    def trial_period_days(self) -> int | None:
        return settings.billing_trial_period_days or None

    created_at: datetime
    updated_at: datetime


class PlanOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None
    is_active: bool
    prices: list[PlanPriceOut]
    created_at: datetime
    updated_at: datetime


class SubscriptionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    organization_id: int
    plan_price_id: int | None
    status: str
    current_period_start: datetime | None
    current_period_end: datetime | None
    cancel_at_period_end: bool
    canceled_at: datetime | None
    cancel_at: datetime | None
    trial_end: datetime | None
    plan_price: PlanPriceOut | None
    has_payment_method: bool = False
    trial_used: bool = False
    created_at: datetime
    updated_at: datetime


class CheckoutOut(BaseModel):
    checkout_url: str


class CustomerPortalOut(BaseModel):
    portal_url: str
