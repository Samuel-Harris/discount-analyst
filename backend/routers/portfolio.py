"""Latest submitted portfolio holdings from the most recent workflow run."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Request
from sqlmodel import Session

from backend.contracts.api import PortfolioResponse
from backend.crud.workflow_runs import get_latest_portfolio_tickers

router = APIRouter(prefix="/portfolio", tags=["portfolio"])


def get_session(request: Request):
    session_factory = request.app.state.db_session_factory
    with session_factory() as session:
        yield session


DbSession = Annotated[Session, Depends(get_session)]


@router.get("")
def get_portfolio(session: DbSession) -> PortfolioResponse:
    tickers = get_latest_portfolio_tickers(session)
    return PortfolioResponse(portfolio_tickers=tickers or [])
