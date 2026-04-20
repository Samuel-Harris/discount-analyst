"""Workflow cancellation and sticky terminal-state CRUD tests."""

from __future__ import annotations

from sqlmodel import Session, col, select

from backend.crud.run_executions import (
    get_agent_execution_id_by_run_and_agent,
    insert_ticker_run_with_agents,
    update_agent_execution,
    update_workflow_agent_execution,
)
from backend.crud.workflow_runs import (
    cancel_workflow_run,
    fetch_workflow_detail,
    insert_surveyor_workflow_execution,
    insert_workflow_run,
    recompute_workflow_status,
    set_workflow_error,
)
from backend.crud.db_utils import new_id, utc_now_iso
from backend.db.models import AgentExecution, Run, WorkflowAgentExecution


def _insert_workflow_fixture(session: Session) -> tuple[str, str, str]:
    workflow_run_id = new_id()
    surveyor_execution_id = new_id()
    run_id = new_id()
    insert_workflow_run(
        session,
        workflow_run_id=workflow_run_id,
        portfolio_tickers=["ABC.L"],
        is_mock=True,
    )
    insert_surveyor_workflow_execution(
        session,
        execution_id=surveyor_execution_id,
        workflow_run_id=workflow_run_id,
    )
    insert_ticker_run_with_agents(
        session,
        run_id=run_id,
        workflow_run_id=workflow_run_id,
        ticker="ABC.L",
        company_name="ABC plc",
        entry_path="profiler",
        is_existing_position=True,
        is_mock=True,
        agent_names=("profiler", "researcher"),
    )
    session.commit()
    return workflow_run_id, surveyor_execution_id, run_id


def test_cancel_workflow_run_preserves_terminal_children(db_session: Session) -> None:
    workflow_run_id, surveyor_execution_id, run_id = _insert_workflow_fixture(
        db_session
    )
    profiler_execution_id = get_agent_execution_id_by_run_and_agent(
        db_session, run_id=run_id, agent_name="profiler"
    )
    assert profiler_execution_id is not None

    update_workflow_agent_execution(
        db_session,
        execution_id=surveyor_execution_id,
        status="completed",
        started_at=utc_now_iso(),
        completed_at=utc_now_iso(),
    )
    update_agent_execution(
        db_session,
        execution_id=profiler_execution_id,
        status="completed",
        started_at=utc_now_iso(),
        completed_at=utc_now_iso(),
    )
    db_session.commit()

    assert cancel_workflow_run(db_session, workflow_run_id) is True

    detail = fetch_workflow_detail(db_session, workflow_run_id)
    assert detail is not None
    assert detail["status"] == "cancelled"
    assert detail["error_message"] is None
    assert detail["surveyor_execution"] is not None
    assert detail["surveyor_execution"]["status"] == "completed"

    run = detail["runs"][0]
    assert run["status"] == "cancelled"
    statuses = {row["agent_name"]: row["status"] for row in run["agent_executions"]}
    assert statuses["profiler"] == "completed"
    assert statuses["researcher"] == "cancelled"


def test_recompute_workflow_status_keeps_cancelled_sticky(db_session: Session) -> None:
    workflow_run_id, _surveyor_execution_id, _run_id = _insert_workflow_fixture(
        db_session
    )
    assert cancel_workflow_run(db_session, workflow_run_id) is True

    recompute_workflow_status(db_session, workflow_run_id)
    detail = fetch_workflow_detail(db_session, workflow_run_id)
    assert detail is not None
    assert detail["status"] == "cancelled"


def test_set_workflow_error_does_not_override_cancelled_workflow(
    db_session: Session,
) -> None:
    workflow_run_id, _surveyor_execution_id, _run_id = _insert_workflow_fixture(
        db_session
    )
    assert cancel_workflow_run(db_session, workflow_run_id) is True

    set_workflow_error(db_session, workflow_run_id, "provider exploded")
    detail = fetch_workflow_detail(db_session, workflow_run_id)
    assert detail is not None
    assert detail["status"] == "cancelled"
    assert detail["error_message"] is None


def test_cancel_workflow_run_marks_active_rows_cancelled(db_session: Session) -> None:
    workflow_run_id, _surveyor_execution_id, _run_id = _insert_workflow_fixture(
        db_session
    )

    assert cancel_workflow_run(db_session, workflow_run_id) is True

    workflow_exec_statuses = {
        row.status.value
        for row in db_session.scalars(
            select(WorkflowAgentExecution).where(
                col(WorkflowAgentExecution.workflow_run_id) == workflow_run_id
            )
        )
    }
    run_exec_statuses = {
        row.status.value
        for row in db_session.scalars(
            select(AgentExecution)
            .join(Run, col(AgentExecution.run_id) == col(Run.id))
            .where(col(Run.workflow_run_id) == workflow_run_id)
        )
    }
    assert workflow_exec_statuses == {"cancelled"}
    assert run_exec_statuses == {"cancelled"}
