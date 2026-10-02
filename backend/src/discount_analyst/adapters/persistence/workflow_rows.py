"""Typed row shapes produced by workflow CRUD for API serialisation."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Literal, TypedDict

from discount_analyst.adapters.persistence.models import CandidateGateStatusDb
from discount_analyst.domain.model_selection.model_name import ModelName


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
    portfolio_value_gbp: Decimal | None


class CostFigureRow(TypedDict):
    state: Literal["amount", "unknown"]
    amount_usd: str | None


class AgentTypeCostRow(TypedDict):
    agent_name: str
    cost: CostFigureRow


class AgentExecutionRow(TypedDict):
    id: str
    agent_name: str
    status: str
    started_at: datetime | None
    completed_at: datetime | None
    model_name: ModelName | None
    cost: CostFigureRow


class CandidateGateRow(TypedDict):
    gate_status: CandidateGateStatusDb | None
    source_ticker: str
    resolved_ticker: str | None
    gate_failure_reason: str | None
    is_actively_trading: bool | None


class TickerRunRow(TypedDict):
    id: str
    ticker: str
    company_name: str
    entry_path: str
    status: str
    final_rating: str | None
    decision_type: str | None
    candidate_gate: CandidateGateRow | None
    agent_executions: list[AgentExecutionRow]


class TickerRunResumeRow(TypedDict):
    id: str
    ticker: str
    entry_path: str
    status: str
    is_existing_position: bool


class WorkflowRunDetailRecord(WorkflowRunHeaderRow):
    can_retry_failed_agents: bool
    surveyor_execution: AgentExecutionRow | None
    curator_execution: AgentExecutionRow | None
    cost_total: CostFigureRow
    cost_successful: CostFigureRow
    cost_unsuccessful: CostFigureRow
    cost_by_agent: list[AgentTypeCostRow]
    runs: list[TickerRunRow]
