"""Load completed ticker lanes as Curator valued and DQR bundles."""

from __future__ import annotations

from pydantic import BaseModel
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
from discount_analyst.agents.researcher.schema import DeepResearchReport
from discount_analyst.agents.sentinel.schema import EvaluationReport
from discount_analyst.agents.strategist.schema import MispricingThesis
from discount_analyst.application.allocations.assemble import (
    DqrLaneBundle,
    ValuedLaneBundle,
)
from discount_analyst.application.allocations.errors import AllocationAssemblyError


def load_completed_lane_bundles(
    session: Session, workflow_run_id: str
) -> tuple[tuple[ValuedLaneBundle, ...], tuple[DqrLaneBundle, ...]]:
    """Reconstruct Curator evidence from completed ticker runs."""
    runs = list(
        session.scalars(
            select(Run)
            .where(col(Run.workflow_run_id) == workflow_run_id)
            .order_by(col(Run.started_at))
        )
    )
    valued: list[ValuedLaneBundle] = []
    dqr: list[DqrLaneBundle] = []
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
        if decision_row.decision_type in {
            DecisionTypeDb.DATA_QUALITY_REJECTION,
            DecisionTypeDb.SENTINEL_REJECTION,
        }:
            if decision_row.rejection_reason is None:
                msg = (
                    f"{decision_row.decision_type.value} for {run.ticker!r} "
                    "is missing a reason."
                )
                raise AllocationAssemblyError(msg)
            if decision_row.decision_type == DecisionTypeDb.DATA_QUALITY_REJECTION:
                rationale = f"Data-quality gate failed: {decision_row.rejection_reason}"
            else:
                rationale = (
                    f"Sentinel rejected the thesis: {decision_row.rejection_reason}"
                )
            dqr.append(
                DqrLaneBundle(
                    source_run_id=run.id,
                    ticker=run.ticker,
                    company_name=run.company_name,
                    is_existing_position=decision_row.is_existing_position,
                    sector=sector,
                    industry=industry,
                    rationale=rationale,
                )
            )
            continue
        if decision_row.decision_type not in {
            DecisionTypeDb.APPRAISED,
            DecisionTypeDb.RATING_TABLE,
        }:
            msg = (
                f"Unsupported decision type {decision_row.decision_type!r} "
                f"for {run.ticker!r}."
            )
            raise AllocationAssemblyError(msg)
        research = _require_model(
            session,
            run_id=run.id,
            ticker=run.ticker,
            agent_name=AgentNameDb.RESEARCHER.value,
            model_type=DeepResearchReport,
        )
        thesis = _require_model(
            session,
            run_id=run.id,
            ticker=run.ticker,
            agent_name=AgentNameDb.STRATEGIST.value,
            model_type=MispricingThesis,
        )
        evaluation = _require_model(
            session,
            run_id=run.id,
            ticker=run.ticker,
            agent_name=AgentNameDb.SENTINEL.value,
            model_type=EvaluationReport,
        )
        appraiser = get_appraiser_output_for_run(session, run_id=run.id)
        if appraiser is None:
            msg = f"Lane {run.ticker!r} is missing Appraiser evidence."
            raise AllocationAssemblyError(msg)
        valued.append(
            ValuedLaneBundle(
                source_run_id=run.id,
                ticker=run.ticker,
                company_name=run.company_name,
                is_existing_position=decision_row.is_existing_position,
                sector=sector,
                industry=industry,
                deep_research=research,
                thesis=thesis,
                evaluation=evaluation,
                appraiser_output=appraiser,
            )
        )
    return tuple(valued), tuple(dqr)


def _require_model[T: BaseModel](
    session: Session,
    *,
    run_id: str,
    ticker: str,
    agent_name: str,
    model_type: type[T],
) -> T:
    payload = get_completed_agent_output_json(
        session, run_id=run_id, agent_name=agent_name
    )
    if payload is None:
        msg = f"Lane {ticker!r} is missing {agent_name} evidence."
        raise AllocationAssemblyError(msg)
    return model_type.model_validate_json(payload)
