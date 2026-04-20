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
from backend.db.seed import seed
from backend.settings.config import DashboardSettings
from backend.settings.testing import LOGFIRE_TOKEN_FOR_TESTS


@pytest.fixture
def client_dev_env(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> Iterator[TestClient]:
    monkeypatch.setenv("ENV", "DEV")
    settings = DashboardSettings(
        database_path=tmp_path / "dashboard_dev.sqlite",
        logfire_token=LOGFIRE_TOKEN_FOR_TESTS,
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
