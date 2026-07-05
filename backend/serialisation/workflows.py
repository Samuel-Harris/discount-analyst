"""Map stored rows to HTTP contract models."""

from backend.contracts.api import (
    AgentExecutionSummary,
    CandidateGateSummary,
    SurveyorExecutionSummary,
    TickerRunDetail,
    WorkflowRunDetailResponse,
    WorkflowRunListItem,
)
from backend.contracts.enums import CandidateGateStatusApi
from backend.contracts.enums import (
    AgentNameSlug,
    DecisionTypeApi,
    EntryPathApi,
    ExecutionStatusApi,
    TickerRunStatusApi,
    WorkflowRunStatusApi,
)
from backend.contracts.workflow_rows import WorkflowRunDetailRecord, WorkflowRunListRow


def workflow_list_item(row: WorkflowRunListRow) -> WorkflowRunListItem:
    started_at = row["started_at"]
    assert started_at is not None
    return WorkflowRunListItem(
        id=row["id"],
        started_at=started_at,
        completed_at=row["completed_at"],
        status=WorkflowRunStatusApi(row["status"]),
        is_mock=row["is_mock"],
        error_message=row["error_message"],
        ticker_run_count=row["ticker_run_count"],
        completed_ticker_run_count=row["completed_ticker_run_count"],
        failed_ticker_run_count=row["failed_ticker_run_count"],
    )


def workflow_detail(
    workflow_run_detail_record: WorkflowRunDetailRecord,
) -> WorkflowRunDetailResponse:
    surveyor_execution = workflow_run_detail_record.get("surveyor_execution")
    surveyor_summary = None
    if surveyor_execution:
        surveyor_summary = SurveyorExecutionSummary(
            id=surveyor_execution["id"],
            agent_name=AgentNameSlug(surveyor_execution["agent_name"]),
            status=ExecutionStatusApi(surveyor_execution["status"]),
            started_at=surveyor_execution["started_at"],
            completed_at=surveyor_execution["completed_at"],
            model_name=surveyor_execution["model_name"],
        )
    runs: list[TickerRunDetail] = []
    for run in workflow_run_detail_record["runs"]:
        agents = [
            AgentExecutionSummary(
                id=agent_execution["id"],
                agent_name=AgentNameSlug(agent_execution["agent_name"]),
                status=ExecutionStatusApi(agent_execution["status"]),
                started_at=agent_execution["started_at"],
                completed_at=agent_execution["completed_at"],
                model_name=agent_execution["model_name"],
            )
            for agent_execution in run["agent_executions"]
        ]
        dt = run["decision_type"]
        gate_row = run.get("candidate_gate")
        candidate_gate = None
        if gate_row is not None:
            gate_status = gate_row["gate_status"]
            candidate_gate = CandidateGateSummary(
                gate_status=CandidateGateStatusApi(gate_status)
                if gate_status
                else None,
                source_ticker=gate_row["source_ticker"],
                resolved_ticker=gate_row["resolved_ticker"],
                gate_failure_reason=gate_row["gate_failure_reason"],
                is_actively_trading=gate_row["is_actively_trading"],
            )
        runs.append(
            TickerRunDetail(
                id=run["id"],
                ticker=run["ticker"],
                company_name=run["company_name"],
                entry_path=EntryPathApi(run["entry_path"]),
                status=TickerRunStatusApi(run["status"]),
                final_rating=run["final_rating"],
                decision_type=DecisionTypeApi(dt) if dt else None,
                candidate_gate=candidate_gate,
                agent_executions=agents,
            )
        )
    detail_started_at = workflow_run_detail_record["started_at"]
    assert detail_started_at is not None
    return WorkflowRunDetailResponse(
        id=workflow_run_detail_record["id"],
        started_at=detail_started_at,
        completed_at=workflow_run_detail_record["completed_at"],
        status=WorkflowRunStatusApi(workflow_run_detail_record["status"]),
        is_mock=workflow_run_detail_record["is_mock"],
        error_message=workflow_run_detail_record["error_message"],
        surveyor_execution=surveyor_summary,
        runs=runs,
    )
