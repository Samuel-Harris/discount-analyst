"""Portfolio allocation persistence, reconstruction, and workflow creation."""

from datetime import date

from sqlmodel import Session, col, select

from discount_analyst.adapters.persistence.crud.db_utils import new_id
from discount_analyst.adapters.persistence.crud.portfolio_allocations import (
    delete_portfolio_allocation_for_execution,
    get_portfolio_allocation_for_execution,
    persist_portfolio_allocation,
)
from discount_analyst.adapters.persistence.crud.run_executions import (
    insert_ticker_run_with_agents,
)
from discount_analyst.adapters.persistence.crud.workflow_runs import insert_workflow_run
from discount_analyst.adapters.persistence.models import AgentExecution, AgentNameDb
from discount_analyst.application.allocations.skip_reasons import (
    LEGACY_WORKFLOW_WITHOUT_POSITION_SNAPSHOT,
)
from discount_analyst.domain.allocations.actions import RebalanceAction
from discount_analyst.domain.allocations.allocation import (
    AllocationPosition,
    CashAllocation,
    PortfolioAllocation,
    SharedRiskCluster,
)
from discount_analyst.domain.allocations.policy import (
    ForcedZeroPolicy,
    ForcedZeroReason,
    InvestablePolicy,
)


def test_insert_workflow_run_creates_surveyor_and_curator(
    db_session: Session,
) -> None:
    workflow_run_id = new_id()
    surveyor_id, curator_id = insert_workflow_run(
        db_session,
        workflow_run_id=workflow_run_id,
        portfolio_tickers=["ABC.L"],
        is_mock=True,
    )

    executions = list(
        db_session.scalars(
            select(AgentExecution).where(
                col(AgentExecution.workflow_run_id) == workflow_run_id
            )
        )
    )
    names = {row.agent_name: row for row in executions}
    assert names[AgentNameDb.SURVEYOR].id == surveyor_id
    assert names[AgentNameDb.CURATOR].id == curator_id
    assert names[AgentNameDb.CURATOR].error_message != (
        LEGACY_WORKFLOW_WITHOUT_POSITION_SNAPSHOT
    )


def test_persist_and_reconstruct_allocation_round_trip(db_session: Session) -> None:
    workflow_run_id = new_id()
    _surveyor_id, curator_id = insert_workflow_run(
        db_session,
        workflow_run_id=workflow_run_id,
        portfolio_tickers=["TSM", "AMAT"],
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
        agent_names=("profiler",),
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
        agent_names=("profiler",),
    )
    db_session.commit()
    original = PortfolioAllocation(
        allocation_date=date(2026, 8, 30),
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
                rationale="Stronger foundry idea.",
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
                rationale="Forced zero.",
            ),
        ),
        cash=CashAllocation(
            current_weight_pct=100.0,
            target_weight_pct=88.0,
            acceptable_weight_low_pct=84.0,
            acceptable_weight_high_pct=92.0,
            rationale="Residual cash.",
        ),
        shared_risk_clusters=(
            SharedRiskCluster(
                label="Semiconductor supply chain",
                member_tickers=("TSM", "AMAT"),
                mechanism="Shared foundry demand shock.",
                allocation_effect="AMAT forced to zero; TSM kept.",
            ),
        ),
        portfolio_rationale="Keep the stronger name.",
    )

    persist_portfolio_allocation(
        db_session, agent_execution_id=curator_id, allocation=original
    )
    db_session.commit()

    loaded = get_portfolio_allocation_for_execution(db_session, curator_id)
    assert loaded == original

    delete_portfolio_allocation_for_execution(db_session, curator_id)
    db_session.commit()
    assert get_portfolio_allocation_for_execution(db_session, curator_id) is None
