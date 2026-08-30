"""Load completed ticker lanes as Allocator ``CompletedLaneBundle`` values."""

from __future__ import annotations

from sqlmodel import Session, col, select

from discount_analyst.adapters.persistence.crud.run_executions import (
    get_appraiser_output_for_run,
    get_completed_agent_output_json,
)
from discount_analyst.adapters.persistence.models import (
    AgentNameDb,
    CandidateSnapshot,
    DecisionTypeDb,
    Run,
    RunFinalDecision,
    WorkflowRunStatusDb,
)
from discount_analyst.agents.appraiser.schema import AppraiserOutput
from discount_analyst.agents.researcher.schema import DeepResearchReport
from discount_analyst.agents.sentinel.schema import EvaluationReport
from discount_analyst.agents.strategist.schema import MispricingThesis
from discount_analyst.application.allocations.assemble import (
    CompletedLaneBundle,
    LaneDecisionKind,
)
from discount_analyst.application.allocations.errors import AllocationAssemblyError
from discount_analyst.domain.decisions.investment_rating import InvestmentRating


def load_completed_lane_bundles(
    session: Session, workflow_run_id: str
) -> tuple[CompletedLaneBundle, ...]:
    """Reconstruct compact Allocator evidence from completed ticker runs."""
    runs = list(
        session.scalars(
            select(Run)
            .where(col(Run.workflow_run_id) == workflow_run_id)
            .order_by(col(Run.started_at))
        )
    )
    bundles: list[CompletedLaneBundle] = []
    for run in runs:
        if run.status != WorkflowRunStatusDb.COMPLETED:
            msg = (
                f"Run {run.id} for {run.ticker!r} is {run.status.value}, not completed."
            )
            raise AllocationAssemblyError(msg)
        decision_row = session.scalars(
            select(RunFinalDecision).where(col(RunFinalDecision.run_id) == run.id)
        ).first()
        if decision_row is None:
            msg = f"Completed run {run.id} for {run.ticker!r} has no final decision."
            raise AllocationAssemblyError(msg)
        snapshot = (
            session.get(CandidateSnapshot, run.candidate_snapshot_id)
            if run.candidate_snapshot_id is not None
            else None
        )
        sector = snapshot.sector if snapshot is not None else "Unknown"
        industry = snapshot.industry if snapshot is not None else "Unknown"
        decision_kind = _lane_decision_kind(run, decision_row)
        rejection_reason = _rejection_reason(run, decision_row, decision_kind)
        if decision_kind == "data_quality_rejection":
            bundles.append(
                CompletedLaneBundle(
                    source_run_id=run.id,
                    ticker=run.ticker,
                    company_name=run.company_name,
                    is_existing_position=decision_row.is_existing_position,
                    rating=InvestmentRating(decision_row.rating),
                    decision_kind=decision_kind,
                    rejection_reason=rejection_reason,
                    sector=sector,
                    industry=industry,
                )
            )
            continue
        research = _load_model(
            session,
            run_id=run.id,
            agent_name=AgentNameDb.RESEARCHER.value,
            model_type=DeepResearchReport,
        )
        thesis = _load_model(
            session,
            run_id=run.id,
            agent_name=AgentNameDb.STRATEGIST.value,
            model_type=MispricingThesis,
        )
        evaluation = _load_model(
            session,
            run_id=run.id,
            agent_name=AgentNameDb.SENTINEL.value,
            model_type=EvaluationReport,
        )
        appraiser: AppraiserOutput | None = None
        if decision_kind == "rating_table":
            appraiser = get_appraiser_output_for_run(session, run_id=run.id)
        bundles.append(
            CompletedLaneBundle(
                source_run_id=run.id,
                ticker=run.ticker,
                company_name=run.company_name,
                is_existing_position=decision_row.is_existing_position,
                rating=InvestmentRating(decision_row.rating),
                decision_kind=decision_kind,
                rejection_reason=rejection_reason,
                sector=sector,
                industry=industry,
                deep_research=research,
                thesis=thesis,
                evaluation=evaluation,
                appraiser_output=appraiser,
            )
        )
    return tuple(bundles)


def _lane_decision_kind(run: Run, row: RunFinalDecision) -> LaneDecisionKind:
    if row.decision_type == DecisionTypeDb.DATA_QUALITY_REJECTION:
        return "data_quality_rejection"
    if row.decision_type == DecisionTypeDb.SENTINEL_REJECTION:
        return "sentinel_rejection"
    if row.decision_type == DecisionTypeDb.RATING_TABLE:
        return "rating_table"
    msg = f"Unsupported decision type {row.decision_type!r} for {run.ticker!r}."
    raise AllocationAssemblyError(msg)


def _rejection_reason(
    run: Run, row: RunFinalDecision, decision_kind: LaneDecisionKind
) -> str | None:
    if decision_kind == "rating_table":
        return None
    if row.rejection_reason is None:
        msg = f"{decision_kind} for {run.ticker!r} is missing a reason."
        raise AllocationAssemblyError(msg)
    return row.rejection_reason


def _load_model[T](
    session: Session,
    *,
    run_id: str,
    agent_name: str,
    model_type: type[T],
) -> T | None:
    payload = get_completed_agent_output_json(
        session, run_id=run_id, agent_name=agent_name
    )
    if payload is None:
        return None
    return model_type.model_validate_json(payload)
