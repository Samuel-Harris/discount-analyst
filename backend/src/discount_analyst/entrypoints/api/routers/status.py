"""Dashboard runtime status, including third-party package freshness."""

from __future__ import annotations

from fastapi import APIRouter, Request

from discount_analyst.adapters.observability.yfinance_freshness import (
    YfinanceFreshness,
    check_yfinance_freshness,
)
from discount_analyst.agents.tools.regulatory_data.cache import RegulatoryDataCache
from discount_analyst.agents.tools.regulatory_data.companies_house.store import (
    companies_house_cache_is_present,
)
from discount_analyst.config.settings import Settings
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
    settings: Settings = request.app.state.settings
    return DashboardStatusResponse(
        yfinance=YfinanceFreshnessResponse(
            installed_version=freshness.installed_version,
            latest_version=freshness.latest_version,
            is_outdated=freshness.is_outdated,
        ),
        sec_user_agent_configured=bool(settings.sec_user_agent.strip()),
        companies_house_cache_present=companies_house_cache_is_present(
            RegulatoryDataCache(settings.regulatory_data_cache_dir)
        ),
    )
