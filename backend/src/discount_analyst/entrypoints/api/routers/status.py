"""Dashboard runtime status, including third-party package freshness."""

from __future__ import annotations

from fastapi import APIRouter, Request

from discount_analyst.adapters.market_data.yfinance_freshness import (
    YfinanceFreshness,
    check_yfinance_freshness,
)
from discount_analyst.entrypoints.api.contracts.api import (
    DashboardStatusResponse,
    YfinanceFreshnessResponse,
)

router = APIRouter(tags=["status"])


@router.get("")
async def get_dashboard_status(request: Request) -> DashboardStatusResponse:
    freshness = getattr(request.app.state, "yfinance_freshness", None)
    if not isinstance(freshness, YfinanceFreshness):
        freshness = await check_yfinance_freshness()
        request.app.state.yfinance_freshness = freshness
    return DashboardStatusResponse(
        yfinance=YfinanceFreshnessResponse(
            installed_version=freshness.installed_version,
            latest_version=freshness.latest_version,
            is_outdated=freshness.is_outdated,
        )
    )
