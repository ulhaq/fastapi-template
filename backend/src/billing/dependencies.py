from typing import Annotated

from fastapi import Depends

from src.billing.abc import BillingProviderABC
from src.billing.stripe_provider import StripeProvider
from src.core.config import settings


def get_billing_provider() -> BillingProviderABC:
    return StripeProvider(
        api_key=settings.stripe_secret_key.get_secret_value(),
        webhook_secret=settings.stripe_webhook_secret.get_secret_value(),
    )


BillingProviderDep = Annotated[BillingProviderABC, Depends(get_billing_provider)]
