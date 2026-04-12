"""Run and AgentExecution persistence (ticker lanes, status updates, outputs)."""

from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import select
from sqlmodel import Session

from backend.crud.agent_output_persistence import (
    persist_profiler_output,
    persist_surveyor_output,
    replace_appraiser_report,
    replace_evaluation_report,
    replace_mispricing_thesis,
    replace_research_report,
    upsert_run_final_decision,
)
from backend.crud.db_utils import new_id, utc_now
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


PROFILER_ENTRY_AGENT_NAMES = (
    "profiler",
    "researcher",
    "strategist",
    "sentinel",
    "appraiser",
    "arbiter",
)
SURVEYOR_ENTRY_AGENT_NAMES = (
    "researcher",
    "strategist",
    "sentinel",
    "appraiser",
    "arbiter",
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
    session.commit()


def get_agent_execution_id_by_run_and_agent(
    session: Session,
    *,
    run_id: str,
    agent_name: str,
) -> str | None:
    row = session.exec(
        select(AgentExecution.id).where(
            AgentExecution.run_id == run_id,
            AgentExecution.agent_name == AgentNameDb(agent_name),
        )
    ).first()
    return row[0] if row is not None else None


def get_workflow_surveyor_execution_id(
    session: Session, workflow_run_id: str
) -> str | None:
    row = session.exec(
        select(WorkflowAgentExecution.id).where(
            WorkflowAgentExecution.workflow_run_id == workflow_run_id,
            WorkflowAgentExecution.agent_name == AgentNameDb.SURVEYOR,
        )
    ).first()
    return row[0] if row is not None else None


def get_workflow_candidate_snapshot_id(
    session: Session, *, workflow_execution_id: str, ticker: str
) -> str | None:
    row = session.exec(
        select(CandidateSnapshot.id).where(
            CandidateSnapshot.workflow_agent_execution_id == workflow_execution_id,
            CandidateSnapshot.ticker == ticker,
        )
    ).first()
    return row[0] if row is not None else None


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
    execution = session.get(WorkflowAgentExecution, execution_id)
    if execution is None:
        return
    execution.status = ExecutionStatusDb(status)
    if started_at is not None:
        execution.started_at = datetime.fromisoformat(started_at.replace("Z", "+00:00"))
    if completed_at is not None:
        execution.completed_at = datetime.fromisoformat(
            completed_at.replace("Z", "+00:00")
        )
    if error_message is not None:
        execution.error_message = error_message

    if output_json and execution.agent_name == AgentNameDb.SURVEYOR:
        persist_surveyor_output(session, execution, output_json)
    session.add(execution)
    session.commit()


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
    execution = session.get(AgentExecution, execution_id)
    if execution is None:
        return
    execution.status = ExecutionStatusDb(status)
    if started_at is not None:
        execution.started_at = datetime.fromisoformat(started_at.replace("Z", "+00:00"))
    if completed_at is not None:
        execution.completed_at = datetime.fromisoformat(
            completed_at.replace("Z", "+00:00")
        )
    if error_message is not None:
        execution.error_message = error_message

    if output_json:
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
    session.add(execution)
    session.commit()


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
    run = session.get(Run, run_id)
    if run is None:
        return
    run.status = WorkflowRunStatusDb(status)
    run.completed_at = utc_now()
    run.final_rating = final_rating
    run.decision_type = DecisionTypeDb(decision_type) if decision_type else None
    run.recommended_action = recommended_action
    run.error_message = error_message
    session.add(run)

    if final_verdict_json and decision_type:
        verdict = Verdict.model_validate_json(final_verdict_json)
        if decision_type == DecisionTypeDb.ARBITER.value:
            source_execution_id = get_agent_execution_id_by_run_and_agent(
                session, run_id=run_id, agent_name=AgentNameDb.ARBITER.value
            )
            if source_execution_id is None:
                session.commit()
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
                session.commit()
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

    session.commit()


def update_ticker_run_company_name(
    session: Session, *, run_id: str, company_name: str
) -> None:
    run = session.get(Run, run_id)
    if run is None:
        return
    run.company_name = company_name
    session.add(run)
    session.commit()
