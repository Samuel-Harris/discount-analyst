"""Workflow-scoped investment thesis snapshots and latest-ticker lookup."""

from decimal import Decimal

from datetime import UTC, datetime

import pytest
from sqlmodel import Session, col, select

from backend.tests.factories.sterling import sterling_holdings
from discount_analyst.adapters.persistence.crud.agent_output_persistence import (
    persist_mispricing_thesis,
    persist_strategist_decision,
)
from discount_analyst.adapters.persistence.crud.conversations import (
    assistant_response_for_run_agent,
)
from discount_analyst.adapters.persistence.crud.db_utils import new_id, utc_now
from discount_analyst.adapters.persistence.crud.portfolio_allocations import (
    persist_portfolio_allocation,
)
from discount_analyst.adapters.persistence.crud.run_executions import (
    insert_ticker_run_with_agents,
)
from discount_analyst.adapters.persistence.crud.workflow_investment_theses import (
    WorkflowThesisSnapshot,
    get_latest_investment_thesis_for_ticker,
    persist_chosen_position_theses,
    persist_workflow_investment_theses,
)
from discount_analyst.adapters.persistence.crud.workflow_runs import insert_workflow_run
from discount_analyst.adapters.persistence.models import (
    AgentExecution,
    AgentNameDb,
    ExecutionStatusDb,
    MispricingThesis as MispricingThesisRow,
    WorkflowInvestmentThesis,
    WorkflowInvestmentThesisOriginDb,
    WorkflowRun,
    WorkflowRunStatusDb,
)
from discount_analyst.adapters.simulation.mock_outputs import (
    mock_surveyor_candidate,
    mock_thesis,
)
from discount_analyst.agents.strategist.schema import (
    MispricingThesis,
    StrategistDecision,
)
from discount_analyst.application.theses import KeepPriorWithoutThesisError
from discount_analyst.domain.allocations.actions import RebalanceAction
from discount_analyst.domain.allocations.allocation import (
    AllocationPosition,
    CashAllocation,
    PortfolioAllocation,
)
from discount_analyst.domain.allocations.policy import (
    ForcedZeroPolicy,
    ForcedZeroReason,
    InvestablePolicy,
)


def _complete_workflow(session: Session, workflow_run_id: str) -> None:
    workflow = session.get(WorkflowRun, workflow_run_id)
    assert workflow is not None
    workflow.status = WorkflowRunStatusDb.COMPLETED
    workflow.completed_at = datetime(2026, 8, 30, tzinfo=UTC)
    session.add(workflow)


def _strategist_execution(session: Session, run_id: str) -> AgentExecution:
    execution = session.scalars(
        select(AgentExecution).where(
            col(AgentExecution.run_id) == run_id,
            col(AgentExecution.agent_name) == AgentNameDb.STRATEGIST,
        )
    ).one()
    execution.status = ExecutionStatusDb.COMPLETED
    execution.completed_at = utc_now()
    session.add(execution)
    return execution


def test_latest_prefers_newest_completed_snapshot(db_session: Session) -> None:
    older = new_id()
    newer = new_id()
    insert_workflow_run(
        db_session,
        workflow_run_id=older,
        holdings=sterling_holdings("ABC.L"),
        suggestion_tickers=(),
        cash_gbp=Decimal("0"),
        is_mock=True,
    )
    insert_workflow_run(
        db_session,
        workflow_run_id=newer,
        holdings=sterling_holdings("ABC.L"),
        suggestion_tickers=(),
        cash_gbp=Decimal("0"),
        is_mock=True,
    )
    older_thesis = mock_thesis(mock_surveyor_candidate(ticker="ABC.L")).model_copy(
        update={"mispricing_argument": "Older snapshot."}
    )
    newer_thesis = mock_thesis(mock_surveyor_candidate(ticker="ABC.L")).model_copy(
        update={"mispricing_argument": "Newer snapshot."}
    )
    persist_workflow_investment_theses(
        db_session,
        workflow_run_id=older,
        snapshots=(
            WorkflowThesisSnapshot(
                ticker="ABC.L",
                company_name="Abc plc",
                thesis=older_thesis,
                origin=WorkflowInvestmentThesisOriginDb.REPLACED,
            ),
        ),
    )
    persist_workflow_investment_theses(
        db_session,
        workflow_run_id=newer,
        snapshots=(
            WorkflowThesisSnapshot(
                ticker="abc.l",
                company_name="Abc plc",
                thesis=newer_thesis,
                origin=WorkflowInvestmentThesisOriginDb.COPIED_PRIOR,
            ),
        ),
    )
    older_wf = db_session.get(WorkflowRun, older)
    newer_wf = db_session.get(WorkflowRun, newer)
    assert older_wf is not None and newer_wf is not None
    older_wf.status = WorkflowRunStatusDb.COMPLETED
    older_wf.completed_at = datetime(2026, 8, 1, tzinfo=UTC)
    newer_wf.status = WorkflowRunStatusDb.COMPLETED
    newer_wf.completed_at = datetime(2026, 8, 30, tzinfo=UTC)
    db_session.add(older_wf)
    db_session.add(newer_wf)
    db_session.commit()

    latest = get_latest_investment_thesis_for_ticker(db_session, "Abc.L")
    assert latest is not None
    assert latest.mispricing_argument == "Newer snapshot."


def test_latest_ignores_failed_workflow_snapshots(db_session: Session) -> None:
    failed = new_id()
    insert_workflow_run(
        db_session,
        workflow_run_id=failed,
        holdings=sterling_holdings("ABC.L"),
        suggestion_tickers=(),
        cash_gbp=Decimal("0"),
        is_mock=True,
    )
    persist_workflow_investment_theses(
        db_session,
        workflow_run_id=failed,
        snapshots=(
            WorkflowThesisSnapshot(
                ticker="ABC.L",
                company_name="Abc plc",
                thesis=mock_thesis(mock_surveyor_candidate(ticker="ABC.L")),
                origin=WorkflowInvestmentThesisOriginDb.REPLACED,
            ),
        ),
    )
    workflow = db_session.get(WorkflowRun, failed)
    assert workflow is not None
    workflow.status = WorkflowRunStatusDb.FAILED
    workflow.completed_at = datetime(2026, 8, 30, tzinfo=UTC)
    db_session.add(workflow)
    db_session.commit()

    assert get_latest_investment_thesis_for_ticker(db_session, "ABC.L") is None


def test_latest_falls_back_to_chosen_strategist_row(db_session: Session) -> None:
    workflow_run_id = new_id()
    _surveyor_id, curator_id = insert_workflow_run(
        db_session,
        workflow_run_id=workflow_run_id,
        holdings=sterling_holdings("TSM"),
        suggestion_tickers=(),
        cash_gbp=Decimal("0"),
        is_mock=True,
    )
    run_id = new_id()
    insert_ticker_run_with_agents(
        db_session,
        run_id=run_id,
        workflow_run_id=workflow_run_id,
        ticker="TSM",
        company_name="TSMC",
        entry_path="profiler",
        is_existing_position=False,
        is_mock=True,
        agent_names=("strategist",),
    )
    thesis = mock_thesis(mock_surveyor_candidate(ticker="TSM", company_name="TSMC"))
    persist_mispricing_thesis(
        db_session,
        _strategist_execution(db_session, run_id),
        thesis,
        origin=WorkflowInvestmentThesisOriginDb.REPLACED,
    )
    persist_portfolio_allocation(
        db_session,
        agent_execution_id=curator_id,
        allocation=PortfolioAllocation(
            allocation_date=datetime(2026, 8, 30, tzinfo=UTC).date(),
            positions=(
                AllocationPosition(
                    ticker="TSM",
                    company_name="TSMC",
                    source_run_id=run_id,
                    is_existing_position=False,
                    current_weight_pct=0.0,
                    policy=InvestablePolicy(),
                    target_weight_pct=12.0,
                    acceptable_weight_low_pct=10.0,
                    acceptable_weight_high_pct=14.0,
                    action=RebalanceAction.ENTER,
                    rationale="Chosen.",
                ),
            ),
            cash=CashAllocation(
                current_weight_pct=100.0,
                target_weight_pct=88.0,
                acceptable_weight_low_pct=86.0,
                acceptable_weight_high_pct=90.0,
                rationale="Cash.",
            ),
            shared_risk_clusters=(),
            portfolio_rationale="Test.",
        ),
    )
    curator = db_session.get(AgentExecution, curator_id)
    assert curator is not None
    curator.status = ExecutionStatusDb.COMPLETED
    curator.completed_at = utc_now()
    db_session.add(curator)
    _complete_workflow(db_session, workflow_run_id)
    db_session.commit()

    latest = get_latest_investment_thesis_for_ticker(db_session, "tsm")
    assert latest is not None
    assert latest.mispricing_argument == thesis.mispricing_argument
    assert latest.ticker == "TSM"


def test_persist_chosen_snapshots_only_positive_targets(db_session: Session) -> None:
    workflow_run_id = new_id()
    insert_workflow_run(
        db_session,
        workflow_run_id=workflow_run_id,
        holdings=sterling_holdings("TSM", "AMAT"),
        suggestion_tickers=(),
        cash_gbp=Decimal("0"),
        is_mock=True,
    )
    tsm_run = new_id()
    amat_run = new_id()
    insert_ticker_run_with_agents(
        db_session,
        run_id=tsm_run,
        workflow_run_id=workflow_run_id,
        ticker="TSM",
        company_name="TSMC",
        entry_path="profiler",
        is_existing_position=False,
        is_mock=True,
        agent_names=("strategist",),
    )
    insert_ticker_run_with_agents(
        db_session,
        run_id=amat_run,
        workflow_run_id=workflow_run_id,
        ticker="AMAT",
        company_name="Applied Materials",
        entry_path="profiler",
        is_existing_position=False,
        is_mock=True,
        agent_names=("strategist",),
    )
    tsm_thesis = mock_thesis(mock_surveyor_candidate(ticker="TSM", company_name="TSMC"))
    persist_mispricing_thesis(
        db_session,
        _strategist_execution(db_session, tsm_run),
        tsm_thesis,
        origin=WorkflowInvestmentThesisOriginDb.REPLACED,
    )
    persist_mispricing_thesis(
        db_session,
        _strategist_execution(db_session, amat_run),
        mock_thesis(
            mock_surveyor_candidate(ticker="AMAT", company_name="Applied Materials")
        ),
        origin=WorkflowInvestmentThesisOriginDb.REPLACED,
    )
    persist_chosen_position_theses(
        db_session,
        workflow_run_id=workflow_run_id,
        allocation=PortfolioAllocation(
            allocation_date=datetime(2026, 8, 30, tzinfo=UTC).date(),
            positions=(
                AllocationPosition(
                    ticker="TSM",
                    company_name="TSMC",
                    source_run_id=tsm_run,
                    is_existing_position=False,
                    current_weight_pct=0.0,
                    policy=InvestablePolicy(),
                    target_weight_pct=12.0,
                    acceptable_weight_low_pct=10.0,
                    acceptable_weight_high_pct=14.0,
                    action=RebalanceAction.ENTER,
                    rationale="Chosen.",
                ),
                AllocationPosition(
                    ticker="AMAT",
                    company_name="Applied Materials",
                    source_run_id=amat_run,
                    is_existing_position=False,
                    current_weight_pct=0.0,
                    policy=ForcedZeroPolicy(reason=ForcedZeroReason.SELL),
                    target_weight_pct=0.0,
                    acceptable_weight_low_pct=0.0,
                    acceptable_weight_high_pct=0.0,
                    action=RebalanceAction.AVOID,
                    rationale="Avoid.",
                ),
            ),
            cash=CashAllocation(
                current_weight_pct=100.0,
                target_weight_pct=88.0,
                acceptable_weight_low_pct=86.0,
                acceptable_weight_high_pct=90.0,
                rationale="Cash.",
            ),
            shared_risk_clusters=(),
            portfolio_rationale="Test.",
        ),
    )
    db_session.commit()

    rows = list(
        db_session.scalars(
            select(WorkflowInvestmentThesis).where(
                col(WorkflowInvestmentThesis.workflow_run_id) == workflow_run_id
            )
        )
    )
    assert [row.ticker for row in rows] == ["TSM"]
    assert rows[0].origin == WorkflowInvestmentThesisOriginDb.REPLACED
    assert rows[0].mispricing_argument == tsm_thesis.mispricing_argument


def test_persist_chosen_origin_copied_prior_from_this_run_row(
    db_session: Session,
) -> None:
    prior_workflow = new_id()
    insert_workflow_run(
        db_session,
        workflow_run_id=prior_workflow,
        holdings=sterling_holdings("TSM"),
        suggestion_tickers=(),
        cash_gbp=Decimal("0"),
        is_mock=True,
    )
    thesis = mock_thesis(mock_surveyor_candidate(ticker="TSM", company_name="TSMC"))
    persist_workflow_investment_theses(
        db_session,
        workflow_run_id=prior_workflow,
        snapshots=(
            WorkflowThesisSnapshot(
                ticker="TSM",
                company_name="TSMC",
                thesis=thesis,
                origin=WorkflowInvestmentThesisOriginDb.REPLACED,
            ),
        ),
    )
    _complete_workflow(db_session, prior_workflow)

    workflow_run_id = new_id()
    insert_workflow_run(
        db_session,
        workflow_run_id=workflow_run_id,
        holdings=sterling_holdings("TSM"),
        suggestion_tickers=(),
        cash_gbp=Decimal("0"),
        is_mock=True,
    )
    run_id = new_id()
    insert_ticker_run_with_agents(
        db_session,
        run_id=run_id,
        workflow_run_id=workflow_run_id,
        ticker="TSM",
        company_name="TSMC",
        entry_path="profiler",
        is_existing_position=False,
        is_mock=True,
        agent_names=("strategist",),
    )
    persist_mispricing_thesis(
        db_session,
        _strategist_execution(db_session, run_id),
        thesis,
        origin=WorkflowInvestmentThesisOriginDb.COPIED_PRIOR,
    )
    persist_chosen_position_theses(
        db_session,
        workflow_run_id=workflow_run_id,
        allocation=_single_chosen_allocation(run_id),
    )
    db_session.commit()

    row = db_session.scalars(
        select(WorkflowInvestmentThesis).where(
            col(WorkflowInvestmentThesis.workflow_run_id) == workflow_run_id
        )
    ).one()
    assert row.origin == WorkflowInvestmentThesisOriginDb.COPIED_PRIOR
    assert row.mispricing_argument == thesis.mispricing_argument


def test_persist_chosen_origin_replaced_even_when_content_matches_prior(
    db_session: Session,
) -> None:
    prior_workflow = new_id()
    insert_workflow_run(
        db_session,
        workflow_run_id=prior_workflow,
        holdings=sterling_holdings("TSM"),
        suggestion_tickers=(),
        cash_gbp=Decimal("0"),
        is_mock=True,
    )
    thesis = mock_thesis(mock_surveyor_candidate(ticker="TSM", company_name="TSMC"))
    persist_workflow_investment_theses(
        db_session,
        workflow_run_id=prior_workflow,
        snapshots=(
            WorkflowThesisSnapshot(
                ticker="TSM",
                company_name="TSMC",
                thesis=thesis,
                origin=WorkflowInvestmentThesisOriginDb.REPLACED,
            ),
        ),
    )
    _complete_workflow(db_session, prior_workflow)

    workflow_run_id = new_id()
    insert_workflow_run(
        db_session,
        workflow_run_id=workflow_run_id,
        holdings=sterling_holdings("TSM"),
        suggestion_tickers=(),
        cash_gbp=Decimal("0"),
        is_mock=True,
    )
    run_id = new_id()
    insert_ticker_run_with_agents(
        db_session,
        run_id=run_id,
        workflow_run_id=workflow_run_id,
        ticker="TSM",
        company_name="TSMC",
        entry_path="profiler",
        is_existing_position=False,
        is_mock=True,
        agent_names=("strategist",),
    )
    persist_mispricing_thesis(
        db_session,
        _strategist_execution(db_session, run_id),
        thesis,
        origin=WorkflowInvestmentThesisOriginDb.REPLACED,
    )
    persist_chosen_position_theses(
        db_session,
        workflow_run_id=workflow_run_id,
        allocation=_single_chosen_allocation(run_id),
    )
    db_session.commit()

    row = db_session.scalars(
        select(WorkflowInvestmentThesis).where(
            col(WorkflowInvestmentThesis.workflow_run_id) == workflow_run_id
        )
    ).one()
    assert row.origin == WorkflowInvestmentThesisOriginDb.REPLACED


def test_persist_chosen_requires_a_live_thesis(db_session: Session) -> None:
    prior_workflow = new_id()
    insert_workflow_run(
        db_session,
        workflow_run_id=prior_workflow,
        holdings=sterling_holdings("TSM"),
        suggestion_tickers=(),
        cash_gbp=Decimal("0"),
        is_mock=True,
    )
    persist_workflow_investment_theses(
        db_session,
        workflow_run_id=prior_workflow,
        snapshots=(
            WorkflowThesisSnapshot(
                ticker="TSM",
                company_name="TSMC",
                thesis=mock_thesis(
                    mock_surveyor_candidate(ticker="TSM", company_name="TSMC")
                ),
                origin=WorkflowInvestmentThesisOriginDb.REPLACED,
            ),
        ),
    )
    _complete_workflow(db_session, prior_workflow)

    workflow_run_id = new_id()
    insert_workflow_run(
        db_session,
        workflow_run_id=workflow_run_id,
        holdings=sterling_holdings("TSM"),
        suggestion_tickers=(),
        cash_gbp=Decimal("0"),
        is_mock=True,
    )
    run_id = new_id()
    insert_ticker_run_with_agents(
        db_session,
        run_id=run_id,
        workflow_run_id=workflow_run_id,
        ticker="TSM",
        company_name="TSMC",
        entry_path="profiler",
        is_existing_position=False,
        is_mock=True,
        agent_names=("strategist",),
    )
    with pytest.raises(ValueError, match="no live thesis"):
        persist_chosen_position_theses(
            db_session,
            workflow_run_id=workflow_run_id,
            allocation=_single_chosen_allocation(run_id),
        )


def test_persist_strategist_keep_copies_prior_into_execution_tables(
    db_session: Session,
) -> None:
    prior_workflow = new_id()
    insert_workflow_run(
        db_session,
        workflow_run_id=prior_workflow,
        holdings=sterling_holdings("ABC.L"),
        suggestion_tickers=(),
        cash_gbp=Decimal("0"),
        is_mock=True,
    )
    prior = mock_thesis(mock_surveyor_candidate(ticker="ABC.L"))
    persist_workflow_investment_theses(
        db_session,
        workflow_run_id=prior_workflow,
        snapshots=(
            WorkflowThesisSnapshot(
                ticker="ABC.L",
                company_name=prior.company_name,
                thesis=prior,
                origin=WorkflowInvestmentThesisOriginDb.REPLACED,
            ),
        ),
    )
    _complete_workflow(db_session, prior_workflow)

    workflow_run_id = new_id()
    insert_workflow_run(
        db_session,
        workflow_run_id=workflow_run_id,
        holdings=sterling_holdings("ABC.L"),
        suggestion_tickers=(),
        cash_gbp=Decimal("0"),
        is_mock=True,
    )
    run_id = new_id()
    insert_ticker_run_with_agents(
        db_session,
        run_id=run_id,
        workflow_run_id=workflow_run_id,
        ticker="ABC.L",
        company_name=prior.company_name,
        entry_path="profiler",
        is_existing_position=False,
        is_mock=True,
        agent_names=("strategist",),
    )
    execution = _strategist_execution(db_session, run_id)
    persist_strategist_decision(
        db_session,
        execution,
        StrategistDecision(decision="keep_prior").model_dump_json(),
    )
    db_session.commit()

    reconstructed = MispricingThesis.model_validate_json(
        assistant_response_for_run_agent(db_session, execution)
    )
    assert reconstructed == prior
    stored = db_session.scalars(
        select(MispricingThesisRow).where(
            col(MispricingThesisRow.agent_execution_id) == execution.id
        )
    ).one()
    assert stored.origin == WorkflowInvestmentThesisOriginDb.COPIED_PRIOR


def test_persist_strategist_keep_without_prior_fails(db_session: Session) -> None:
    workflow_run_id = new_id()
    insert_workflow_run(
        db_session,
        workflow_run_id=workflow_run_id,
        holdings=sterling_holdings("ABC.L"),
        suggestion_tickers=(),
        cash_gbp=Decimal("0"),
        is_mock=True,
    )
    run_id = new_id()
    insert_ticker_run_with_agents(
        db_session,
        run_id=run_id,
        workflow_run_id=workflow_run_id,
        ticker="ABC.L",
        company_name="Abc plc",
        entry_path="profiler",
        is_existing_position=False,
        is_mock=True,
        agent_names=("strategist",),
    )
    execution = _strategist_execution(db_session, run_id)
    with pytest.raises(KeepPriorWithoutThesisError, match="keep_prior is invalid"):
        persist_strategist_decision(
            db_session,
            execution,
            StrategistDecision(decision="keep_prior").model_dump_json(),
        )


def _single_chosen_allocation(run_id: str) -> PortfolioAllocation:
    return PortfolioAllocation(
        allocation_date=datetime(2026, 8, 30, tzinfo=UTC).date(),
        positions=(
            AllocationPosition(
                ticker="TSM",
                company_name="TSMC",
                source_run_id=run_id,
                is_existing_position=False,
                current_weight_pct=0.0,
                policy=InvestablePolicy(),
                target_weight_pct=12.0,
                acceptable_weight_low_pct=10.0,
                acceptable_weight_high_pct=14.0,
                action=RebalanceAction.ENTER,
                rationale="Chosen.",
            ),
        ),
        cash=CashAllocation(
            current_weight_pct=100.0,
            target_weight_pct=88.0,
            acceptable_weight_low_pct=86.0,
            acceptable_weight_high_pct=90.0,
            rationale="Cash.",
        ),
        shared_risk_clusters=(),
        portfolio_rationale="Test.",
    )
