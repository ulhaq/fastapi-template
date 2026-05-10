from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.testclient import TestClient

from src.billing.dependencies import require_quota
from src.enums import UsageMetric
from src.main import app
from src.models.billing import PlanQuota, UsageRecord
from tests.conftest import TestSessionLocal

# ---------------------------------------------------------------------------
# Test-only route - exercises require_quota in a real request cycle
# ---------------------------------------------------------------------------

_test_router = APIRouter()


@_test_router.get("/test-quota-gate")
async def _quota_gated_endpoint(
    _: Annotated[None, Depends(require_quota(UsageMetric.API_REQUESTS))],
) -> dict:
    return {"ok": True}


app.include_router(_test_router, prefix="/v1")

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_FREE_PLAN_ID = 1  # seeded in conftest


async def _add_quota(plan_id: int, metric: str, limit_value: int | None) -> None:
    async with TestSessionLocal() as session:
        session.add(PlanQuota(plan_id=plan_id, metric=metric, limit_value=limit_value))
        await session.commit()


async def _add_usage(organization_id: int, metric: str, count: int) -> None:
    async with TestSessionLocal() as session:
        session.add(
            UsageRecord(
                organization_id=organization_id,
                metric=metric,
                period_start=date.today().replace(day=1),
                count=count,
            )
        )
        await session.commit()


# ---------------------------------------------------------------------------
# GET /v1/billing/usage
# ---------------------------------------------------------------------------


def test_get_usage_requires_auth(client: TestClient) -> None:
    response = client.get("/v1/billing/usage")
    assert response.status_code == 401


def test_get_usage_empty_when_no_quotas_configured(
    admin_authenticated: TestClient,
) -> None:
    response = admin_authenticated.get("/v1/billing/usage")
    assert response.status_code == 200
    rs = response.json()
    assert rs["usage"] == []
    assert rs["period_start"] == date.today().replace(day=1).isoformat()


async def test_get_usage_returns_zero_count_when_no_records(
    admin_authenticated: TestClient,
) -> None:
    await _add_quota(_FREE_PLAN_ID, UsageMetric.API_REQUESTS, 1000)

    response = admin_authenticated.get("/v1/billing/usage")
    assert response.status_code == 200
    rs = response.json()
    assert len(rs["usage"]) == 1
    item = rs["usage"][0]
    assert item["metric"] == UsageMetric.API_REQUESTS
    assert item["count"] == 0
    assert item["limit"] == 1000


async def test_get_usage_returns_actual_count(
    admin_authenticated: TestClient,
) -> None:
    await _add_quota(_FREE_PLAN_ID, UsageMetric.API_REQUESTS, 500)
    await _add_usage(organization_id=1, metric=UsageMetric.API_REQUESTS, count=42)

    response = admin_authenticated.get("/v1/billing/usage")
    assert response.status_code == 200
    item = response.json()["usage"][0]
    assert item["count"] == 42
    assert item["limit"] == 500


async def test_get_usage_unlimited_plan_shows_none_limit(
    admin_authenticated: TestClient,
) -> None:
    await _add_quota(_FREE_PLAN_ID, UsageMetric.API_REQUESTS, None)

    response = admin_authenticated.get("/v1/billing/usage")
    assert response.status_code == 200
    item = response.json()["usage"][0]
    assert item["limit"] is None


async def test_get_usage_is_org_isolated(
    admin_authenticated: TestClient,
    organization2_admin_authenticated: TestClient,
) -> None:
    await _add_quota(_FREE_PLAN_ID, UsageMetric.API_REQUESTS, 100)
    await _add_usage(organization_id=1, metric=UsageMetric.API_REQUESTS, count=10)
    await _add_usage(organization_id=2, metric=UsageMetric.API_REQUESTS, count=77)

    org1_item = admin_authenticated.get("/v1/billing/usage").json()["usage"][0]  # type: ignore[union-attr]
    org2_item = organization2_admin_authenticated.get("/v1/billing/usage").json()[  # type: ignore[union-attr]
        "usage"
    ][0]

    assert org1_item["count"] == 10
    assert org2_item["count"] == 77


# ---------------------------------------------------------------------------
# Plan response includes plan_quotas
# ---------------------------------------------------------------------------


async def test_plan_list_includes_plan_quotas(
    admin_authenticated: TestClient,
) -> None:
    await _add_quota(_FREE_PLAN_ID, UsageMetric.API_REQUESTS, 100)

    response = admin_authenticated.get("/v1/billing/plans")
    assert response.status_code == 200
    free_plan = next(p for p in response.json() if p["name"] == "Free")
    assert len(free_plan["plan_quotas"]) == 1
    quota = free_plan["plan_quotas"][0]
    assert quota["metric"] == UsageMetric.API_REQUESTS
    assert quota["limit_value"] == 100


def test_plan_list_plan_quotas_empty_when_none_configured(
    admin_authenticated: TestClient,
) -> None:
    response = admin_authenticated.get("/v1/billing/plans")
    assert response.status_code == 200
    free_plan = next(p for p in response.json() if p["name"] == "Free")
    assert free_plan["plan_quotas"] == []


# ---------------------------------------------------------------------------
# require_quota dependency
# ---------------------------------------------------------------------------


def test_quota_allows_request_when_no_quota_configured(
    admin_authenticated: TestClient,
) -> None:
    response = admin_authenticated.get("/v1/test-quota-gate")
    assert response.status_code == 200


async def test_quota_allows_request_under_limit(
    admin_authenticated: TestClient,
) -> None:
    await _add_quota(_FREE_PLAN_ID, UsageMetric.API_REQUESTS, 10)
    await _add_usage(organization_id=1, metric=UsageMetric.API_REQUESTS, count=9)

    response = admin_authenticated.get("/v1/test-quota-gate")
    assert response.status_code == 200


async def test_quota_blocks_request_at_limit(
    admin_authenticated: TestClient,
) -> None:
    await _add_quota(_FREE_PLAN_ID, UsageMetric.API_REQUESTS, 10)
    await _add_usage(organization_id=1, metric=UsageMetric.API_REQUESTS, count=10)

    response = admin_authenticated.get("/v1/test-quota-gate")
    assert response.status_code == 429
    assert response.json()["error_code"] == "quota_exceeded"


async def test_quota_blocks_request_over_limit(
    admin_authenticated: TestClient,
) -> None:
    await _add_quota(_FREE_PLAN_ID, UsageMetric.API_REQUESTS, 5)
    await _add_usage(organization_id=1, metric=UsageMetric.API_REQUESTS, count=99)

    response = admin_authenticated.get("/v1/test-quota-gate")
    assert response.status_code == 429


async def test_quota_allows_unlimited_plan(
    admin_authenticated: TestClient,
) -> None:
    await _add_quota(_FREE_PLAN_ID, UsageMetric.API_REQUESTS, None)
    await _add_usage(organization_id=1, metric=UsageMetric.API_REQUESTS, count=9999)

    response = admin_authenticated.get("/v1/test-quota-gate")
    assert response.status_code == 200


async def test_quota_is_org_isolated(
    admin_authenticated: TestClient,
    organization2_admin_authenticated: TestClient,
) -> None:
    await _add_quota(_FREE_PLAN_ID, UsageMetric.API_REQUESTS, 5)
    # Only org 2 is at limit
    await _add_usage(organization_id=2, metric=UsageMetric.API_REQUESTS, count=5)

    # Org 1 is under limit - allowed
    assert admin_authenticated.get("/v1/test-quota-gate").status_code == 200  # type: ignore[union-attr]

    # Org 2 is at limit - blocked
    assert (
        organization2_admin_authenticated.get("/v1/test-quota-gate").status_code == 429  # type: ignore[union-attr]
    )
