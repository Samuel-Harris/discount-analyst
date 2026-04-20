"""Run and AgentExecution persistence (ticker lanes, status updates, outputs).

Status fields and structured output persistence are split so callers can compose
them inside a single explicit transaction (for example ``DashboardPipelineRunner._db``,
which commits after each operation batch).
"""

from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import select
from sqlmodel import Session, col

from backend.crud.agent_output_persistence import (
    persist_profiler_output,
    persist_surveyor_output,
    replace_appraiser_report,
    replace_evaluation_report,
    replace_mispricing_thesis,
    replace_research_report,
    upsert_run_final_decision,
)
from backend.crud.db_utils import (
    ACTIVE_EXECUTION_STATUSES,
    TERMINAL_EXECUTION_STATUSES,
    new_id,
    utc_now,
)
from backend.db.models import (
    AgentExecution,
    AgentNameDb,
    CandidateSnapshot,
    DecisionTypeDb,
    EntryPathDb,
    ExecutionStatusDb,
    Run,
    WorkflowAgentExecution,
    WorkflowRunStatusDb,
)
from discount_analyst.agents.arbiter.schema import ArbiterDecision
from discount_analyst.pipeline.schema import SentinelRejection, Verdict

_ACTIVE_RUN_STATUSES = frozenset({WorkflowRunStatusDb.RUNNING.value})
_TERMINAL_RUN_STATUSES = frozenset(
    {
        WorkflowRunStatusDb.COMPLETED.value,
        WorkflowRunStatusDb.FAILED.value,
        WorkflowRunStatusDb.CANCELLED.value,
    }
)


def insert_ticker_run_with_agents(
    session: Session,
    *,
    run_id: str,
    workflow_run_id: str,
    ticker: str,
    company_name: str,
    entry_path: str,
    is_existing_position: bool,
    is_mock: bool,
    agent_names: tuple[str, ...],
    candidate_snapshot_id: str | None = None,
) -> None:
    session.add(
        Run(
            id=run_id,
            workflow_run_id=workflow_run_id,
            candidate_snapshot_id=candidate_snapshot_id,
            ticker=ticker,
            company_name=company_name,
            started_at=utc_now(),
            completed_at=None,
            entry_path=EntryPathDb(entry_path),
            is_existing_position=is_existing_position,
            status=WorkflowRunStatusDb.RUNNING,
            is_mock=is_mock,
            error_message=None,
            final_rating=None,
            decision_type=None,
            recommended_action=None,
        )
    )
    for name in agent_names:
        session.add(
            AgentExecution(
                id=new_id(),
                run_id=run_id,
                agent_name=AgentNameDb(name),
                status=ExecutionStatusDb.PENDING,
                started_at=None,
                completed_at=None,
                error_message=None,
            )
        )


def get_agent_execution_id_by_run_and_agent(
    session: Session,
    *,
    run_id: str,
    agent_name: str,
) -> str | None:
    row = session.scalars(
        select(col(AgentExecution.id)).where(
            col(AgentExecution.run_id) == run_id,
            col(AgentExecution.agent_name) == AgentNameDb(agent_name),
        )
    ).first()
    return row


def get_workflow_surveyor_execution_id(
    session: Session, workflow_run_id: str
) -> str | None:
    row = session.scalars(
        select(col(WorkflowAgentExecution.id)).where(
            col(WorkflowAgentExecution.workflow_run_id) == workflow_run_id,
            col(WorkflowAgentExecution.agent_name) == AgentNameDb.SURVEYOR,
        )
    ).first()
    return row


def get_workflow_candidate_snapshot_id(
    session: Session, *, workflow_execution_id: str, ticker: str
) -> str | None:
    row = session.scalars(
        select(col(CandidateSnapshot.id)).where(
            col(CandidateSnapshot.workflow_agent_execution_id) == workflow_execution_id,
            col(CandidateSnapshot.ticker) == ticker,
        )
    ).first()
    return row


def apply_workflow_agent_execution_status(
    session: Session,
    *,
    execution_id: str,
    status: str,
    started_at: str | None = None,
    completed_at: str | None = None,
    error_message: str | None = None,
) -> WorkflowAgentExecution | None:
    """Update workflow-level execution status and timestamps only (no output rows)."""
    execution = session.get(WorkflowAgentExecution, execution_id)
    if execution is None:
        return None
    next_status = ExecutionStatusDb(status)
    current_status = execution.status.value
    if current_status == ExecutionStatusDb.CANCELLED.value and (
        next_status.value != ExecutionStatusDb.CANCELLED.value
    ):
        return None
    if (
        current_status in TERMINAL_EXECUTION_STATUSES
        and next_status.value in ACTIVE_EXECUTION_STATUSES
    ):
        return None
    execution.status = next_status
    if started_at is not None:
        execution.started_at = datetime.fromisoformat(started_at.replace("Z", "+00:00"))
    if completed_at is not None:
        execution.completed_at = datetime.fromisoformat(
            completed_at.replace("Z", "+00:00")
        )
    if error_message is not None:
        execution.error_message = error_message
    session.add(execution)
    return execution


def persist_workflow_agent_execution_structured_output(
    session: Session,
    execution: WorkflowAgentExecution,
    output_json: str | None,
) -> None:
    """Persist heavyweight structured rows derived from agent JSON (e.g. surveyor)."""
    if output_json and execution.agent_name == AgentNameDb.SURVEYOR:
        persist_surveyor_output(session, execution, output_json)


def update_workflow_agent_execution(
    session: Session,
    *,
    execution_id: str,
    status: str,
    output_json: str | None = None,
    started_at: str | None = None,
    completed_at: str | None = None,
    error_message: str | None = None,
) -> None:
    execution = apply_workflow_agent_execution_status(
        session,
        execution_id=execution_id,
        status=status,
        started_at=started_at,
        completed_at=completed_at,
        error_message=error_message,
    )
    if execution is None:
        return
    persist_workflow_agent_execution_structured_output(session, execution, output_json)


def apply_agent_execution_status(
    session: Session,
    *,
    execution_id: str,
    status: str,
    started_at: str | None = None,
    completed_at: str | None = None,
    error_message: str | None = None,
) -> AgentExecution | None:
    """Update per-ticker agent execution status and timestamps only (no output rows)."""
    execution = session.get(AgentExecution, execution_id)
    if execution is None:
        return None
    next_status = ExecutionStatusDb(status)
    current_status = execution.status.value
    if current_status == ExecutionStatusDb.CANCELLED.value and (
        next_status.value != ExecutionStatusDb.CANCELLED.value
    ):
        return None
    if (
        current_status in TERMINAL_EXECUTION_STATUSES
        and next_status.value in ACTIVE_EXECUTION_STATUSES
    ):
        return None
    execution.status = next_status
    if started_at is not None:
        execution.started_at = datetime.fromisoformat(started_at.replace("Z", "+00:00"))
    if completed_at is not None:
        execution.completed_at = datetime.fromisoformat(
            completed_at.replace("Z", "+00:00")
        )
    if error_message is not None:
        execution.error_message = error_message
    session.add(execution)
    return execution


def persist_agent_execution_structured_output(
    session: Session,
    execution: AgentExecution,
    output_json: str | None,
) -> None:
    """Persist heavyweight structured rows derived from agent JSON."""
    if not output_json:
        return
    match execution.agent_name:
        case AgentNameDb.PROFILER:
            persist_profiler_output(session, execution, output_json)
        case AgentNameDb.RESEARCHER:
            replace_research_report(session, execution, output_json)
        case AgentNameDb.STRATEGIST:
            replace_mispricing_thesis(session, execution, output_json)
        case AgentNameDb.SENTINEL:
            replace_evaluation_report(session, execution, output_json)
        case AgentNameDb.APPRAISER:
            replace_appraiser_report(session, execution, output_json)
        case _:
            pass


def update_agent_execution(
    session: Session,
    *,
    execution_id: str,
    status: str,
    output_json: str | None = None,
    started_at: str | None = None,
    completed_at: str | None = None,
    error_message: str | None = None,
) -> None:
    execution = apply_agent_execution_status(
        session,
        execution_id=execution_id,
        status=status,
        started_at=started_at,
        completed_at=completed_at,
        error_message=error_message,
    )
    if execution is None:
        return
    persist_agent_execution_structured_output(session, execution, output_json)


def apply_ticker_run_completion_fields(
    session: Session,
    *,
    run_id: str,
    status: str,
    final_rating: str | None,
    decision_type: str | None,
    recommended_action: str | None,
    error_message: str | None = None,
) -> Run | None:
    """Update ticker ``Run`` completion fields only (no ``RunFinalDecision`` rows)."""
    run = session.get(Run, run_id)
    if run is None:
        return None
    next_status = WorkflowRunStatusDb(status)
    current_status = run.status.value
    if current_status == WorkflowRunStatusDb.CANCELLED.value and (
        next_status.value != WorkflowRunStatusDb.CANCELLED.value
    ):
        return None
    if (
        current_status in _TERMINAL_RUN_STATUSES
        and next_status.value in _ACTIVE_RUN_STATUSES
    ):
        return None
    run.status = next_status
    run.completed_at = utc_now()
    run.final_rating = final_rating
    run.decision_type = DecisionTypeDb(decision_type) if decision_type else None
    run.recommended_action = recommended_action
    run.error_message = error_message
    session.add(run)
    return run


def persist_ticker_run_final_verdict(
    session: Session,
    *,
    run_id: str,
    final_verdict_json: str | None,
    decision_type: str | None,
) -> None:
    """Upsert structured final decision rows from the verdict JSON payload."""
    if not final_verdict_json or not decision_type:
        return
    verdict = Verdict.model_validate_json(final_verdict_json)
    if decision_type == DecisionTypeDb.ARBITER.value:
        source_execution_id = get_agent_execution_id_by_run_and_agent(
            session, run_id=run_id, agent_name=AgentNameDb.ARBITER.value
        )
        if source_execution_id is None:
            return
        decision = ArbiterDecision.model_validate(verdict.decision)
        upsert_run_final_decision(
            session,
            run_id=run_id,
            source_agent_execution_id=source_execution_id,
            decision_type=DecisionTypeDb.ARBITER,
            decision_date=date.fromisoformat(decision.decision_date),
            is_existing_position=decision.is_existing_position,
            rating=decision.rating.value,
            recommended_action=decision.recommended_action,
            conviction=decision.conviction,
            rejection_reason=None,
            current_price=decision.margin_of_safety.current_price,
            bear_intrinsic_value=decision.margin_of_safety.bear_intrinsic_value,
            base_intrinsic_value=decision.margin_of_safety.base_intrinsic_value,
            bull_intrinsic_value=decision.margin_of_safety.bull_intrinsic_value,
            margin_of_safety_base_pct=decision.margin_of_safety.margin_of_safety_base_pct,
            margin_of_safety_verdict=decision.margin_of_safety.margin_of_safety_verdict,
            primary_driver=decision.rationale.primary_driver,
            red_flag_disposition=decision.rationale.red_flag_disposition,
            data_gap_disposition=decision.rationale.data_gap_disposition,
            thesis_expiry_note=decision.thesis_expiry_note,
            supporting_factors=decision.rationale.supporting_factors,
            mitigating_factors=decision.rationale.mitigating_factors,
        )
    elif decision_type == DecisionTypeDb.SENTINEL_REJECTION.value:
        source_execution_id = get_agent_execution_id_by_run_and_agent(
            session, run_id=run_id, agent_name=AgentNameDb.SENTINEL.value
        )
        if source_execution_id is None:
            return
        decision = SentinelRejection.model_validate(verdict.decision)
        upsert_run_final_decision(
            session,
            run_id=run_id,
            source_agent_execution_id=source_execution_id,
            decision_type=DecisionTypeDb.SENTINEL_REJECTION,
            decision_date=date.fromisoformat(decision.decision_date),
            is_existing_position=decision.is_existing_position,
            rating=decision.rating.value,
            recommended_action=decision.recommended_action,
            conviction=None,
            rejection_reason=decision.rejection_reason,
            current_price=None,
            bear_intrinsic_value=None,
            base_intrinsic_value=None,
            bull_intrinsic_value=None,
            margin_of_safety_base_pct=None,
            margin_of_safety_verdict=None,
            primary_driver=None,
            red_flag_disposition=None,
            data_gap_disposition=None,
            thesis_expiry_note=None,
            supporting_factors=[],
            mitigating_factors=[],
        )


def update_ticker_run_completion(
    session: Session,
    *,
    run_id: str,
    status: str,
    final_rating: str | None,
    decision_type: str | None,
    recommended_action: str | None,
    final_verdict_json: str | None,
    error_message: str | None = None,
) -> None:
    run = apply_ticker_run_completion_fields(
        session,
        run_id=run_id,
        status=status,
        final_rating=final_rating,
        decision_type=decision_type,
        recommended_action=recommended_action,
        error_message=error_message,
    )
    if run is None:
        return
    persist_ticker_run_final_verdict(
        session,
        run_id=run_id,
        final_verdict_json=final_verdict_json,
        decision_type=decision_type,
    )


def update_ticker_run_company_name(
    session: Session, *, run_id: str, company_name: str
) -> None:
    run = session.get(Run, run_id)
    if run is None:
        return
    run.company_name = company_name
    session.add(run)
