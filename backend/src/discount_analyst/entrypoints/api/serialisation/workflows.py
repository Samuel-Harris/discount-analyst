"""Map stored rows to HTTP contract models."""

from discount_analyst.entrypoints.api.contracts.api import (
    AgentExecutionSummary,
    CandidateGateSummary,
    TickerRunDetail,
    WorkflowRunDetailResponse,
    WorkflowRunListItem,
)
from discount_analyst.entrypoints.api.contracts.enums import CandidateGateStatusApi
from discount_analyst.entrypoints.api.contracts.enums import (
    AgentNameSlug,
    DecisionTypeApi,
    EntryPathApi,
    ExecutionStatusApi,
    TickerRunStatusApi,
    WorkflowRunStatusApi,
)
from discount_analyst.adapters.persistence.workflow_rows import (
    AgentExecutionRow,
    TickerRunRow,
    WorkflowRunDetailRecord,
    WorkflowRunListRow,
)


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
    started_at = workflow_run_detail_record["started_at"]
    assert started_at is not None
    return WorkflowRunDetailResponse(
        id=workflow_run_detail_record["id"],
        started_at=started_at,
        completed_at=workflow_run_detail_record["completed_at"],
        status=WorkflowRunStatusApi(workflow_run_detail_record["status"]),
        is_mock=workflow_run_detail_record["is_mock"],
        error_message=workflow_run_detail_record["error_message"],
        can_retry_failed_agents=workflow_run_detail_record["can_retry_failed_agents"],
        surveyor_execution=_optional_execution_summary(
            workflow_run_detail_record["surveyor_execution"]
        ),
        allocator_execution=_optional_execution_summary(
            workflow_run_detail_record["allocator_execution"]
        ),
        runs=[_ticker_run_detail(run) for run in workflow_run_detail_record["runs"]],
    )


def _optional_execution_summary(
    row: AgentExecutionRow | None,
) -> AgentExecutionSummary | None:
    if row is None:
        return None
    return _execution_summary(row)


def _execution_summary(row: AgentExecutionRow) -> AgentExecutionSummary:
    return AgentExecutionSummary(
        id=row["id"],
        agent_name=AgentNameSlug(row["agent_name"]),
        status=ExecutionStatusApi(row["status"]),
        started_at=row["started_at"],
        completed_at=row["completed_at"],
        model_name=row["model_name"],
    )


def _ticker_run_detail(run: TickerRunRow) -> TickerRunDetail:
    decision_type = run["decision_type"]
    gate_row = run.get("candidate_gate")
    candidate_gate = None
    if gate_row is not None:
        gate_status = gate_row["gate_status"]
        candidate_gate = CandidateGateSummary(
            gate_status=CandidateGateStatusApi(gate_status) if gate_status else None,
            source_ticker=gate_row["source_ticker"],
            resolved_ticker=gate_row["resolved_ticker"],
            gate_failure_reason=gate_row["gate_failure_reason"],
            is_actively_trading=gate_row["is_actively_trading"],
        )
    return TickerRunDetail(
        id=run["id"],
        ticker=run["ticker"],
        company_name=run["company_name"],
        entry_path=EntryPathApi(run["entry_path"]),
        status=TickerRunStatusApi(run["status"]),
        final_rating=run["final_rating"],
        decision_type=DecisionTypeApi(decision_type) if decision_type else None,
        candidate_gate=candidate_gate,
        agent_executions=[
            _execution_summary(agent_execution)
            for agent_execution in run["agent_executions"]
        ],
    )
