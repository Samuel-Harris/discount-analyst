"""Run and AgentExecution persistence (ticker lanes, status updates, outputs).

Status fields and structured output persistence are split so callers can compose
them inside a single explicit transaction (for example ``DashboardPipelineRunner._db``,
which commits after each operation batch).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Any

from sqlalchemy import select
from sqlmodel import Session, col

from discount_analyst.application.workflows.agent_lane_order import LANE_AGENT_SLUGS
from discount_analyst.adapters.persistence.crud.agent_output_persistence import (
    appraiser_output_from_report,
    persist_profiler_output,
    persist_surveyor_output,
    replace_appraiser_output,
    replace_evaluation_report,
    replace_mispricing_thesis,
    replace_research_report,
    upsert_run_final_decision,
)
from discount_analyst.adapters.persistence.crud.candidate_snapshots import (
    snapshot_to_candidate,
)
from discount_analyst.adapters.persistence.crud.conversations import (
    assistant_response_for_run_agent,
    insert_conversation_for_agent_execution,
)
from discount_analyst.adapters.persistence.crud.db_utils import (
    ACTIVE_EXECUTION_STATUSES,
    TERMINAL_EXECUTION_STATUSES,
    new_id,
    utc_now,
)
from discount_analyst.adapters.persistence.models import (
    AgentExecution,
    AgentNameDb,
    CandidateSnapshot,
    DecisionTypeDb,
    EntryPathDb,
    ExecutionStatusDb,
    AppraiserReport,
    Run,
    WorkflowRun,
    WorkflowRunStatusDb,
)
from discount_analyst.agents.appraiser.schema import AppraiserOutput
from discount_analyst.domain.decisions.schema import (
    DataQualityRejection,
    RatingTableDecision,
    SentinelRejection,
    Verdict,
)
from discount_analyst.agents.surveyor.schema import SurveyorCandidate
from discount_analyst.domain.model_selection.model_name import ModelName

_ACTIVE_RUN_STATUSES = frozenset({WorkflowRunStatusDb.RUNNING.value})
_TERMINAL_RUN_STATUSES = frozenset(
    {
        WorkflowRunStatusDb.COMPLETED.value,
        WorkflowRunStatusDb.FAILED.value,
        WorkflowRunStatusDb.CANCELLED.value,
    }
)
_AGENT_LANE_ORDER = {
    AgentNameDb.PROFILER: 0,
    AgentNameDb.RESEARCHER: 1,
    AgentNameDb.STRATEGIST: 2,
    AgentNameDb.SENTINEL: 3,
    AgentNameDb.APPRAISER: 4,
}


@dataclass(frozen=True)
class RetryFailedAgentsPreparation:
    workflow_run_id: str
    surveyor_reset: bool
    lane_reset_count: int
    agent_execution_reset_count: int


class RetryFailedAgentsError(Exception):
    """Base class for retry preparation failures."""


class RetryWorkflowRunNotFoundError(RetryFailedAgentsError):
    """Raised when the workflow run does not exist."""


class RetryWorkflowRunNotTerminalError(RetryFailedAgentsError):
    """Raised when the workflow run is not in a terminal state."""


class NoFailedAgentsToRetryError(RetryFailedAgentsError):
    """Raised when no failed surveyor or lane execution exists."""


def _reset_agent_execution(execution: AgentExecution) -> None:
    execution.status = ExecutionStatusDb.PENDING
    execution.started_at = None
    execution.completed_at = None
    execution.error_message = None
    execution.model_name = None


def _clear_run_completion_fields(run: Run) -> None:
    run.status = WorkflowRunStatusDb.RUNNING
    run.completed_at = None
    run.error_message = None
    run.lane_aborted = False
    run.final_rating = None
    run.decision_type = None
    run.recommended_action = None


def _lane_executions(executions: list[AgentExecution]) -> list[AgentExecution]:
    return [
        execution
        for execution in executions
        if execution.agent_name.value in LANE_AGENT_SLUGS
    ]


def workflow_can_retry_failed_agents(
    *,
    workflow_status: WorkflowRunStatusDb,
    surveyor: AgentExecution | None,
    runs: list[Run],
    executions_by_run_id: dict[str, list[AgentExecution]],
) -> bool:
    """Return whether a terminal workflow has failed surveyor or lane work to retry."""
    if workflow_status.value not in _TERMINAL_RUN_STATUSES:
        return False
    if surveyor is not None and surveyor.status == ExecutionStatusDb.FAILED:
        return True
    return any(
        _first_retry_lane_order(run, executions_by_run_id.get(run.id, [])) is not None
        for run in runs
    )


def _first_retry_lane_order(run: Run, executions: list[AgentExecution]) -> int | None:
    """Return the first lane agent order to reset, or None when the run is not retriable."""
    lane_executions = _lane_executions(executions)
    failed_orders = [
        _AGENT_LANE_ORDER[execution.agent_name]
        for execution in lane_executions
        if execution.status == ExecutionStatusDb.FAILED
    ]
    if failed_orders:
        return min(failed_orders)

    if (
        run.lane_aborted
        and run.status == WorkflowRunStatusDb.FAILED
        and lane_executions
    ):
        return min(
            _AGENT_LANE_ORDER[execution.agent_name] for execution in lane_executions
        )

    return None


def prepare_retry_failed_agents(
    session: Session,
    workflow_run_id: str,
) -> RetryFailedAgentsPreparation:
    """Reset failed agents, and downstream lane agents, for an explicit retry."""
    workflow = session.get(WorkflowRun, workflow_run_id)
    if workflow is None:
        raise RetryWorkflowRunNotFoundError(workflow_run_id)
    if workflow.status.value not in _TERMINAL_RUN_STATUSES:
        raise RetryWorkflowRunNotTerminalError(workflow_run_id)

    surveyor_reset = False
    lane_reset_count = 0
    agent_execution_reset_count = 0

    surveyor = session.scalars(
        select(AgentExecution).where(
            col(AgentExecution.workflow_run_id) == workflow_run_id,
            col(AgentExecution.agent_name) == AgentNameDb.SURVEYOR,
        )
    ).first()
    if surveyor is not None and surveyor.status == ExecutionStatusDb.FAILED:
        _reset_agent_execution(surveyor)
        session.add(surveyor)
        surveyor_reset = True

    runs = list(
        session.scalars(select(Run).where(col(Run.workflow_run_id) == workflow_run_id))
    )
    for run in runs:
        executions = sorted(
            session.scalars(
                select(AgentExecution).where(col(AgentExecution.run_id) == run.id)
            ),
            key=lambda execution: _AGENT_LANE_ORDER.get(execution.agent_name, 99),
        )
        first_failed_order = _first_retry_lane_order(run, executions)
        if first_failed_order is None:
            continue
        for execution in executions:
            order = _AGENT_LANE_ORDER.get(execution.agent_name)
            if order is None or order < first_failed_order:
                continue
            _reset_agent_execution(execution)
            session.add(execution)
            agent_execution_reset_count += 1
        _clear_run_completion_fields(run)
        session.add(run)
        lane_reset_count += 1

    if surveyor_reset:
        for run in runs:
            if run.status != WorkflowRunStatusDb.CANCELLED:
                continue
            _clear_run_completion_fields(run)
            session.add(run)
            for execution in session.scalars(
                select(AgentExecution).where(col(AgentExecution.run_id) == run.id)
            ):
                if execution.status != ExecutionStatusDb.CANCELLED:
                    continue
                _reset_agent_execution(execution)
                session.add(execution)
                agent_execution_reset_count += 1

    if not surveyor_reset and lane_reset_count == 0:
        raise NoFailedAgentsToRetryError(workflow_run_id)

    workflow.status = WorkflowRunStatusDb.RUNNING
    workflow.completed_at = None
    workflow.error_message = None
    session.add(workflow)

    return RetryFailedAgentsPreparation(
        workflow_run_id=workflow_run_id,
        surveyor_reset=surveyor_reset,
        lane_reset_count=lane_reset_count,
        agent_execution_reset_count=agent_execution_reset_count,
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
                workflow_run_id=None,
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


def get_agent_execution_status_by_run_and_agent(
    session: Session,
    *,
    run_id: str,
    agent_name: str,
) -> str | None:
    row = session.scalars(
        select(AgentExecution).where(
            col(AgentExecution.run_id) == run_id,
            col(AgentExecution.agent_name) == AgentNameDb(agent_name),
        )
    ).first()
    return None if row is None else row.status.value


def get_workflow_surveyor_execution_id(
    session: Session, workflow_run_id: str
) -> str | None:
    row = session.scalars(
        select(col(AgentExecution.id)).where(
            col(AgentExecution.workflow_run_id) == workflow_run_id,
            col(AgentExecution.agent_name) == AgentNameDb.SURVEYOR,
        )
    ).first()
    return row


def get_workflow_surveyor_execution_status(
    session: Session, workflow_run_id: str
) -> str | None:
    row = session.scalars(
        select(AgentExecution).where(
            col(AgentExecution.workflow_run_id) == workflow_run_id,
            col(AgentExecution.agent_name) == AgentNameDb.SURVEYOR,
        )
    ).first()
    return None if row is None else row.status.value


def get_workflow_candidate_snapshot_id(
    session: Session, *, workflow_execution_id: str, ticker: str
) -> str | None:
    row = session.scalars(
        select(col(CandidateSnapshot.id)).where(
            col(CandidateSnapshot.agent_execution_id) == workflow_execution_id,
            col(CandidateSnapshot.ticker) == ticker,
        )
    ).first()
    return row


def get_candidate_for_run(session: Session, *, run_id: str) -> SurveyorCandidate | None:
    run = session.get(Run, run_id)
    if run is None or run.candidate_snapshot_id is None:
        return None
    snapshot = session.get(CandidateSnapshot, run.candidate_snapshot_id)
    if snapshot is None:
        return None
    return snapshot_to_candidate(snapshot)


def get_candidate_snapshot_id_for_run(session: Session, *, run_id: str) -> str | None:
    run = session.get(Run, run_id)
    if run is None:
        return None
    return run.candidate_snapshot_id


def get_completed_agent_output_json(
    session: Session,
    *,
    run_id: str,
    agent_name: str,
) -> str | None:
    execution = session.scalars(
        select(AgentExecution).where(
            col(AgentExecution.run_id) == run_id,
            col(AgentExecution.agent_name) == AgentNameDb(agent_name),
        )
    ).first()
    if execution is None or execution.status != ExecutionStatusDb.COMPLETED:
        return None
    output_json = assistant_response_for_run_agent(session, execution)
    if output_json == "{}":
        return None
    return output_json


def get_appraiser_report_for_run(
    session: Session,
    *,
    run_id: str,
) -> AppraiserReport | None:
    return session.scalars(
        select(AppraiserReport)
        .join(
            AgentExecution,
            col(AppraiserReport.agent_execution_id) == col(AgentExecution.id),
        )
        .where(
            col(AgentExecution.run_id) == run_id,
            col(AgentExecution.agent_name) == AgentNameDb.APPRAISER,
        )
    ).first()


def get_appraiser_output_for_run(
    session: Session,
    *,
    run_id: str,
) -> AppraiserOutput | None:
    row = get_appraiser_report_for_run(session, run_id=run_id)
    if row is None:
        return None
    return appraiser_output_from_report(row)


def apply_agent_execution_status(
    session: Session,
    *,
    execution_id: str,
    status: str,
    started_at: str | None = None,
    completed_at: str | None = None,
    error_message: str | None = None,
    model_name: ModelName | None = None,
) -> AgentExecution | None:
    """Update agent execution status and timestamps only (no output rows)."""
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
    if model_name is not None:
        execution.model_name = model_name
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
        case AgentNameDb.SURVEYOR:
            persist_surveyor_output(session, execution, output_json)
        case AgentNameDb.PROFILER:
            persist_profiler_output(session, execution, output_json)
        case AgentNameDb.RESEARCHER:
            replace_research_report(session, execution, output_json)
        case AgentNameDb.STRATEGIST:
            replace_mispricing_thesis(session, execution, output_json)
        case AgentNameDb.SENTINEL:
            replace_evaluation_report(session, execution, output_json)
        case AgentNameDb.APPRAISER:
            replace_appraiser_output(session, execution, output_json)
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
    model_name: ModelName | None = None,
) -> None:
    execution = apply_agent_execution_status(
        session,
        execution_id=execution_id,
        status=status,
        started_at=started_at,
        completed_at=completed_at,
        error_message=error_message,
        model_name=model_name,
    )
    if execution is None:
        return
    persist_agent_execution_structured_output(session, execution, output_json)


def complete_agent_execution_with_conversation(
    session: Session,
    *,
    execution_id: str,
    conversation_id: str,
    system_prompt: str,
    output_json: str | None,
    completed_at: str,
    messages: list[Any] | None = None,
    messages_json: str | None = None,
) -> None:
    insert_conversation_for_agent_execution(
        session,
        conversation_id=conversation_id,
        agent_execution_id=execution_id,
        system_prompt=system_prompt,
        messages=messages,
        messages_json=messages_json,
    )
    update_agent_execution(
        session,
        execution_id=execution_id,
        status=ExecutionStatusDb.COMPLETED.value,
        output_json=output_json,
        completed_at=completed_at,
    )


def mark_lane_abort(
    session: Session,
    *,
    run_id: str,
    error_message: str,
) -> None:
    """Fail the active stage, skip unreached stages, and mark the run as lane-aborted."""
    run = session.get(Run, run_id)
    if run is not None:
        run.lane_aborted = True
        session.add(run)

    executions = sorted(
        session.scalars(
            select(AgentExecution).where(col(AgentExecution.run_id) == run_id)
        ),
        key=lambda execution: _AGENT_LANE_ORDER.get(execution.agent_name, 99),
    )
    completed_at = utc_now()
    failed_execution: AgentExecution | None = None
    for execution in executions:
        if execution.status == ExecutionStatusDb.RUNNING:
            failed_execution = execution
            break
    if failed_execution is None:
        completed = [
            execution
            for execution in executions
            if execution.status == ExecutionStatusDb.COMPLETED
        ]
        if completed:
            failed_execution = completed[-1]

    if failed_execution is not None:
        failed_execution.status = ExecutionStatusDb.FAILED
        failed_execution.completed_at = completed_at
        failed_execution.error_message = error_message
        session.add(failed_execution)

    for execution in executions:
        if execution.status != ExecutionStatusDb.PENDING:
            continue
        execution.status = ExecutionStatusDb.SKIPPED
        execution.completed_at = completed_at
        execution.error_message = error_message
        session.add(execution)


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
    if decision_type == DecisionTypeDb.RATING_TABLE.value:
        source_execution_id = get_agent_execution_id_by_run_and_agent(
            session, run_id=run_id, agent_name=AgentNameDb.APPRAISER.value
        )
        if source_execution_id is None:
            return
        decision = RatingTableDecision.model_validate(verdict.decision)
        upsert_run_final_decision(
            session,
            run_id=run_id,
            source_agent_execution_id=source_execution_id,
            decision_type=DecisionTypeDb.RATING_TABLE,
            decision_date=date.fromisoformat(decision.decision_date),
            is_existing_position=decision.is_existing_position,
            rating=decision.rating.value,
            recommended_action=decision.recommended_action,
            conviction=decision.conviction,
            rejection_reason=None,
            current_price=decision.margin_of_safety.current_price,
            bear_intrinsic_value=decision.margin_of_safety.intrinsic_value_bear,
            base_intrinsic_value=decision.margin_of_safety.expected_intrinsic_value,
            bull_intrinsic_value=decision.margin_of_safety.intrinsic_value_bull,
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
    elif decision_type == DecisionTypeDb.DATA_QUALITY_REJECTION.value:
        source_execution_id = get_agent_execution_id_by_run_and_agent(
            session, run_id=run_id, agent_name=AgentNameDb.RESEARCHER.value
        )
        if source_execution_id is None:
            return
        decision = DataQualityRejection.model_validate(verdict.decision)
        upsert_run_final_decision(
            session,
            run_id=run_id,
            source_agent_execution_id=source_execution_id,
            decision_type=DecisionTypeDb.DATA_QUALITY_REJECTION,
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


def update_ticker_run_ticker(session: Session, *, run_id: str, ticker: str) -> None:
    run = session.get(Run, run_id)
    if run is None:
        return
    run.ticker = ticker
    session.add(run)
