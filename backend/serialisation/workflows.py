"""Map stored rows to HTTP contract models."""

from backend.contracts.api import (
    AgentExecutionSummary,
    SurveyorExecutionSummary,
    TickerRunDetail,
    WorkflowRunDetailResponse,
    WorkflowRunListItem,
)
from backend.common.primitive_types import AgentNameSlug
from backend.contracts.enums import (
    DecisionTypeApi,
    EntryPathApi,
    ExecutionStatusApi,
    TickerRunStatusApi,
    WorkflowRunStatusApi,
)


def workflow_list_item(row: dict) -> WorkflowRunListItem:
    return WorkflowRunListItem(
        id=row["id"],
        started_at=row["started_at"],
        completed_at=row["completed_at"],
        status=WorkflowRunStatusApi(row["status"]),
        is_mock=row["is_mock"],
        error_message=row["error_message"],
        ticker_run_count=row["ticker_run_count"],
        completed_ticker_run_count=row["completed_ticker_run_count"],
        failed_ticker_run_count=row["failed_ticker_run_count"],
    )


def workflow_detail(d: dict) -> WorkflowRunDetailResponse:
    se = d.get("surveyor_execution")
    surveyor_summary = None
    if se:
        surveyor_summary = SurveyorExecutionSummary(
            id=se["id"],
            agent_name=AgentNameSlug(se["agent_name"]),
            status=ExecutionStatusApi(se["status"]),
            started_at=se["started_at"],
            completed_at=se["completed_at"],
        )
    runs: list[TickerRunDetail] = []
    for r in d["runs"]:
        agents = [
            AgentExecutionSummary(
                id=a["id"],
                agent_name=AgentNameSlug(a["agent_name"]),
                status=ExecutionStatusApi(a["status"]),
                started_at=a["started_at"],
                completed_at=a["completed_at"],
            )
            for a in r["agent_executions"]
        ]
        dt = r["decision_type"]
        runs.append(
            TickerRunDetail(
                id=r["id"],
                ticker=r["ticker"],
                company_name=r["company_name"],
                entry_path=EntryPathApi(r["entry_path"]),
                status=TickerRunStatusApi(r["status"]),
                final_rating=r["final_rating"],
                decision_type=DecisionTypeApi(dt) if dt else None,
                agent_executions=agents,
            )
        )
    return WorkflowRunDetailResponse(
        id=d["id"],
        started_at=d["started_at"],
        completed_at=d["completed_at"],
        status=WorkflowRunStatusApi(d["status"]),
        is_mock=d["is_mock"],
        error_message=d["error_message"],
        surveyor_execution=surveyor_summary,
        runs=runs,
    )
