"""Latest submitted portfolio holdings from the most recent workflow run."""

from __future__ import annotations

import logfire
from fastapi import APIRouter

from discount_analyst.entrypoints.api.contracts.api import (
    PortfolioPositionInput,
    PortfolioResponse,
)
from discount_analyst.entrypoints.api.deps import DbSession
from discount_analyst.adapters.persistence.crud.workflow_runs import (
    get_latest_portfolio_ledger,
)

router = APIRouter(tags=["portfolio"])


@router.get("")
def get_portfolio(session: DbSession) -> PortfolioResponse:
    ledger = get_latest_portfolio_ledger(session)
    logfire.debug(
        "Returned latest portfolio ledger",
        holding_count=len(ledger.positions),
        suggestion_count=len(ledger.suggestion_tickers),
    )
    return PortfolioResponse(
        positions=[
            PortfolioPositionInput(ticker=position.ticker, value_gbp=position.value_gbp)
            for position in ledger.positions
        ],
        cash_gbp=ledger.cash_gbp,
        suggestion_tickers=list(ledger.suggestion_tickers),
    )
