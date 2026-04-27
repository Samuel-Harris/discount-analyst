"""HTTP contract tests with an isolated SQLite database per test module."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path
from typing import cast

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.app.main import create_app
from backend.contracts.agent_lane_order import PROFILER_ENTRY_AGENT_NAMES
from backend.crud.db_utils import new_id, utc_now
from backend.crud.run_executions import (
    get_agent_execution_id_by_run_and_agent,
    insert_ticker_run_with_agents,
)
from backend.crud.workflow_runs import (
    insert_surveyor_workflow_execution,
    insert_workflow_run,
)
from backend.db.models import (
    AgentExecution,
    ExecutionStatusDb,
    Run,
    WorkflowAgentExecution,
    WorkflowRun,
    WorkflowRunStatusDb,
)
from backend.db.seed import seed
from backend.settings.testing import dashboard_settings_for_tests


@pytest.fixture
def client_dev_env(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> Iterator[TestClient]:
    monkeypatch.setenv("ENV", "DEV")
    settings = dashboard_settings_for_tests(
        database_path=tmp_path / "dashboard_dev.sqlite",
        deploy_env="DEV",
    )
    with TestClient(create_app(settings)) as test_client:
        yield test_client


def test_list_workflow_runs_empty(client: TestClient) -> None:
    r = client.get("/api/workflow_runs")
    assert r.status_code == 200
    assert r.json() == []


def test_dev_deploy_env_forces_mock_even_when_client_requests_live(
    client_dev_env: TestClient,
) -> None:
    r = client_dev_env.post(
        "/api/workflow_runs",
        json={"portfolio_tickers": ["X.L"], "is_mock": False},
    )
    assert r.status_code == 201
    listed = client_dev_env.get("/api/workflow_runs").json()
    assert len(listed) == 1
    assert listed[0]["is_mock"] is True


def test_post_and_list_workflow_run(client: TestClient) -> None:
    body = {"portfolio_tickers": ["AAA.L", "BBB.L"], "is_mock": True}
    r = client.post("/api/workflow_runs", json=body)
    assert r.status_code == 201
    data = r.json()
    assert "workflow_run_id" in data
    assert len(data["profiler_runs"]) == 2
    assert data["surveyor_started"] is True

    listed = client.get("/api/workflow_runs").json()
    assert len(listed) == 1
    assert listed[0]["ticker_run_count"] == 2


def test_get_workflow_detail(client: TestClient) -> None:
    client.post(
        "/api/workflow_runs", json={"portfolio_tickers": ["X.L"], "is_mock": True}
    )
    wf_id = client.get("/api/workflow_runs").json()[0]["id"]
    d = client.get(f"/api/workflow_runs/{wf_id}").json()
    assert d["id"] == wf_id
    assert d["surveyor_execution"]["agent_name"] == "surveyor"
    assert len(d["runs"]) == 1
    names = [a["agent_name"] for a in d["runs"][0]["agent_executions"]]
    assert names == list(PROFILER_ENTRY_AGENT_NAMES)


def test_delete_mock_only(client: TestClient) -> None:
    client.post("/api/workflow_runs", json={"portfolio_tickers": [], "is_mock": False})
    real_id = client.get("/api/workflow_runs").json()[0]["id"]
    assert client.delete(f"/api/workflow_runs/{real_id}").status_code == 403

    client.post("/api/workflow_runs", json={"portfolio_tickers": [], "is_mock": True})
    rows = client.get("/api/workflow_runs").json()
    mock_id = next(x["id"] for x in rows if x["is_mock"] is True)
    assert client.delete(f"/api/workflow_runs/{mock_id}").status_code == 204


def test_cancel_workflow_run_not_found(client: TestClient) -> None:
    response = client.post(
        "/api/workflow_runs/00000000-0000-4000-8000-000000000999/cancel"
    )
    assert response.status_code == 404


def test_cancel_workflow_run_is_idempotent(client: TestClient) -> None:
    create_response = client.post(
        "/api/workflow_runs",
        json={"portfolio_tickers": ["CXL.L"], "is_mock": True},
    )
    workflow_run_id = create_response.json()["workflow_run_id"]

    first_cancel = client.post(f"/api/workflow_runs/{workflow_run_id}/cancel")
    second_cancel = client.post(f"/api/workflow_runs/{workflow_run_id}/cancel")

    assert first_cancel.status_code == 204
    assert second_cancel.status_code == 204
    detail = client.get(f"/api/workflow_runs/{workflow_run_id}").json()
    assert detail["status"] == "cancelled"
    assert detail["error_message"] is None


def test_portfolio_latest(client: TestClient) -> None:
    assert client.get("/api/portfolio").json() == {"portfolio_tickers": []}
    client.post(
        "/api/workflow_runs",
        json={"portfolio_tickers": ["P1", "P2"], "is_mock": True},
    )
    assert client.get("/api/portfolio").json() == {"portfolio_tickers": ["P1", "P2"]}


def test_seed_and_detail_shape(client: TestClient) -> None:
    app = cast(FastAPI, client.app)
    with app.state.db_session_factory() as session:
        seed(session)
    listed = client.get("/api/workflow_runs").json()
    assert len(listed) == 1
    wf_id = listed[0]["id"]
    detail = client.get(f"/api/workflow_runs/{wf_id}").json()
    assert len(detail["runs"]) == 2
    paths = {x["entry_path"] for x in detail["runs"]}
    assert paths == {"profiler", "surveyor"}


def test_surveyor_conversation_after_seed(client: TestClient) -> None:
    app = cast(FastAPI, client.app)
    with app.state.db_session_factory() as session:
        seed(session)
    wf_id = client.get("/api/workflow_runs").json()[0]["id"]
    r = client.get(f"/api/agents/workflow_runs/{wf_id}/agents/surveyor/conversation")
    assert r.status_code == 200
    assert "assistant_response" in r.json()


def test_run_agent_conversation_after_seed(client: TestClient) -> None:
    app = cast(FastAPI, client.app)
    with app.state.db_session_factory() as session:
        seed(session)
    detail = client.get("/api/workflow_runs").json()
    wf_id = detail[0]["id"]
    runs = client.get(f"/api/workflow_runs/{wf_id}").json()["runs"]
    run_profiler = next(r for r in runs if r["entry_path"] == "profiler")
    r = client.get(
        f"/api/agents/runs/{run_profiler['id']}/agents/profiler/conversation"
    )
    assert r.status_code == 200


def _insert_retryable_workflow(app: FastAPI) -> tuple[str, str]:
    workflow_run_id = new_id()
    surveyor_execution_id = new_id()
    run_id = new_id()
    with app.state.db_session_factory() as session:
        insert_workflow_run(
            session,
            workflow_run_id=workflow_run_id,
            portfolio_tickers=["RET.L"],
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
            ticker="RET.L",
            company_name="Retry plc",
            entry_path="profiler",
            is_existing_position=True,
            is_mock=True,
            agent_names=PROFILER_ENTRY_AGENT_NAMES,
        )
        workflow = session.get(WorkflowRun, workflow_run_id)
        surveyor = session.get(WorkflowAgentExecution, surveyor_execution_id)
        run = session.get(Run, run_id)
        assert workflow is not None
        assert surveyor is not None
        assert run is not None
        workflow.status = WorkflowRunStatusDb.COMPLETED
        workflow.completed_at = utc_now()
        surveyor.status = ExecutionStatusDb.COMPLETED
        surveyor.completed_at = utc_now()
        run.status = WorkflowRunStatusDb.FAILED
        run.completed_at = utc_now()
        researcher_id = get_agent_execution_id_by_run_and_agent(
            session, run_id=run_id, agent_name="researcher"
        )
        assert researcher_id is not None
        researcher = session.get(AgentExecution, researcher_id)
        assert researcher is not None
        researcher.status = ExecutionStatusDb.FAILED
        researcher.completed_at = utc_now()
        researcher.error_message = "researcher failed"
        session.add(workflow)
        session.add(surveyor)
        session.add(run)
        session.add(researcher)
        session.commit()
    return workflow_run_id, run_id


def test_retry_failed_agents_not_found(client: TestClient) -> None:
    response = client.post(
        "/api/workflow_runs/00000000-0000-4000-8000-000000000999/retry_failed_agents"
    )
    assert response.status_code == 404


def test_retry_failed_agents_requires_terminal_workflow(client: TestClient) -> None:
    app = cast(FastAPI, client.app)
    workflow_run_id, run_id = _insert_retryable_workflow(app)
    with app.state.db_session_factory() as session:
        workflow = session.get(WorkflowRun, workflow_run_id)
        assert workflow is not None
        workflow.status = WorkflowRunStatusDb.RUNNING
        workflow.completed_at = None
        session.add(workflow)
        run = session.get(Run, run_id)
        assert run is not None
        run.status = WorkflowRunStatusDb.RUNNING
        session.add(run)
        session.commit()

    response = client.post(f"/api/workflow_runs/{workflow_run_id}/retry_failed_agents")

    assert response.status_code == 409


def test_retry_failed_agents_returns_400_when_no_failed_agents(
    client: TestClient,
) -> None:
    app = cast(FastAPI, client.app)
    workflow_run_id, run_id = _insert_retryable_workflow(app)
    with app.state.db_session_factory() as session:
        researcher_id = get_agent_execution_id_by_run_and_agent(
            session, run_id=run_id, agent_name="researcher"
        )
        assert researcher_id is not None
        researcher = session.get(AgentExecution, researcher_id)
        assert researcher is not None
        researcher.status = ExecutionStatusDb.REJECTED
        researcher.error_message = None
        session.add(researcher)
        session.commit()

    response = client.post(f"/api/workflow_runs/{workflow_run_id}/retry_failed_agents")

    assert response.status_code == 400


def test_retry_failed_agents_returns_409_when_runner_task_active(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    app = cast(FastAPI, client.app)
    workflow_run_id, _run_id = _insert_retryable_workflow(app)
    monkeypatch.setattr(
        app.state.pipeline_runner,
        "has_active_workflow_task",
        lambda _workflow_run_id: True,
    )

    response = client.post(f"/api/workflow_runs/{workflow_run_id}/retry_failed_agents")

    assert response.status_code == 409


def test_retry_failed_agents_prepares_and_schedules(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    app = cast(FastAPI, client.app)
    workflow_run_id, run_id = _insert_retryable_workflow(app)
    scheduled: list[str] = []
    monkeypatch.setattr(
        app.state.pipeline_runner,
        "schedule_workflow_execution",
        lambda workflow_id: scheduled.append(workflow_id),
    )

    response = client.post(f"/api/workflow_runs/{workflow_run_id}/retry_failed_agents")

    assert response.status_code == 202
    assert scheduled == [workflow_run_id]
    detail = client.get(f"/api/workflow_runs/{workflow_run_id}").json()
    assert detail["status"] == "running"
    lane = next(run for run in detail["runs"] if run["id"] == run_id)
    statuses = {row["agent_name"]: row["status"] for row in lane["agent_executions"]}
    assert statuses["researcher"] == "pending"
