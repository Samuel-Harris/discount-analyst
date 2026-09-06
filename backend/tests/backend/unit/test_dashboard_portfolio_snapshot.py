"""Dashboard Curator loads the persisted sterling ledger as a snapshot."""

from decimal import Decimal

import pytest
from sqlmodel import Session

from backend.tests.factories.sterling import sterling_holdings
from discount_analyst.adapters.orchestration.stages.curator_stage import (
    load_dashboard_portfolio_snapshot,
)
from discount_analyst.adapters.persistence.crud.agent_output_persistence import (
    persist_profiler_output,
)
from discount_analyst.adapters.persistence.crud.db_utils import new_id, utc_now
from discount_analyst.adapters.persistence.crud.run_executions import (
    get_agent_execution_id_by_run_and_agent,
    insert_ticker_run_with_agents,
    update_ticker_run_ticker,
)
from discount_analyst.adapters.persistence.crud.workflow_runs import insert_workflow_run
from discount_analyst.adapters.persistence.models import (
    AgentExecution,
    WorkflowRun,
    WorkflowRunPortfolioTicker,
    WorkflowRunStatusDb,
)
from discount_analyst.adapters.simulation.mock_outputs import mock_profiler_output
from discount_analyst.domain.allocations.snapshot import SterlingPosition


def test_loader_converts_unequal_sterling_ledger(db_session: Session) -> None:
    workflow_run_id = new_id()
    insert_workflow_run(
        db_session,
        workflow_run_id=workflow_run_id,
        holdings=(
            SterlingPosition(ticker="A.L", value_gbp=Decimal("7000.00")),
            SterlingPosition(ticker="B.L", value_gbp=Decimal("1000.00")),
        ),
        suggestion_tickers=("HINT.L",),
        cash_gbp=Decimal("2000.00"),
        is_mock=False,
    )

    snapshot = load_dashboard_portfolio_snapshot(db_session, workflow_run_id)

    workflow = db_session.get(WorkflowRun, workflow_run_id)
    assert workflow is not None
    assert snapshot.as_of == workflow.started_at.date()
    assert [position.ticker for position in snapshot.positions] == ["A.L", "B.L"]
    assert snapshot.positions[0].current_weight_pct == 70.0
    assert snapshot.positions[1].current_weight_pct == 10.0
    assert snapshot.cash_weight_pct == 20.0


def test_loader_rejects_pre_ledger_workflow(db_session: Session) -> None:
    workflow_run_id = new_id()
    db_session.add(
        WorkflowRun(
            id=workflow_run_id,
            started_at=utc_now(),
            completed_at=None,
            status=WorkflowRunStatusDb.RUNNING,
            is_mock=True,
            error_message=None,
            cash_gbp=None,
        )
    )
    db_session.add(
        WorkflowRunPortfolioTicker(
            id=new_id(),
            workflow_run_id=workflow_run_id,
            sort_order=0,
            ticker="OLD.L",
            value_gbp=None,
        )
    )
    db_session.commit()

    with pytest.raises(RuntimeError, match="without a sterling ledger"):
        load_dashboard_portfolio_snapshot(db_session, workflow_run_id)


def test_loader_uses_resolved_run_ticker_for_holdings(db_session: Session) -> None:
    workflow_run_id = new_id()
    run_id = new_id()
    insert_workflow_run(
        db_session,
        workflow_run_id=workflow_run_id,
        holdings=sterling_holdings("CBOX", value_gbp=Decimal("1000.00")),
        suggestion_tickers=(),
        cash_gbp=Decimal("0"),
        is_mock=False,
    )
    insert_ticker_run_with_agents(
        db_session,
        run_id=run_id,
        workflow_run_id=workflow_run_id,
        ticker="CBOX",
        company_name="CBOX",
        entry_path="profiler",
        is_existing_position=True,
        is_mock=False,
        agent_names=("profiler",),
    )
    db_session.commit()
    execution_id = get_agent_execution_id_by_run_and_agent(
        db_session, run_id=run_id, agent_name="profiler"
    )
    assert execution_id is not None
    execution = db_session.get(AgentExecution, execution_id)
    assert execution is not None
    persist_profiler_output(
        db_session, execution, mock_profiler_output(ticker="CBOX").model_dump_json()
    )
    update_ticker_run_ticker(db_session, run_id=run_id, ticker="CBOX.L")
    db_session.commit()

    snapshot = load_dashboard_portfolio_snapshot(db_session, workflow_run_id)

    assert [position.ticker for position in snapshot.positions] == ["CBOX.L"]
    assert snapshot.positions[0].current_weight_pct == 100.0
