"""Typed row shapes produced by workflow CRUD for API serialisation."""

from __future__ import annotations

from datetime import datetime
from typing import TypedDict


class WorkflowRunListRow(TypedDict):
    id: str
    started_at: datetime | None
    completed_at: datetime | None
    status: str
    is_mock: bool
    error_message: str | None
    ticker_run_count: int
    completed_ticker_run_count: int
    failed_ticker_run_count: int


class WorkflowRunHeaderRow(TypedDict):
    id: str
    started_at: datetime | None
    completed_at: datetime | None
    status: str
    is_mock: bool
    error_message: str | None
    portfolio_tickers: list[str]


class SurveyorExecutionRow(TypedDict):
    id: str
    agent_name: str
    status: str
    started_at: datetime | None
    completed_at: datetime | None


class AgentExecutionRow(TypedDict):
    id: str
    agent_name: str
    status: str
    started_at: datetime | None
    completed_at: datetime | None


class TickerRunRow(TypedDict):
    id: str
    ticker: str
    company_name: str
    entry_path: str
    status: str
    final_rating: str | None
    decision_type: str | None
    agent_executions: list[AgentExecutionRow]


class WorkflowRunDetailRecord(WorkflowRunHeaderRow):
    surveyor_execution: SurveyorExecutionRow | None
    runs: list[TickerRunRow]
