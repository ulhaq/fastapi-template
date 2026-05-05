from collections.abc import Callable
from datetime import date
from typing import Annotated

from fastapi import Depends

from src.billing.abc import BillingProviderABC
from src.billing.stripe_provider import StripeProvider
from src.core.config import settings
from src.core.dependencies import authenticate
from src.core.exceptions import QuotaExceededException
from src.core.security import Auth
from src.enums import UsageMetric
from src.repositories.repository_manager import RepositoryManager


def get_billing_provider() -> BillingProviderABC:
    return StripeProvider(
        api_key=settings.stripe_secret_key.get_secret_value(),
        webhook_secret=settings.stripe_webhook_secret.get_secret_value(),
    )


BillingProviderDep = Annotated[BillingProviderABC, Depends(get_billing_provider)]


def _current_period_start() -> date:
    return date.today().replace(day=1)


def require_quota(metric: UsageMetric) -> Callable:
    """
    FastAPI dependency factory that blocks the request with QUOTA_EXCEEDED when
    the organisation has consumed its plan allocation for `metric` this period.
    Use as a default-value dependency on the route parameter list:

        async def my_endpoint(
            _: Annotated[None, Depends(require_quota(UsageMetric.API_REQUESTS))],
            ...
        ): ...
    """

    async def _check(
        repos: Annotated[RepositoryManager, Depends()],
        current_user: Annotated[Auth, Depends(authenticate)],
    ) -> None:
        quota = await repos.plan_quota.get_for_organization(
            current_user.organization_id, metric
        )
        if quota is None or quota.limit_value is None:
            return
        count = await repos.usage_record.get_count(
            current_user.organization_id, metric, _current_period_start()
        )
        if count >= quota.limit_value:
            raise QuotaExceededException()

    return _check


async def track_usage(
    repos: RepositoryManager,
    organization_id: int,
    metric: UsageMetric,
) -> int:
    """Atomically increments the usage counter and returns the new count."""
    return await repos.usage_record.increment(
        organization_id, metric, _current_period_start()
    )
