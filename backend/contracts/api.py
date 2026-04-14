from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from backend.contracts.enums import (
    AgentNameSlug,
    DecisionTypeApi,
    EntryPathApi,
    ExecutionStatusApi,
    TickerRunStatusApi,
    WorkflowRunStatusApi,
)


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


class TickerRunDetail(BaseModel):
    id: str
    ticker: str
    company_name: str
    entry_path: EntryPathApi
    status: TickerRunStatusApi
    final_rating: str | None
    decision_type: DecisionTypeApi | None
    agent_executions: list[AgentExecutionSummary]


class SurveyorExecutionSummary(BaseModel):
    id: str
    agent_name: AgentNameSlug
    status: ExecutionStatusApi
    started_at: datetime | None
    completed_at: datetime | None


class WorkflowRunDetailResponse(BaseModel):
    id: str
    started_at: datetime
    completed_at: datetime | None
    status: WorkflowRunStatusApi
    is_mock: bool
    error_message: str | None
    surveyor_execution: SurveyorExecutionSummary | None
    runs: list[TickerRunDetail]


class CreateWorkflowRunRequest(BaseModel):
    portfolio_tickers: list[str] = Field(min_length=0)
    is_mock: bool = False


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
    portfolio_tickers: list[str]
