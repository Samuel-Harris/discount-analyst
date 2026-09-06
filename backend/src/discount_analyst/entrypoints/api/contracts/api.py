from __future__ import annotations

from datetime import datetime
from decimal import Decimal, ROUND_HALF_EVEN
from typing import Annotated, Self

from pydantic import AfterValidator, BaseModel, Field, PlainSerializer, model_validator
from pydantic.json_schema import WithJsonSchema

from discount_analyst.entrypoints.api.contracts.enums import (
    AgentNameSlug,
    CandidateGateStatusApi,
    DecisionTypeApi,
    EntryPathApi,
    ExecutionStatusApi,
    TickerRunStatusApi,
    WorkflowRunStatusApi,
)
from discount_analyst.domain.model_selection.model_name import ModelName

_STERLING_QUANTUM = Decimal("0.01")


def _quantize_sterling(value: Decimal) -> Decimal:
    return value.quantize(_STERLING_QUANTUM, rounding=ROUND_HALF_EVEN)


SterlingPounds = Annotated[
    Decimal,
    Field(ge=0),
    AfterValidator(_quantize_sterling),
    PlainSerializer(lambda value: float(value), return_type=float, when_used="json"),
    WithJsonSchema({"type": "number", "minimum": 0, "multipleOf": 0.01}),
]


class WorkflowRunListItem(BaseModel):
    id: str
    started_at: datetime
    completed_at: datetime | None
    status: WorkflowRunStatusApi
    is_mock: bool
    error_message: str | None
    ticker_run_count: int
    completed_ticker_run_count: int
    failed_ticker_run_count: int


class AgentExecutionSummary(BaseModel):
    id: str
    agent_name: AgentNameSlug
    status: ExecutionStatusApi
    started_at: datetime | None
    completed_at: datetime | None
    model_name: ModelName | None = None


class CandidateGateSummary(BaseModel):
    gate_status: CandidateGateStatusApi | None
    source_ticker: str
    resolved_ticker: str | None
    gate_failure_reason: str | None
    is_actively_trading: bool | None


class TickerRunDetail(BaseModel):
    id: str
    ticker: str
    company_name: str
    entry_path: EntryPathApi
    status: TickerRunStatusApi
    final_rating: str | None
    decision_type: DecisionTypeApi | None
    candidate_gate: CandidateGateSummary | None = None
    agent_executions: list[AgentExecutionSummary]


class WorkflowRunDetailResponse(BaseModel):
    id: str
    started_at: datetime
    completed_at: datetime | None
    status: WorkflowRunStatusApi
    is_mock: bool
    error_message: str | None
    can_retry_failed_agents: bool
    surveyor_execution: AgentExecutionSummary | None
    curator_execution: AgentExecutionSummary | None
    runs: list[TickerRunDetail]


class PortfolioPositionInput(BaseModel):
    ticker: str = Field(min_length=1)
    value_gbp: SterlingPounds

    @model_validator(mode="after")
    def strip_ticker(self) -> Self:
        ticker = self.ticker.strip()
        if not ticker:
            raise ValueError("Holding tickers must not be blank")
        self.ticker = ticker
        return self


class CreateWorkflowRunRequest(BaseModel):
    positions: list[PortfolioPositionInput] = Field(
        default_factory=list[PortfolioPositionInput]
    )
    cash_gbp: SterlingPounds
    suggestion_tickers: list[str] = Field(default_factory=list)
    is_mock: bool = False

    @model_validator(mode="after")
    def normalise_ledger(self) -> Self:
        holding_keys: dict[str, str] = {}
        for position in self.positions:
            key = position.ticker.casefold()
            previous = holding_keys.get(key)
            if previous is not None:
                raise ValueError(
                    "Holding tickers must be unique case-insensitively; "
                    f"{previous!r} and {position.ticker!r} collide."
                )
            holding_keys[key] = position.ticker

        suggestion_keys: dict[str, str] = {}
        kept_suggestions: list[str] = []
        for raw_ticker in self.suggestion_tickers:
            ticker = raw_ticker.strip()
            if not ticker:
                raise ValueError("Suggestion tickers must not be blank")
            key = ticker.casefold()
            if key in holding_keys:
                continue
            previous = suggestion_keys.get(key)
            if previous is not None:
                raise ValueError(
                    "Suggestion tickers must be unique case-insensitively; "
                    f"{previous!r} and {ticker!r} collide."
                )
            suggestion_keys[key] = ticker
            kept_suggestions.append(ticker)
        self.suggestion_tickers = kept_suggestions
        return self


class ProfilerRunCreated(BaseModel):
    run_id: str
    ticker: str


class CreateWorkflowRunResponse(BaseModel):
    workflow_run_id: str
    profiler_runs: list[ProfilerRunCreated]
    surveyor_started: bool = True


class ConversationResponse(BaseModel):
    system_prompt: str
    messages_json: str
    assistant_response: str


class PortfolioResponse(BaseModel):
    positions: list[PortfolioPositionInput]
    cash_gbp: SterlingPounds
    suggestion_tickers: list[str]


class YfinanceFreshnessResponse(BaseModel):
    installed_version: str
    latest_version: str | None
    is_outdated: bool


class DashboardStatusResponse(BaseModel):
    yfinance: YfinanceFreshnessResponse
