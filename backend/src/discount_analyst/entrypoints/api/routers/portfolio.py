"""Latest submitted portfolio holdings from the most recent workflow run."""

from __future__ import annotations

import logfire
from fastapi import APIRouter

from discount_analyst.entrypoints.api.contracts.api import PortfolioResponse
from discount_analyst.entrypoints.api.deps import DbSession
from discount_analyst.adapters.persistence.crud.workflow_runs import (
    get_latest_portfolio_tickers,
)

router = APIRouter(tags=["portfolio"])


@router.get("")
def get_portfolio(session: DbSession) -> PortfolioResponse:
    tickers = get_latest_portfolio_tickers(session)
    out = tickers or []
    logfire.debug("Returned latest portfolio tickers", ticker_count=len(out))
    return PortfolioResponse(portfolio_tickers=out)
