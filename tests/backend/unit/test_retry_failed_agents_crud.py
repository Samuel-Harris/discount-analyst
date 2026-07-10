"""Retry failed agents CRUD preparation tests."""

from __future__ import annotations

import pytest
from sqlmodel import Session, col, select

from backend.contracts.agent_lane_order import (
    PROFILER_ENTRY_AGENT_NAMES,
    SURVEYOR_ENTRY_AGENT_NAMES,
)
from backend.crud.db_utils import utc_now
from backend.crud.run_executions import (
    NoFailedAgentsToRetryError,
    RetryWorkflowRunNotFoundError,
    RetryWorkflowRunNotTerminalError,
    get_agent_execution_id_by_run_and_agent,
    insert_ticker_run_with_agents,
    prepare_retry_failed_agents,
)
from backend.crud.workflow_runs import (
    fetch_workflow_detail,
    insert_surveyor_workflow_execution,
    insert_workflow_run,
)
from backend.crud.db_utils import new_id
from backend.db.models import (
    AgentExecution,
    AgentNameDb,
    ExecutionStatusDb,
    Run,
    WorkflowAgentExecution,
    WorkflowRun,
    WorkflowRunStatusDb,
)


def _insert_workflow_with_profiler_lane(session: Session) -> tuple[str, str, str]:
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
        agent_names=PROFILER_ENTRY_AGENT_NAMES,
    )
    session.commit()
    return workflow_run_id, surveyor_execution_id, run_id


def _insert_workflow_with_surveyor_lane(session: Session) -> tuple[str, str, str]:
    workflow_run_id = new_id()
    surveyor_execution_id = new_id()
    run_id = new_id()
    insert_workflow_run(
        session,
        workflow_run_id=workflow_run_id,
        portfolio_tickers=["NATR"],
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
        ticker="NATR",
        company_name="Nature's Sunshine",
        entry_path="surveyor",
        is_existing_position=False,
        is_mock=True,
        agent_names=SURVEYOR_ENTRY_AGENT_NAMES,
    )
    session.commit()
    return workflow_run_id, surveyor_execution_id, run_id


def _set_agent_status(
    session: Session, *, run_id: str, agent_name: str, status: ExecutionStatusDb
) -> None:
    execution_id = get_agent_execution_id_by_run_and_agent(
        session, run_id=run_id, agent_name=agent_name
    )
    assert execution_id is not None
    execution = session.get(AgentExecution, execution_id)
    assert execution is not None
    execution.status = status
    execution.started_at = utc_now()
    execution.completed_at = utc_now()
    execution.error_message = (
        "old failure" if status == ExecutionStatusDb.FAILED else None
    )
    session.add(execution)


def test_prepare_retry_failed_agents_resets_failed_surveyor_and_lane(
    db_session: Session,
) -> None:
    workflow_run_id, surveyor_execution_id, run_id = (
        _insert_workflow_with_profiler_lane(db_session)
    )
    workflow = db_session.get(WorkflowRun, workflow_run_id)
    surveyor = db_session.get(WorkflowAgentExecution, surveyor_execution_id)
    run = db_session.get(Run, run_id)
    assert workflow is not None
    assert surveyor is not None
    assert run is not None

    workflow.status = WorkflowRunStatusDb.COMPLETED
    workflow.completed_at = utc_now()
    workflow.error_message = "old workflow error"
    surveyor.status = ExecutionStatusDb.FAILED
    surveyor.started_at = utc_now()
    surveyor.completed_at = utc_now()
    surveyor.error_message = "surveyor failed"
    run.status = WorkflowRunStatusDb.FAILED
    run.completed_at = utc_now()
    run.error_message = "lane failed"
    run.final_rating = "Hold"
    run.recommended_action = "Hold"
    _set_agent_status(
        db_session,
        run_id=run_id,
        agent_name="profiler",
        status=ExecutionStatusDb.COMPLETED,
    )
    _set_agent_status(
        db_session,
        run_id=run_id,
        agent_name="researcher",
        status=ExecutionStatusDb.FAILED,
    )
    for agent_name in ("strategist", "sentinel", "appraiser"):
        _set_agent_status(
            db_session,
            run_id=run_id,
            agent_name=agent_name,
            status=ExecutionStatusDb.SKIPPED,
        )
    db_session.commit()

    preparation = prepare_retry_failed_agents(db_session, workflow_run_id)
    db_session.commit()

    assert preparation.surveyor_reset is True
    assert preparation.lane_reset_count == 1
    detail = fetch_workflow_detail(db_session, workflow_run_id)
    assert detail is not None
    assert detail["status"] == "running"
    assert detail["error_message"] is None
    assert detail["surveyor_execution"] is not None
    assert detail["surveyor_execution"]["status"] == "pending"
    lane = detail["runs"][0]
    assert lane["status"] == "running"
    assert lane["final_rating"] is None
    statuses = {row["agent_name"]: row["status"] for row in lane["agent_executions"]}
    assert statuses["profiler"] == "completed"
    assert statuses["researcher"] == "pending"
    assert statuses["strategist"] == "pending"
    assert statuses["sentinel"] == "pending"
    assert statuses["appraiser"] == "pending"


def test_fetch_workflow_detail_can_retry_for_failed_surveyor_and_lane(
    db_session: Session,
) -> None:
    workflow_run_id, surveyor_execution_id, run_id = (
        _insert_workflow_with_profiler_lane(db_session)
    )
    workflow = db_session.get(WorkflowRun, workflow_run_id)
    surveyor = db_session.get(WorkflowAgentExecution, surveyor_execution_id)
    run = db_session.get(Run, run_id)
    assert workflow is not None
    assert surveyor is not None
    assert run is not None

    workflow.status = WorkflowRunStatusDb.FAILED
    workflow.completed_at = utc_now()
    surveyor.status = ExecutionStatusDb.FAILED
    run.status = WorkflowRunStatusDb.FAILED
    _set_agent_status(
        db_session,
        run_id=run_id,
        agent_name="researcher",
        status=ExecutionStatusDb.FAILED,
    )
    db_session.commit()

    detail = fetch_workflow_detail(db_session, workflow_run_id)
    assert detail is not None
    assert detail["can_retry_failed_agents"] is True


def test_fetch_workflow_detail_can_retry_for_gate_abort_lane(
    db_session: Session,
) -> None:
    workflow_run_id, _surveyor_execution_id, run_id = (
        _insert_workflow_with_surveyor_lane(db_session)
    )
    workflow = db_session.get(WorkflowRun, workflow_run_id)
    run = db_session.get(Run, run_id)
    assert workflow is not None
    assert run is not None

    workflow.status = WorkflowRunStatusDb.FAILED
    workflow.completed_at = utc_now()
    run.status = WorkflowRunStatusDb.FAILED
    run.completed_at = utc_now()
    for agent_name in SURVEYOR_ENTRY_AGENT_NAMES:
        _set_agent_status(
            db_session,
            run_id=run_id,
            agent_name=agent_name,
            status=ExecutionStatusDb.SKIPPED,
        )
    db_session.commit()

    detail = fetch_workflow_detail(db_session, workflow_run_id)
    assert detail is not None
    assert detail["can_retry_failed_agents"] is True


def test_fetch_workflow_detail_can_retry_false_for_running_workflow(
    db_session: Session,
) -> None:
    workflow_run_id, _, run_id = _insert_workflow_with_profiler_lane(db_session)
    _set_agent_status(
        db_session,
        run_id=run_id,
        agent_name="researcher",
        status=ExecutionStatusDb.FAILED,
    )
    db_session.commit()

    detail = fetch_workflow_detail(db_session, workflow_run_id)
    assert detail is not None
    assert detail["status"] == "running"
    assert detail["can_retry_failed_agents"] is False


def test_prepare_retry_failed_agents_resets_gate_abort_lane_with_all_skipped_agents(
    db_session: Session,
) -> None:
    workflow_run_id, _surveyor_execution_id, run_id = (
        _insert_workflow_with_surveyor_lane(db_session)
    )
    workflow = db_session.get(WorkflowRun, workflow_run_id)
    run = db_session.get(Run, run_id)
    assert workflow is not None
    assert run is not None

    workflow.status = WorkflowRunStatusDb.FAILED
    workflow.completed_at = utc_now()
    run.status = WorkflowRunStatusDb.FAILED
    run.completed_at = utc_now()
    run.error_message = (
        "Client error '429 Too Many Requests' for url "
        "'https://financialmodelingprep.com/stable/profile?symbol=NATR'"
    )
    for agent_name in SURVEYOR_ENTRY_AGENT_NAMES:
        _set_agent_status(
            db_session,
            run_id=run_id,
            agent_name=agent_name,
            status=ExecutionStatusDb.SKIPPED,
        )
    db_session.commit()

    preparation = prepare_retry_failed_agents(db_session, workflow_run_id)
    db_session.commit()

    assert preparation.surveyor_reset is False
    assert preparation.lane_reset_count == 1
    assert preparation.agent_execution_reset_count == 4
    detail = fetch_workflow_detail(db_session, workflow_run_id)
    assert detail is not None
    assert detail["status"] == "running"
    lane = detail["runs"][0]
    assert lane["status"] == "running"
    refreshed_run = db_session.get(Run, run_id)
    assert refreshed_run is not None
    assert refreshed_run.error_message is None
    statuses = {row["agent_name"]: row["status"] for row in lane["agent_executions"]}
    assert statuses == {
        "researcher": "pending",
        "strategist": "pending",
        "sentinel": "pending",
        "appraiser": "pending",
    }


def test_prepare_retry_failed_agents_rejects_running_workflow(
    db_session: Session,
) -> None:
    workflow_run_id, _surveyor_execution_id, run_id = (
        _insert_workflow_with_profiler_lane(db_session)
    )
    _set_agent_status(
        db_session,
        run_id=run_id,
        agent_name="researcher",
        status=ExecutionStatusDb.FAILED,
    )
    db_session.commit()

    with pytest.raises(RetryWorkflowRunNotTerminalError):
        prepare_retry_failed_agents(db_session, workflow_run_id)


def test_prepare_retry_failed_agents_ignores_rejected_only_lanes(
    db_session: Session,
) -> None:
    workflow_run_id, _surveyor_execution_id, run_id = (
        _insert_workflow_with_profiler_lane(db_session)
    )
    workflow = db_session.get(WorkflowRun, workflow_run_id)
    assert workflow is not None
    workflow.status = WorkflowRunStatusDb.FAILED
    workflow.completed_at = utc_now()
    _set_agent_status(
        db_session,
        run_id=run_id,
        agent_name="researcher",
        status=ExecutionStatusDb.REJECTED,
    )
    db_session.commit()

    with pytest.raises(NoFailedAgentsToRetryError):
        prepare_retry_failed_agents(db_session, workflow_run_id)

    status = db_session.scalars(
        select(AgentExecution.status).where(
            col(AgentExecution.run_id) == run_id,
            col(AgentExecution.agent_name) == AgentNameDb.RESEARCHER,
        )
    ).one()
    assert status == ExecutionStatusDb.REJECTED


def test_prepare_retry_failed_agents_resets_cancelled_children_after_surveyor_failure(
    db_session: Session,
) -> None:
    workflow_run_id, surveyor_execution_id, run_id = (
        _insert_workflow_with_profiler_lane(db_session)
    )
    workflow = db_session.get(WorkflowRun, workflow_run_id)
    surveyor = db_session.get(WorkflowAgentExecution, surveyor_execution_id)
    run = db_session.get(Run, run_id)
    assert workflow is not None
    assert surveyor is not None
    assert run is not None
    workflow.status = WorkflowRunStatusDb.FAILED
    workflow.completed_at = utc_now()
    surveyor.status = ExecutionStatusDb.FAILED
    surveyor.completed_at = utc_now()
    run.status = WorkflowRunStatusDb.CANCELLED
    run.completed_at = utc_now()
    for execution in db_session.scalars(
        select(AgentExecution).where(col(AgentExecution.run_id) == run_id)
    ):
        execution.status = ExecutionStatusDb.CANCELLED
        execution.completed_at = utc_now()
        db_session.add(execution)
    db_session.commit()

    prepare_retry_failed_agents(db_session, workflow_run_id)
    db_session.commit()

    detail = fetch_workflow_detail(db_session, workflow_run_id)
    assert detail is not None
    assert detail["surveyor_execution"] is not None
    assert detail["surveyor_execution"]["status"] == "pending"
    lane = detail["runs"][0]
    assert lane["status"] == "running"
    assert {row["status"] for row in lane["agent_executions"]} == {"pending"}


def test_prepare_retry_failed_agents_missing_workflow(db_session: Session) -> None:
    with pytest.raises(RetryWorkflowRunNotFoundError):
        prepare_retry_failed_agents(db_session, "00000000-0000-4000-8000-000000000999")
