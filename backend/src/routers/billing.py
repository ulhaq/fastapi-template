from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Request, status

from src.core.dependencies import require_owner, require_permission
from src.core.limiter import limiter
from src.core.security import Auth
from src.enums import Permission
from src.schemas.billing import (
    CheckoutIn,
    CheckoutOut,
    CustomerPortalOut,
    PlanOut,
    SubscriptionOut,
    SwitchPlanIn,
)
from src.services.billing import PlanService, SubscriptionService, WebhookService

plan_router = APIRouter(prefix="/billing/plans")
subscription_router = APIRouter(prefix="/billing/subscriptions")
webhook_router = APIRouter(prefix="/billing")


# ---------------------------------------------------------------------------
# Plan endpoints
# ---------------------------------------------------------------------------


@plan_router.get("", status_code=status.HTTP_200_OK)
async def list_plans(
    service: Annotated[PlanService, Depends()],
    _: Annotated[Auth, Depends(require_permission(Permission.READ_PLAN))],
) -> list[PlanOut]:
    return await service.get_all_plans()


@plan_router.get("/{plan_id}", status_code=status.HTTP_200_OK)
async def retrieve_a_plan(
    service: Annotated[PlanService, Depends()],
    _: Annotated[Auth, Depends(require_permission(Permission.READ_PLAN))],
    plan_id: Annotated[int, Path()],
) -> PlanOut:
    return await service.get_plan(plan_id)


# ---------------------------------------------------------------------------
# Subscription endpoints
# ---------------------------------------------------------------------------


@subscription_router.post("/checkout", status_code=status.HTTP_200_OK)
@limiter.limit("5/minute")
async def start_checkout(
    request: Request,  # pylint: disable=unused-argument
    service: Annotated[SubscriptionService, Depends()],
    _: Annotated[Auth, Depends(require_owner())],
    checkout_in: CheckoutIn,
) -> CheckoutOut:
    return await service.start_checkout(checkout_in)


@subscription_router.get("/current", status_code=status.HTTP_200_OK)
async def get_current_subscription(
    service: Annotated[SubscriptionService, Depends()],
    _: Annotated[Auth, Depends(require_permission(Permission.READ_SUBSCRIPTION))],
) -> SubscriptionOut:
    return await service.get_current_subscription()


@subscription_router.post("/current/cancel", status_code=status.HTTP_200_OK)
@limiter.limit("5/minute")
async def cancel_subscription(
    request: Request,  # pylint: disable=unused-argument
    service: Annotated[SubscriptionService, Depends()],
    _: Annotated[Auth, Depends(require_owner())],
) -> SubscriptionOut:
    return await service.cancel_subscription()


@subscription_router.post("/current/resume", status_code=status.HTTP_200_OK)
@limiter.limit("5/minute")
async def resume_subscription(
    request: Request,  # pylint: disable=unused-argument
    service: Annotated[SubscriptionService, Depends()],
    _: Annotated[Auth, Depends(require_owner())],
) -> SubscriptionOut:
    return await service.resume_subscription()


@subscription_router.post("/current/switch-plan", status_code=status.HTTP_200_OK)
@limiter.limit("5/minute")
async def switch_plan(
    request: Request,  # pylint: disable=unused-argument
    service: Annotated[SubscriptionService, Depends()],
    _: Annotated[Auth, Depends(require_owner())],
    switch_in: SwitchPlanIn,
) -> SubscriptionOut | CheckoutOut:
    return await service.switch_plan(switch_in)


@subscription_router.get("/portal", status_code=status.HTTP_200_OK)
async def get_customer_portal(
    service: Annotated[SubscriptionService, Depends()],
    _: Annotated[Auth, Depends(require_owner())],
) -> CustomerPortalOut:
    return await service.get_customer_portal_url()


# ---------------------------------------------------------------------------
# Webhook endpoint
# ---------------------------------------------------------------------------


@webhook_router.post("/webhook", status_code=status.HTTP_200_OK)
@limiter.limit("120/minute")
async def billing_webhook(
    request: Request,
    service: Annotated[WebhookService, Depends()],
) -> dict:
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")
    success = await service.process_webhook(payload, sig_header)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Webhook processing failed",
        )
    return {"received": True}
