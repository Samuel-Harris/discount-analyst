"""HTTP contract tests with an isolated SQLite database per test module."""

from __future__ import annotations

from collections.abc import Iterator
from decimal import Decimal
from pathlib import Path
from typing import cast

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.tests.factories.sterling import sterling_holdings
from discount_analyst.adapters.observability.yfinance_freshness import YfinanceFreshness
from discount_analyst.composition.api import create_app
from discount_analyst.application.workflows.agent_lane_order import (
    PROFILER_ENTRY_AGENT_NAMES,
)
from discount_analyst.adapters.persistence.crud.db_utils import new_id, utc_now
from discount_analyst.adapters.persistence.crud.run_executions import (
    get_agent_execution_id_by_run_and_agent,
    insert_ticker_run_with_agents,
)
from discount_analyst.adapters.persistence.crud.workflow_runs import (
    insert_workflow_run,
)
from discount_analyst.adapters.persistence.models import (
    AgentExecution,
    ExecutionStatusDb,
    Run,
    WorkflowRun,
    WorkflowRunPortfolioTicker,
    WorkflowRunStatusDb,
)
from discount_analyst.composition.dev_seed import seed
from discount_analyst.config.settings import Settings
from discount_analyst.config.testing_settings import dashboard_settings_for_tests


def _launch_json(
    *tickers: str,
    cash_gbp: float = 0,
    suggestions: list[str] | None = None,
    is_mock: bool = True,
    value_gbp: float = 1000,
) -> dict[str, object]:
    return {
        "positions": [{"ticker": ticker, "value_gbp": value_gbp} for ticker in tickers],
        "cash_gbp": cash_gbp,
        "suggestion_tickers": suggestions or [],
        "is_mock": is_mock,
    }


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


def test_dashboard_status_reports_current_yfinance(client: TestClient) -> None:
    response = client.get("/api/status")
    assert response.status_code == 200
    payload = response.json()["yfinance"]
    assert payload["is_outdated"] is False
    assert payload["installed_version"]
    assert payload["latest_version"] == payload["installed_version"]


def test_dashboard_status_reports_outdated_yfinance(
    dashboard_settings: Settings,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def _outdated() -> YfinanceFreshness:
        return YfinanceFreshness(
            installed_version="1.6.0",
            latest_version="1.7.0",
            is_outdated=True,
        )

    monkeypatch.setattr(
        "discount_analyst.entrypoints.api.routers.status.check_yfinance_freshness",
        _outdated,
    )
    with TestClient(create_app(dashboard_settings)) as test_client:
        payload = test_client.get("/api/status").json()["yfinance"]
    assert payload == {
        "installed_version": "1.6.0",
        "latest_version": "1.7.0",
        "is_outdated": True,
    }


def test_dev_deploy_env_forces_mock_even_when_client_requests_live(
    client_dev_env: TestClient,
) -> None:
    r = client_dev_env.post(
        "/api/workflow_runs",
        json=_launch_json("X.L", is_mock=False),
    )
    assert r.status_code == 201
    listed = client_dev_env.get("/api/workflow_runs").json()
    assert len(listed) == 1
    assert listed[0]["is_mock"] is True


def test_post_and_list_workflow_run(client: TestClient) -> None:
    body = _launch_json("AAA.L", "BBB.L")
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
    client.post("/api/workflow_runs", json=_launch_json("X.L"))
    wf_id = client.get("/api/workflow_runs").json()[0]["id"]
    d = client.get(f"/api/workflow_runs/{wf_id}").json()
    assert d["id"] == wf_id
    assert d["surveyor_execution"]["agent_name"] == "surveyor"
    assert len(d["runs"]) == 1
    names = [a["agent_name"] for a in d["runs"][0]["agent_executions"]]
    assert names == list(PROFILER_ENTRY_AGENT_NAMES)


def test_delete_mock_only(client: TestClient) -> None:
    client.post("/api/workflow_runs", json=_launch_json(is_mock=False))
    real_id = client.get("/api/workflow_runs").json()[0]["id"]
    assert client.delete(f"/api/workflow_runs/{real_id}").status_code == 403

    client.post("/api/workflow_runs", json=_launch_json())
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
        json=_launch_json("CXL.L"),
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
    assert client.get("/api/portfolio").json() == {
        "positions": [],
        "cash_gbp": 0.0,
        "suggestion_tickers": [],
    }
    client.post(
        "/api/workflow_runs",
        json=_launch_json("P1", "P2", cash_gbp=250.5),
    )
    assert client.get("/api/portfolio").json() == {
        "positions": [
            {"ticker": "P1", "value_gbp": 1000.0},
            {"ticker": "P2", "value_gbp": 1000.0},
        ],
        "cash_gbp": 250.5,
        "suggestion_tickers": [],
    }


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


def test_curator_conversation_after_seed(client: TestClient) -> None:
    app = cast(FastAPI, client.app)
    with app.state.db_session_factory() as session:
        seed(session)
    wf_id = client.get("/api/workflow_runs").json()[0]["id"]
    r = client.get(f"/api/agents/workflow_runs/{wf_id}/agents/curator/conversation")
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
            holdings=sterling_holdings("RET.L"),
            suggestion_tickers=(),
            cash_gbp=Decimal("0"),
            is_mock=True,
            surveyor_execution_id=surveyor_execution_id,
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
        surveyor = session.get(AgentExecution, surveyor_execution_id)
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

    def _stub_has_active(_workflow_run_id: str) -> bool:
        return True

    monkeypatch.setattr(
        app.state.pipeline_runner,
        "has_active_workflow_task",
        _stub_has_active,
    )

    response = client.post(f"/api/workflow_runs/{workflow_run_id}/retry_failed_agents")

    assert response.status_code == 409


def test_retry_failed_agents_prepares_and_schedules(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    app = cast(FastAPI, client.app)
    workflow_run_id, run_id = _insert_retryable_workflow(app)
    scheduled: list[str] = []

    def _capture_schedule(workflow_id: str) -> None:
        scheduled.append(workflow_id)

    monkeypatch.setattr(
        app.state.pipeline_runner,
        "schedule_workflow_execution",
        _capture_schedule,
    )

    response = client.post(f"/api/workflow_runs/{workflow_run_id}/retry_failed_agents")

    assert response.status_code == 202
    assert scheduled == [workflow_run_id]
    detail = client.get(f"/api/workflow_runs/{workflow_run_id}").json()
    assert detail["status"] == "running"
    lane = next(run for run in detail["runs"] if run["id"] == run_id)
    statuses = {row["agent_name"]: row["status"] for row in lane["agent_executions"]}
    assert statuses["researcher"] == "pending"


def test_create_workflow_run_holdings_and_suggestions(client: TestClient) -> None:
    response = client.post(
        "/api/workflow_runs",
        json=_launch_json("HOLD.L", cash_gbp=500, suggestions=["HINT.L"]),
    )
    assert response.status_code == 201
    created = response.json()
    tickers = [run["ticker"] for run in created["profiler_runs"]]
    assert tickers == ["HOLD.L", "HINT.L"]
    wf_id = created["workflow_run_id"]
    detail = client.get(f"/api/workflow_runs/{wf_id}").json()
    by_ticker = {run["ticker"]: run for run in detail["runs"]}
    assert by_ticker["HOLD.L"]["entry_path"] == "profiler"
    assert by_ticker["HINT.L"]["entry_path"] == "profiler"


def test_create_workflow_run_drops_overlapping_suggestion(client: TestClient) -> None:
    response = client.post(
        "/api/workflow_runs",
        json=_launch_json("ABC.L", suggestions=["abc.l", "HINT.L"]),
    )
    assert response.status_code == 201
    tickers = [run["ticker"] for run in response.json()["profiler_runs"]]
    assert tickers == ["ABC.L", "HINT.L"]
    portfolio = client.get("/api/portfolio").json()
    assert [row["ticker"] for row in portfolio["positions"]] == ["ABC.L"]
    assert portfolio["suggestion_tickers"] == ["HINT.L"]


def test_create_empty_ledger_is_allowed(client: TestClient) -> None:
    response = client.post("/api/workflow_runs", json=_launch_json())
    assert response.status_code == 201
    assert response.json()["profiler_runs"] == []


def test_create_rejects_duplicate_holdings(client: TestClient) -> None:
    response = client.post(
        "/api/workflow_runs",
        json=_launch_json("Abc.L", "ABC.L"),
    )
    assert response.status_code == 422


def test_create_rejects_duplicate_suggestions(client: TestClient) -> None:
    response = client.post(
        "/api/workflow_runs",
        json=_launch_json(suggestions=["Hint.L", "HINT.L"]),
    )
    assert response.status_code == 422


def test_create_rejects_negative_values(client: TestClient) -> None:
    response = client.post(
        "/api/workflow_runs",
        json={
            "positions": [{"ticker": "ABC.L", "value_gbp": -1}],
            "cash_gbp": 0,
            "suggestion_tickers": [],
            "is_mock": True,
        },
    )
    assert response.status_code == 422


def test_portfolio_prefill_old_run_without_ledger_uses_suggestions(
    client: TestClient,
) -> None:
    app = cast(FastAPI, client.app)
    workflow_run_id = new_id()
    with app.state.db_session_factory() as session:
        session.add(
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
        session.add(
            WorkflowRunPortfolioTicker(
                id=new_id(),
                workflow_run_id=workflow_run_id,
                sort_order=0,
                ticker="OLD.L",
                value_gbp=None,
            )
        )
        session.commit()
    assert client.get("/api/portfolio").json() == {
        "positions": [],
        "cash_gbp": 0.0,
        "suggestion_tickers": ["OLD.L"],
    }
