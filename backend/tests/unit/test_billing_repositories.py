# mypy: disable-error-code="no-untyped-def"
"""Tests for billing repositories and billing/dependencies.py."""

from datetime import UTC, date, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.billing.dependencies import (
    _current_period_start,
    get_billing_provider,
    track_usage,
)
from src.billing.stripe_provider import StripeProvider
from src.core.exceptions import QuotaExceededException
from src.core.security import Auth
from src.enums import Permission as PermEnum
from src.enums import PlanFeature, UsageMetric
from src.models.billing import (
    Plan,
    PlanPrice,
    PlanQuota,
    WebhookEvent,
)
from src.models.organization import Organization
from src.repositories.repository_manager import RepositoryManager
from tests.conftest import TestSessionLocal


def _admin_auth(org_id: int = 1) -> Auth:
    return Auth(
        id=1,
        name="Alice",
        email="admin@example.org",
        organization_id=org_id,
        roles=["Owner"],
        permissions=[p.value for p in PermEnum],
    )


# ---------------------------------------------------------------------------
# billing/dependencies.py
# ---------------------------------------------------------------------------


def test_get_billing_provider_returns_stripe_provider():
    provider = get_billing_provider()
    assert isinstance(provider, StripeProvider)


def test_current_period_start_is_first_of_month():
    d = _current_period_start()
    assert d.day == 1
    assert isinstance(d, date)


async def test_require_quota_no_quota_defined_passes():
    """When no quota is configured, the check passes without raising."""
    from src.billing.dependencies import require_quota

    repos = MagicMock()
    repos.plan_quota.get_for_organization = AsyncMock(return_value=None)
    auth = _admin_auth()

    check = require_quota(UsageMetric.API_REQUESTS)
    # Directly call the inner _check function
    _ = check.__wrapped__ if hasattr(check, "__wrapped__") else None
    # require_quota returns the inner _check coroutine function directly
    await check(repos=repos, current_user=auth)


async def test_require_quota_within_limit_passes():
    from src.billing.dependencies import require_quota

    quota = MagicMock()
    quota.limit_value = 100
    repos = MagicMock()
    repos.plan_quota.get_for_organization = AsyncMock(return_value=quota)
    repos.usage_record.get_count = AsyncMock(return_value=50)
    auth = _admin_auth()

    check = require_quota(UsageMetric.API_REQUESTS)
    await check(repos=repos, current_user=auth)  # should not raise


async def test_require_quota_unlimited_passes():
    """quota.limit_value = None means unlimited."""
    from src.billing.dependencies import require_quota

    quota = MagicMock()
    quota.limit_value = None
    repos = MagicMock()
    repos.plan_quota.get_for_organization = AsyncMock(return_value=quota)
    auth = _admin_auth()

    check = require_quota(UsageMetric.API_REQUESTS)
    await check(repos=repos, current_user=auth)


async def test_require_quota_exceeded_raises():
    from src.billing.dependencies import require_quota

    quota = MagicMock()
    quota.limit_value = 10
    repos = MagicMock()
    repos.plan_quota.get_for_organization = AsyncMock(return_value=quota)
    repos.usage_record.get_count = AsyncMock(return_value=10)
    auth = _admin_auth()

    check = require_quota(UsageMetric.API_REQUESTS)
    with pytest.raises(QuotaExceededException):
        await check(repos=repos, current_user=auth)


async def test_track_usage_calls_increment():
    repos = MagicMock()
    repos.usage_record.increment = AsyncMock(return_value=5)

    result = await track_usage(
        repos, organization_id=1, metric=UsageMetric.API_REQUESTS
    )
    assert result == 5
    repos.usage_record.increment.assert_awaited_once()


# ---------------------------------------------------------------------------
# PlanRepository
# ---------------------------------------------------------------------------


async def test_plan_get_by_external_product_id_found():
    async with TestSessionLocal() as session:
        async with session.begin():
            plan = Plan(
                name="Test Plan", is_active=True, external_product_id="prod_abc"
            )
            session.add(plan)
            await session.flush()
            repos = RepositoryManager(session)
            result = await repos.plan.get_by_external_product_id("prod_abc")
            assert result is not None
            assert result.external_product_id == "prod_abc"


async def test_plan_get_by_external_product_id_not_found():
    async with TestSessionLocal() as session:
        async with session.begin():
            repos = RepositoryManager(session)
            result = await repos.plan.get_by_external_product_id("prod_nonexistent")
            assert result is None


async def test_plan_get_active_plans():
    async with TestSessionLocal() as session:
        async with session.begin():
            repos = RepositoryManager(session)
            plans = await repos.plan.get_active_plans()
            assert len(plans) >= 1
            assert all(p.is_active for p in plans)


# ---------------------------------------------------------------------------
# PlanPriceRepository
# ---------------------------------------------------------------------------


async def test_plan_price_get_by_plan():
    async with TestSessionLocal() as session:
        async with session.begin():
            repos = RepositoryManager(session)
            # Get the seeded free plan (id=1)
            plans = await repos.plan.get_active_plans()
            free_plan = plans[0]
            prices = await repos.plan_price.get_by_plan(free_plan.id)
            assert len(prices) >= 1


async def test_plan_price_get_by_external_price_id_found():
    async with TestSessionLocal() as session:
        async with session.begin():
            plan = Plan(name="Ext Plan", is_active=True, external_product_id="prod_ext")
            session.add(plan)
            await session.flush()
            price = PlanPrice(
                plan_id=plan.id,
                amount=500,
                currency="usd",
                interval="month",
                interval_count=1,
                external_price_id="price_ext_abc",
                is_active=True,
            )
            session.add(price)
            await session.flush()
            repos = RepositoryManager(session)
            result = await repos.plan_price.get_by_external_price_id("price_ext_abc")
            assert result is not None
            assert result.external_price_id == "price_ext_abc"


async def test_plan_price_get_by_external_price_id_not_found():
    async with TestSessionLocal() as session:
        async with session.begin():
            repos = RepositoryManager(session)
            result = await repos.plan_price.get_by_external_price_id(
                "price_nonexistent"
            )
            assert result is None


async def test_plan_price_get_free_price():
    async with TestSessionLocal() as session:
        async with session.begin():
            repos = RepositoryManager(session)
            result = await repos.plan_price.get_free_price()
            assert result is not None
            assert result.amount == 0


async def test_plan_price_get_highest_price():
    async with TestSessionLocal() as session:
        async with session.begin():
            plan = Plan(
                name="Paid Plan", is_active=True, external_product_id="prod_paid"
            )
            session.add(plan)
            await session.flush()
            price = PlanPrice(
                plan_id=plan.id,
                amount=999,
                currency="usd",
                interval="month",
                interval_count=1,
                external_price_id="price_highest",
                is_active=True,
            )
            session.add(price)
            await session.flush()
            repos = RepositoryManager(session)
            result = await repos.plan_price.get_highest_price()
            assert result is not None
            assert result.amount == 999


async def test_plan_price_get_active_by_plan():
    async with TestSessionLocal() as session:
        async with session.begin():
            repos = RepositoryManager(session)
            plans = await repos.plan.get_active_plans()
            free_plan = plans[0]
            prices = await repos.plan_price.get_active_by_plan(free_plan.id)
            assert len(prices) >= 1
            assert all(p.is_active for p in prices)


async def test_plan_price_has_active_subscriptions_true():
    """The seeded free price has an active subscription for org 1."""
    async with TestSessionLocal() as session:
        async with session.begin():
            repos = RepositoryManager(session)
            free_price = await repos.plan_price.get_free_price()
            assert free_price is not None
            result = await repos.plan_price.has_active_subscriptions(free_price.id)
            assert result is True


async def test_plan_price_has_active_subscriptions_false():
    async with TestSessionLocal() as session:
        async with session.begin():
            plan = Plan(name="No Sub Plan", is_active=True)
            session.add(plan)
            await session.flush()
            price = PlanPrice(
                plan_id=plan.id,
                amount=100,
                currency="usd",
                interval="month",
                interval_count=1,
                is_active=True,
            )
            session.add(price)
            await session.flush()
            repos = RepositoryManager(session)
            result = await repos.plan_price.has_active_subscriptions(price.id)
            assert result is False


# ---------------------------------------------------------------------------
# PlanFeatureRepository
# ---------------------------------------------------------------------------


async def test_plan_feature_get_features_for_organization():
    """Org 1 has an active free subscription; free plan has API_ACCESS feature."""
    async with TestSessionLocal() as session:
        async with session.begin():
            repos = RepositoryManager(session)
            features = await repos.plan_feature.get_features_for_organization(1)
            assert PlanFeature.API_ACCESS in features


# ---------------------------------------------------------------------------
# SubscriptionRepository
# ---------------------------------------------------------------------------


async def test_subscription_get_active_for_organization_found():
    async with TestSessionLocal() as session:
        async with session.begin():
            repos = RepositoryManager(session)
            repos.subscription.set_organization_scope(1)
            result = await repos.subscription.get_active_for_organization(1)
            assert result is not None
            assert result.status == "active"


async def test_subscription_get_active_for_organization_not_found():
    async with TestSessionLocal() as session:
        async with session.begin():
            repos = RepositoryManager(session)
            result = await repos.subscription.get_active_for_organization(9999)
            assert result is None


async def test_subscription_get_active_for_organization_locked():
    async with TestSessionLocal() as session:
        async with session.begin():
            repos = RepositoryManager(session)
            repos.subscription.set_organization_scope(1)
            result = await repos.subscription.get_active_for_organization_locked(1)
            assert result is not None


async def _fresh_org(session) -> int:
    """Create and flush a new organization, returning its id."""
    org = Organization(name="Temp Org")
    session.add(org)
    await session.flush()
    return org.id


async def test_subscription_get_by_external_subscription_id_found():
    async with TestSessionLocal() as session:
        async with session.begin():
            org_id = await _fresh_org(session)
            repos = RepositoryManager(session)
            free_price = await repos.plan_price.get_free_price()
            assert free_price is not None
            sub = await repos.subscription.create(
                organization_id=org_id,
                plan_price_id=free_price.id,
                status="active",
                external_subscription_id="sub_ext_find_me",
            )
            result = await repos.subscription.get_by_external_subscription_id(
                "sub_ext_find_me"
            )
            assert result is not None
            assert result.id == sub.id


async def test_subscription_get_by_external_subscription_id_not_found():
    async with TestSessionLocal() as session:
        async with session.begin():
            repos = RepositoryManager(session)
            result = await repos.subscription.get_by_external_subscription_id(
                "sub_nope"
            )
            assert result is None


async def test_subscription_get_by_external_subscription_id_locked():
    async with TestSessionLocal() as session:
        async with session.begin():
            org_id = await _fresh_org(session)
            repos = RepositoryManager(session)
            free_price = await repos.plan_price.get_free_price()
            assert free_price is not None
            await repos.subscription.create(
                organization_id=org_id,
                plan_price_id=free_price.id,
                status="active",
                external_subscription_id="sub_ext_locked",
            )
            result = await repos.subscription.get_by_external_subscription_id_locked(
                "sub_ext_locked"
            )
            assert result is not None


async def test_subscription_get_stale_incomplete():
    async with TestSessionLocal() as session:
        async with session.begin():
            org_id = await _fresh_org(session)
            repos = RepositoryManager(session)
            free_price = await repos.plan_price.get_free_price()
            assert free_price is not None
            stale_sub = await repos.subscription.create(
                organization_id=org_id,
                plan_price_id=free_price.id,
                status="incomplete",
            )
            stale_sub.created_at = datetime.now(UTC) - timedelta(days=2)
            session.add(stale_sub)
            await session.flush()

            threshold = datetime.now(UTC) - timedelta(days=1)
            results = await repos.subscription.get_stale_incomplete_subscriptions(
                threshold
            )
            assert any(s.id == stale_sub.id for s in results)


async def test_subscription_bulk_cancel_stale_incomplete():
    async with TestSessionLocal() as session:
        async with session.begin():
            org_id = await _fresh_org(session)
            repos = RepositoryManager(session)
            free_price = await repos.plan_price.get_free_price()
            assert free_price is not None
            stale_sub = await repos.subscription.create(
                organization_id=org_id,
                plan_price_id=free_price.id,
                status="incomplete",
            )
            stale_sub.created_at = datetime.now(UTC) - timedelta(days=2)
            session.add(stale_sub)
            await session.flush()

            threshold = datetime.now(UTC) - timedelta(days=1)
            count = await repos.subscription.bulk_cancel_stale_incomplete(threshold)
            assert count >= 1


async def test_subscription_acquire_checkout_lock():
    """pg_advisory_xact_lock is mocked to SELECT 1 by conftest fixture."""
    async with TestSessionLocal() as session:
        async with session.begin():
            repos = RepositoryManager(session)
            repos.subscription.set_organization_scope(1)
            # Should not raise
            await repos.subscription.acquire_checkout_lock(1)


async def test_subscription_create_or_get_active():
    async with TestSessionLocal() as session:
        async with session.begin():
            repos = RepositoryManager(session)
            free_price = await repos.plan_price.get_free_price()
            assert free_price is not None
            sub = await repos.subscription.create_or_get_active(
                organization_id=1,
                plan_price_id=free_price.id,
                status="incomplete",
            )
            assert sub is not None


# ---------------------------------------------------------------------------
# PlanQuotaRepository
# ---------------------------------------------------------------------------


async def test_plan_quota_get_for_organization():
    """Create a quota for the free plan, verify it's returned for org 1's active sub."""
    async with TestSessionLocal() as session:
        async with session.begin():
            repos = RepositoryManager(session)
            free_price = await repos.plan_price.get_free_price()
            assert free_price is not None
            plan_id = free_price.plan_id
            quota = PlanQuota(
                plan_id=plan_id, metric=UsageMetric.API_REQUESTS, limit_value=100
            )
            session.add(quota)
            await session.flush()

            result = await repos.plan_quota.get_for_organization(
                1, UsageMetric.API_REQUESTS
            )
            assert result is not None
            assert result.limit_value == 100


async def test_plan_quota_get_quotas_for_organization():
    async with TestSessionLocal() as session:
        async with session.begin():
            repos = RepositoryManager(session)
            free_price = await repos.plan_price.get_free_price()
            assert free_price is not None
            plan_id = free_price.plan_id
            quota = PlanQuota(
                plan_id=plan_id, metric=UsageMetric.API_REQUESTS, limit_value=50
            )
            session.add(quota)
            await session.flush()

            results = await repos.plan_quota.get_quotas_for_organization(1)
            assert len(results) >= 1


# ---------------------------------------------------------------------------
# UsageRecordRepository
# ---------------------------------------------------------------------------


async def test_usage_record_get_count_zero():
    async with TestSessionLocal() as session:
        async with session.begin():
            repos = RepositoryManager(session)
            count = await repos.usage_record.get_count(
                organization_id=1,
                metric=UsageMetric.API_REQUESTS,
                period_start=date.today(),
            )
            assert count == 0


async def test_usage_record_get_for_organization_empty():
    async with TestSessionLocal() as session:
        async with session.begin():
            repos = RepositoryManager(session)
            records = await repos.usage_record.get_for_organization(
                organization_id=1,
                period_start=date.today(),
            )
            assert records == [] or len(records) == 0


# ---------------------------------------------------------------------------
# WebhookEventRepository
# ---------------------------------------------------------------------------


async def _create_webhook_event(
    session, external_event_id: str = "evt_test"
) -> WebhookEvent:
    repos = RepositoryManager(session)
    return await repos.webhook_event.create(
        external_event_id=external_event_id,
        event_type="customer.subscription.updated",
        status="received",
    )


async def test_webhook_event_get_by_external_event_id_found():
    async with TestSessionLocal() as session:
        async with session.begin():
            event = await _create_webhook_event(session, "evt_find_me")
            repos = RepositoryManager(session)
            result = await repos.webhook_event.get_by_external_event_id("evt_find_me")
            assert result is not None
            assert result.id == event.id


async def test_webhook_event_get_by_external_event_id_not_found():
    async with TestSessionLocal() as session:
        async with session.begin():
            repos = RepositoryManager(session)
            result = await repos.webhook_event.get_by_external_event_id("evt_nope")
            assert result is None


async def test_webhook_event_mark_processed():
    async with TestSessionLocal() as session:
        async with session.begin():
            event = await _create_webhook_event(session, "evt_process_me")
            repos = RepositoryManager(session)
            updated = await repos.webhook_event.mark_processed(event)
            assert updated.status == "processed"
            assert updated.processed_at is not None


async def test_webhook_event_mark_failed():
    async with TestSessionLocal() as session:
        async with session.begin():
            event = await _create_webhook_event(session, "evt_fail_me")
            repos = RepositoryManager(session)
            updated = await repos.webhook_event.mark_failed(
                event, "something went wrong"
            )
            assert updated.status == "failed"
            assert updated.error == "something went wrong"
