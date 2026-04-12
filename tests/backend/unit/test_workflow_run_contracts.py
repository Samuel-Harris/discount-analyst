"""Pydantic validation of HTTP JSON against agreed workflow-run API contracts."""

from __future__ import annotations

import time
from typing import cast
from uuid import UUID

from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.contracts.api import (
    ConversationResponse,
    CreateWorkflowRunResponse,
    PortfolioResponse,
    WorkflowRunDetailResponse,
    WorkflowRunListItem,
)
from backend.db.seed import seed


def _assert_uuid(value: str) -> None:
    UUID(value)


def test_list_workflow_runs_items_match_workflow_run_list_item(
    client: TestClient,
) -> None:
    client.post(
        "/api/workflow_runs",
        json={"portfolio_tickers": ["T1.L", "T2.L"], "is_mock": True},
    )
    rows = client.get("/api/workflow_runs").json()
    assert len(rows) == 1
    item = WorkflowRunListItem.model_validate(rows[0])
    _assert_uuid(item.id)
    assert item.status in ("running", "completed", "failed")
    assert item.ticker_run_count == 2
    assert item.completed_ticker_run_count >= 0
    assert item.failed_ticker_run_count >= 0


def test_create_workflow_run_response_matches_contract(client: TestClient) -> None:
    r = client.post(
        "/api/workflow_runs",
        json={"portfolio_tickers": ["A.L", "  B.L  ", ""], "is_mock": True},
    )
    assert r.status_code == 201
    body = CreateWorkflowRunResponse.model_validate(r.json())
    _assert_uuid(body.workflow_run_id)
    assert body.surveyor_started is True
    tickers = {p.ticker for p in body.profiler_runs}
    assert tickers == {"A.L", "B.L"}
    for p in body.profiler_runs:
        _assert_uuid(p.run_id)


def test_workflow_run_detail_matches_contract_after_post(client: TestClient) -> None:
    wf_id = client.post(
        "/api/workflow_runs",
        json={"portfolio_tickers": ["X.L"], "is_mock": True},
    ).json()["workflow_run_id"]
    detail = client.get(f"/api/workflow_runs/{wf_id}").json()
    m = WorkflowRunDetailResponse.model_validate(detail)
    assert m.id == wf_id
    assert m.surveyor_execution is not None
    assert m.surveyor_execution.agent_name == "surveyor"
    assert len(m.runs) == 1
    run0 = m.runs[0]
    assert run0.entry_path == "profiler"
    assert run0.ticker == "X.L"
    for ex in run0.agent_executions:
        _assert_uuid(ex.id)
        assert ex.agent_name in (
            "profiler",
            "researcher",
            "strategist",
            "sentinel",
            "appraiser",
            "arbiter",
        )


def test_workflow_run_detail_seed_profiler_and_surveyor_lanes(
    client: TestClient,
) -> None:
    app = cast(FastAPI, client.app)
    with app.state.db_session_factory() as session:
        seed(session)
    listed = client.get("/api/workflow_runs").json()
    wf_id = listed[0]["id"]
    detail = WorkflowRunDetailResponse.model_validate(
        client.get(f"/api/workflow_runs/{wf_id}").json()
    )
    paths = {r.entry_path for r in detail.runs}
    assert paths == {"profiler", "surveyor"}
    surveyor_lane = next(r for r in detail.runs if r.entry_path == "surveyor")
    assert all(a.agent_name != "profiler" for a in surveyor_lane.agent_executions)
    profiler_lane = next(r for r in detail.runs if r.entry_path == "profiler")
    names = [a.agent_name for a in profiler_lane.agent_executions]
    assert names[0] == "profiler"


def test_list_newest_workflow_first(client: TestClient) -> None:
    first = client.post(
        "/api/workflow_runs",
        json={"portfolio_tickers": ["OLD"], "is_mock": True},
    ).json()["workflow_run_id"]
    time.sleep(0.02)
    second = client.post(
        "/api/workflow_runs",
        json={"portfolio_tickers": ["NEW"], "is_mock": True},
    ).json()["workflow_run_id"]
    rows = client.get("/api/workflow_runs").json()
    assert [r["id"] for r in rows][:2] == [second, first]


def test_get_workflow_run_not_found(client: TestClient) -> None:
    r = client.get("/api/workflow_runs/00000000-0000-4000-8000-000000000001")
    assert r.status_code == 404


def test_delete_workflow_run_not_found(client: TestClient) -> None:
    r = client.delete("/api/workflow_runs/00000000-0000-4000-8000-000000000002")
    assert r.status_code == 404


def test_conversation_endpoints_validate(client: TestClient) -> None:
    app = cast(FastAPI, client.app)
    with app.state.db_session_factory() as session:
        seed(session)
    wf_id = client.get("/api/workflow_runs").json()[0]["id"]
    surv = ConversationResponse.model_validate(
        client.get(
            f"/api/agents/workflow_runs/{wf_id}/agents/surveyor/conversation"
        ).json()
    )
    assert surv.system_prompt
    assert surv.assistant_response

    runs = client.get(f"/api/workflow_runs/{wf_id}").json()["runs"]
    run_id = next(r["id"] for r in runs if r["entry_path"] == "profiler")
    prof = ConversationResponse.model_validate(
        client.get(f"/api/agents/runs/{run_id}/agents/profiler/conversation").json()
    )
    assert prof.messages_json


def test_surveyor_conversation_not_found(client: TestClient) -> None:
    missing = "00000000-0000-4000-8000-000000000003"
    assert (
        client.get(
            f"/api/agents/workflow_runs/{missing}/agents/surveyor/conversation"
        ).status_code
        == 404
    )


def test_run_agent_conversation_not_found(client: TestClient) -> None:
    assert (
        client.get(
            "/api/agents/runs/00000000-0000-4000-8000-000000000004/agents/profiler/conversation"
        ).status_code
        == 404
    )


def test_run_agent_conversation_invalid_agent_name(client: TestClient) -> None:
    assert (
        client.get(
            "/api/agents/runs/00000000-0000-4000-8000-000000000005/agents/not-an-agent/conversation"
        ).status_code
        == 400
    )


def test_portfolio_response_contract(client: TestClient) -> None:
    empty = PortfolioResponse.model_validate(client.get("/api/portfolio").json())
    assert empty.portfolio_tickers == []
    client.post(
        "/api/workflow_runs",
        json={"portfolio_tickers": ["P1", "P2"], "is_mock": True},
    )
    loaded = PortfolioResponse.model_validate(client.get("/api/portfolio").json())
    assert loaded.portfolio_tickers == ["P1", "P2"]
