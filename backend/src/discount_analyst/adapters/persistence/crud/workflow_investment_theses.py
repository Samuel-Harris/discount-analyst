"""Persist and load workflow-scoped investment thesis snapshots."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, cast

from sqlalchemy import func
from sqlmodel import Session, col, delete, select

from discount_analyst.adapters.persistence.crud.db_utils import new_id
from discount_analyst.adapters.persistence.models import (
    AgentExecution,
    AgentNameDb,
    ExecutionStatusDb,
    MispricingThesis,
    MispricingThesisEvaluationQuestion,
    MispricingThesisFalsificationCondition,
    MispricingThesisPermanentLossScenario,
    MispricingThesisRisk,
    PortfolioAllocation,
    PortfolioAllocationPosition,
    Run,
    WorkflowInvestmentThesis,
    WorkflowInvestmentThesisEvaluationQuestion,
    WorkflowInvestmentThesisFalsificationCondition,
    WorkflowInvestmentThesisOriginDb,
    WorkflowInvestmentThesisPermanentLossScenario,
    WorkflowInvestmentThesisRisk,
    WorkflowRun,
    WorkflowRunStatusDb,
)
from discount_analyst.agents.strategist.schema import (
    MispricingThesis as MispricingThesisSchema,
)
from discount_analyst.domain.allocations.allocation import (
    PortfolioAllocation as DomainPortfolioAllocation,
)

ConvictionLevel = Literal["Low", "Medium", "High"]


@dataclass(frozen=True, slots=True)
class WorkflowThesisSnapshot:
    ticker: str
    company_name: str
    thesis: MispricingThesisSchema
    origin: WorkflowInvestmentThesisOriginDb


def persist_workflow_investment_theses(
    session: Session,
    *,
    workflow_run_id: str,
    snapshots: tuple[WorkflowThesisSnapshot, ...],
) -> None:
    """Replace this workflow's thesis snapshots with ``snapshots``."""
    _delete_snapshots_for_workflow(session, workflow_run_id)
    for snapshot in snapshots:
        _insert_snapshot(session, workflow_run_id=workflow_run_id, snapshot=snapshot)


def persist_chosen_position_theses(
    session: Session,
    *,
    workflow_run_id: str,
    allocation: DomainPortfolioAllocation,
) -> None:
    """Snapshot this-run Strategist theses for positions with target > 0.

    ``origin`` is copied from the execution-scoped Strategist row written when
    the keep/replace discriminator was still in hand. Chosen positions with no
    this-run thesis fail; a prior snapshot is not a substitute.
    """
    snapshots: list[WorkflowThesisSnapshot] = []
    for position in allocation.positions:
        if position.target_weight_pct <= 0:
            continue
        live_and_origin = _this_run_thesis_and_origin(session, position.source_run_id)
        if live_and_origin is None:
            msg = f"Chosen position {position.ticker!r} has no live thesis to snapshot."
            raise ValueError(msg)
        live, origin = live_and_origin
        snapshots.append(
            WorkflowThesisSnapshot(
                ticker=position.ticker,
                company_name=position.company_name,
                thesis=live,
                origin=origin,
            )
        )
    persist_workflow_investment_theses(
        session, workflow_run_id=workflow_run_id, snapshots=tuple(snapshots)
    )


def get_latest_investment_thesis_for_ticker(
    session: Session, ticker: str
) -> MispricingThesisSchema | None:
    """Load the durable latest thesis for ``ticker`` (casefold).

    Newest completed workflow with a snapshot row wins. Otherwise the newest
    completed workflow whose Curator allocation chose the ticker
    (``target_weight_pct > 0``), then that lane's Strategist thesis.
    """
    folded = ticker.casefold()
    snapshotted = _latest_snapshot_for_ticker(session, folded)
    if snapshotted is not None:
        return snapshotted
    return _latest_chosen_strategist_thesis(session, folded)


def _latest_snapshot_for_ticker(
    session: Session, folded_ticker: str
) -> MispricingThesisSchema | None:
    rows = list(
        session.exec(
            select(WorkflowInvestmentThesis, WorkflowRun)
            .join(
                WorkflowRun,
                col(WorkflowInvestmentThesis.workflow_run_id) == col(WorkflowRun.id),
            )
            .where(
                col(WorkflowRun.status) == WorkflowRunStatusDb.COMPLETED,
                func.lower(col(WorkflowInvestmentThesis.ticker)) == folded_ticker,
            )
            .order_by(col(WorkflowRun.completed_at).desc())
        ).all()
    )
    if not rows:
        return None
    thesis_row, _workflow = rows[0]
    return _workflow_row_to_schema(session, thesis_row)


def _latest_chosen_strategist_thesis(
    session: Session, folded_ticker: str
) -> MispricingThesisSchema | None:
    rows = list(
        session.exec(
            select(PortfolioAllocationPosition, WorkflowRun)
            .join(
                PortfolioAllocation,
                col(PortfolioAllocationPosition.allocation_id)
                == col(PortfolioAllocation.id),
            )
            .join(
                AgentExecution,
                col(PortfolioAllocation.agent_execution_id) == col(AgentExecution.id),
            )
            .join(
                WorkflowRun,
                col(AgentExecution.workflow_run_id) == col(WorkflowRun.id),
            )
            .where(
                col(WorkflowRun.status) == WorkflowRunStatusDb.COMPLETED,
                col(AgentExecution.agent_name) == AgentNameDb.CURATOR,
                col(AgentExecution.status) == ExecutionStatusDb.COMPLETED,
                func.lower(col(PortfolioAllocationPosition.ticker)) == folded_ticker,
                col(PortfolioAllocationPosition.target_weight_pct) > 0,
            )
            .order_by(col(WorkflowRun.completed_at).desc())
        ).all()
    )
    if not rows:
        return None
    position_row, _workflow = rows[0]
    return _thesis_for_run(session, position_row.source_run_id)


def _this_run_thesis_and_origin(
    session: Session, run_id: str
) -> tuple[MispricingThesisSchema, WorkflowInvestmentThesisOriginDb] | None:
    execution = session.scalars(
        select(AgentExecution).where(
            col(AgentExecution.run_id) == run_id,
            col(AgentExecution.agent_name) == AgentNameDb.STRATEGIST,
        )
    ).first()
    if execution is None or execution.status != ExecutionStatusDb.COMPLETED:
        return None
    row = session.scalars(
        select(MispricingThesis).where(
            col(MispricingThesis.agent_execution_id) == execution.id
        )
    ).first()
    run = session.get(Run, run_id)
    if row is None or run is None:
        return None
    return _execution_row_to_schema(session, row, run), row.origin


def _thesis_for_run(session: Session, run_id: str) -> MispricingThesisSchema | None:
    loaded = _this_run_thesis_and_origin(session, run_id)
    if loaded is None:
        return None
    return loaded[0]


def _insert_snapshot(
    session: Session, *, workflow_run_id: str, snapshot: WorkflowThesisSnapshot
) -> None:
    thesis = snapshot.thesis
    row = WorkflowInvestmentThesis(
        id=new_id(),
        workflow_run_id=workflow_run_id,
        ticker=snapshot.ticker,
        company_name=snapshot.company_name,
        mispricing_type=thesis.mispricing_type,
        market_belief=thesis.market_belief,
        mispricing_argument=thesis.mispricing_argument,
        resolution_mechanism=thesis.resolution_mechanism,
        conviction_level=thesis.conviction_level,
        origin=snapshot.origin,
    )
    session.add(row)
    for idx, value in enumerate(thesis.falsification_conditions):
        session.add(
            WorkflowInvestmentThesisFalsificationCondition(
                id=new_id(),
                workflow_investment_thesis_id=row.id,
                sort_order=idx,
                condition_text=value,
            )
        )
    for idx, value in enumerate(thesis.thesis_risks):
        session.add(
            WorkflowInvestmentThesisRisk(
                id=new_id(),
                workflow_investment_thesis_id=row.id,
                sort_order=idx,
                risk_text=value,
            )
        )
    for idx, value in enumerate(thesis.evaluation_questions):
        session.add(
            WorkflowInvestmentThesisEvaluationQuestion(
                id=new_id(),
                workflow_investment_thesis_id=row.id,
                sort_order=idx,
                question_text=value,
            )
        )
    for idx, value in enumerate(thesis.permanent_loss_scenarios):
        session.add(
            WorkflowInvestmentThesisPermanentLossScenario(
                id=new_id(),
                workflow_investment_thesis_id=row.id,
                sort_order=idx,
                scenario_text=value,
            )
        )


def _delete_snapshots_for_workflow(session: Session, workflow_run_id: str) -> None:
    parent_ids = list(
        session.scalars(
            select(col(WorkflowInvestmentThesis.id)).where(
                col(WorkflowInvestmentThesis.workflow_run_id) == workflow_run_id
            )
        )
    )
    if not parent_ids:
        return
    session.exec(
        delete(WorkflowInvestmentThesisFalsificationCondition).where(
            col(
                WorkflowInvestmentThesisFalsificationCondition.workflow_investment_thesis_id
            ).in_(parent_ids)
        )
    )
    session.exec(
        delete(WorkflowInvestmentThesisRisk).where(
            col(WorkflowInvestmentThesisRisk.workflow_investment_thesis_id).in_(
                parent_ids
            )
        )
    )
    session.exec(
        delete(WorkflowInvestmentThesisEvaluationQuestion).where(
            col(
                WorkflowInvestmentThesisEvaluationQuestion.workflow_investment_thesis_id
            ).in_(parent_ids)
        )
    )
    session.exec(
        delete(WorkflowInvestmentThesisPermanentLossScenario).where(
            col(
                WorkflowInvestmentThesisPermanentLossScenario.workflow_investment_thesis_id
            ).in_(parent_ids)
        )
    )
    session.exec(
        delete(WorkflowInvestmentThesis).where(
            col(WorkflowInvestmentThesis.workflow_run_id) == workflow_run_id
        )
    )


def _workflow_row_to_schema(
    session: Session, row: WorkflowInvestmentThesis
) -> MispricingThesisSchema:
    return MispricingThesisSchema(
        ticker=row.ticker,
        company_name=row.company_name,
        mispricing_type=row.mispricing_type,
        market_belief=row.market_belief,
        mispricing_argument=row.mispricing_argument,
        resolution_mechanism=row.resolution_mechanism,
        falsification_conditions=_ordered_texts(
            session,
            WorkflowInvestmentThesisFalsificationCondition,
            WorkflowInvestmentThesisFalsificationCondition.workflow_investment_thesis_id,
            row.id,
            "condition_text",
        ),
        thesis_risks=_ordered_texts(
            session,
            WorkflowInvestmentThesisRisk,
            WorkflowInvestmentThesisRisk.workflow_investment_thesis_id,
            row.id,
            "risk_text",
        ),
        evaluation_questions=_ordered_texts(
            session,
            WorkflowInvestmentThesisEvaluationQuestion,
            WorkflowInvestmentThesisEvaluationQuestion.workflow_investment_thesis_id,
            row.id,
            "question_text",
        ),
        permanent_loss_scenarios=_ordered_texts(
            session,
            WorkflowInvestmentThesisPermanentLossScenario,
            WorkflowInvestmentThesisPermanentLossScenario.workflow_investment_thesis_id,
            row.id,
            "scenario_text",
        ),
        conviction_level=_conviction(row.conviction_level),
    )


def _execution_row_to_schema(
    session: Session, row: MispricingThesis, run: Run
) -> MispricingThesisSchema:
    return MispricingThesisSchema(
        ticker=run.ticker,
        company_name=run.company_name,
        mispricing_type=row.mispricing_type,
        market_belief=row.market_belief,
        mispricing_argument=row.mispricing_argument,
        resolution_mechanism=row.resolution_mechanism,
        falsification_conditions=_ordered_texts(
            session,
            MispricingThesisFalsificationCondition,
            MispricingThesisFalsificationCondition.mispricing_thesis_id,
            row.id,
            "condition_text",
        ),
        thesis_risks=_ordered_texts(
            session,
            MispricingThesisRisk,
            MispricingThesisRisk.mispricing_thesis_id,
            row.id,
            "risk_text",
        ),
        evaluation_questions=_ordered_texts(
            session,
            MispricingThesisEvaluationQuestion,
            MispricingThesisEvaluationQuestion.mispricing_thesis_id,
            row.id,
            "question_text",
        ),
        permanent_loss_scenarios=_ordered_texts(
            session,
            MispricingThesisPermanentLossScenario,
            MispricingThesisPermanentLossScenario.mispricing_thesis_id,
            row.id,
            "scenario_text",
        ),
        conviction_level=_conviction(row.conviction_level),
    )


def _ordered_texts(
    session: Session,
    model: type[object],
    fk_column: object,
    parent_id: str,
    text_attr: str,
) -> list[str]:
    rows = list(
        session.scalars(
            select(model).where(fk_column == parent_id).order_by(col(model.sort_order))  # type: ignore[attr-defined]
        )
    )
    return [getattr(child, text_attr) for child in rows]


def _conviction(value: str) -> ConvictionLevel:
    return cast(ConvictionLevel, value)
