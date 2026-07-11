"""Tests for structured agent output persistence."""

from sqlmodel import Session, col, select

from discount_analyst.adapters.persistence.crud.agent_output_persistence import (
    persist_profiler_output,
)
from discount_analyst.adapters.persistence.crud.db_utils import new_id
from discount_analyst.adapters.persistence.crud.run_executions import (
    get_agent_execution_id_by_run_and_agent,
    insert_ticker_run_with_agents,
)
from discount_analyst.adapters.persistence.crud.workflow_runs import insert_workflow_run
from discount_analyst.adapters.persistence.models import (
    AgentExecution,
    CandidateSnapshot,
    Run,
)
from discount_analyst.adapters.simulation.mock_outputs import mock_profiler_output


def test_persist_profiler_output_writes_one_first_candidate_snapshot(
    db_session: Session,
) -> None:
    workflow_run_id = new_id()
    run_id = new_id()
    insert_workflow_run(
        db_session,
        workflow_run_id=workflow_run_id,
        portfolio_tickers=["ABC.L"],
        is_mock=True,
    )
    insert_ticker_run_with_agents(
        db_session,
        run_id=run_id,
        workflow_run_id=workflow_run_id,
        ticker="ABC.L",
        company_name="ABC plc",
        entry_path="profiler",
        is_existing_position=True,
        is_mock=True,
        agent_names=("profiler",),
    )
    db_session.commit()

    execution_id = get_agent_execution_id_by_run_and_agent(
        db_session,
        run_id=run_id,
        agent_name="profiler",
    )
    assert execution_id is not None
    execution = db_session.get(AgentExecution, execution_id)
    assert execution is not None
    output = mock_profiler_output(ticker="ABC.L")

    persist_profiler_output(db_session, execution, output.model_dump_json())
    db_session.commit()
    persist_profiler_output(db_session, execution, output.model_dump_json())
    db_session.commit()

    snapshots = db_session.scalars(
        select(CandidateSnapshot).where(
            col(CandidateSnapshot.agent_execution_id) == execution_id
        )
    ).all()
    assert len(snapshots) == 1
    assert snapshots[0].sort_order == 0
    assert snapshots[0].ticker == "ABC.L"

    run = db_session.get(Run, run_id)
    assert run is not None
    assert run.candidate_snapshot_id == snapshots[0].id
