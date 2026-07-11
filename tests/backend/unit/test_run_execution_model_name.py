"""Unit tests for agent execution model_name persistence."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest
from sqlmodel import Session, select

from backend.crud.db_utils import new_id, utc_now
from backend.crud.run_executions import (
    apply_agent_execution_status,
    prepare_retry_failed_agents,
)
from backend.db.models import (
    AgentExecution,
    AgentNameDb,
    ExecutionStatusDb,
    WorkflowRun,
    WorkflowRunStatusDb,
)
from backend.settings.testing import dashboard_settings_for_tests
from discount_analyst.models.model_name import ModelName


@pytest.fixture
def session(tmp_path: Path) -> Iterator[Session]:
    from backend.app.main import create_app

    settings = dashboard_settings_for_tests(database_path=tmp_path / "crud.sqlite")
    app = create_app(settings)
    factory = app.state.db_session_factory
    with factory() as s:
        yield s


def _insert_workflow_run(session: Session, *, workflow_run_id: str) -> None:
    session.add(
        WorkflowRun(
            id=workflow_run_id,
            started_at=utc_now(),
            completed_at=None,
            status=WorkflowRunStatusDb.RUNNING,
            is_mock=False,
            error_message=None,
        )
    )
    session.commit()


def test_apply_agent_execution_status_sets_model_name(session: Session) -> None:
    from backend.crud.run_executions import insert_ticker_run_with_agents

    workflow_run_id = new_id()
    run_id = new_id()
    _insert_workflow_run(session, workflow_run_id=workflow_run_id)
    insert_ticker_run_with_agents(
        session,
        run_id=run_id,
        workflow_run_id=workflow_run_id,
        ticker="TST.L",
        company_name="Test Co",
        entry_path="profiler",
        is_existing_position=False,
        is_mock=False,
        agent_names=("profiler",),
    )
    session.commit()

    execution = session.exec(
        select(AgentExecution).where(AgentExecution.run_id == run_id)
    ).one()
    apply_agent_execution_status(
        session,
        execution_id=execution.id,
        status=ExecutionStatusDb.RUNNING.value,
        model_name=ModelName.GPT_5_1,
    )
    session.commit()

    refreshed = session.get(AgentExecution, execution.id)
    assert refreshed is not None
    assert refreshed.model_name == ModelName.GPT_5_1


def test_apply_workflow_scoped_agent_execution_status_sets_model_name(
    session: Session,
) -> None:
    workflow_run_id = new_id()
    execution_id = new_id()
    _insert_workflow_run(session, workflow_run_id=workflow_run_id)
    session.add(
        AgentExecution(
            id=execution_id,
            workflow_run_id=workflow_run_id,
            run_id=None,
            agent_name=AgentNameDb.SURVEYOR,
            status=ExecutionStatusDb.PENDING,
        )
    )
    session.commit()

    apply_agent_execution_status(
        session,
        execution_id=execution_id,
        status=ExecutionStatusDb.RUNNING.value,
        model_name=ModelName.CLAUDE_OPUS_4_6,
    )
    session.commit()

    refreshed = session.get(AgentExecution, execution_id)
    assert refreshed is not None
    assert refreshed.model_name == ModelName.CLAUDE_OPUS_4_6


def test_retry_failed_agents_clears_model_name(session: Session) -> None:
    workflow_run_id = new_id()
    execution_id = new_id()
    _insert_workflow_run(session, workflow_run_id=workflow_run_id)
    workflow = session.get(WorkflowRun, workflow_run_id)
    assert workflow is not None
    workflow.status = WorkflowRunStatusDb.FAILED
    session.add(workflow)
    session.add(
        AgentExecution(
            id=execution_id,
            workflow_run_id=workflow_run_id,
            run_id=None,
            agent_name=AgentNameDb.SURVEYOR,
            status=ExecutionStatusDb.FAILED,
            model_name=ModelName.GPT_5_2,
        )
    )
    session.commit()

    prepare_retry_failed_agents(session, workflow_run_id)
    session.commit()

    refreshed = session.get(AgentExecution, execution_id)
    assert refreshed is not None
    assert refreshed.status == ExecutionStatusDb.PENDING
    assert refreshed.model_name is None
