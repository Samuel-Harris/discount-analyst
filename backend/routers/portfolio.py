"""Latest submitted portfolio holdings from the most recent workflow run."""

from __future__ import annotations

from fastapi import APIRouter

from backend.contracts.api import PortfolioResponse
from backend.deps import DbSession
from backend.crud.workflow_runs import get_latest_portfolio_tickers

router = APIRouter(tags=["portfolio"])


@router.get("")
def get_portfolio(session: DbSession) -> PortfolioResponse:
    tickers = get_latest_portfolio_tickers(session)
    return PortfolioResponse(portfolio_tickers=tickers or [])
