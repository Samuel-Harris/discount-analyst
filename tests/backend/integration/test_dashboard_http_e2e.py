"""HTTP-level dashboard checks: create a mock run and observe completion via the API."""

from __future__ import annotations

from pathlib import Path
from typing import Any, cast
from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from backend.app.main import create_app
from backend.contracts.agent_lane_order import PROFILER_ENTRY_AGENT_NAMES
from backend.observability.logging import configure_dashboard_observability
from backend.settings.config import DashboardSettings
from backend.settings.testing import LOGFIRE_TOKEN_FOR_TESTS


@pytest.mark.asyncio
async def test_post_workflow_run_then_poll_detail_until_completed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ENV", "PROD")
    db_path = tmp_path / "dashboard_http_e2e.sqlite"
    settings = DashboardSettings(
        database_path=db_path, logfire_token=LOGFIRE_TOKEN_FOR_TESTS
    )
    configure_dashboard_observability(settings)
    app = create_app(settings)

    with (
        patch("backend.pipeline.sqlmodel_runner.asyncio.sleep", new=AsyncMock()),
        patch("backend.pipeline.stages.profiler_stage.asyncio.sleep", new=AsyncMock()),
    ):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            created = await client.post(
                "/api/workflow_runs",
                json={"portfolio_tickers": ["M1.L"], "is_mock": True},
            )
            assert created.status_code == 201
            wf_id = created.json()["workflow_run_id"]

            detail: dict[str, Any] = {}
            for _ in range(600):
                response = await client.get(f"/api/workflow_runs/{wf_id}")
                assert response.status_code == 200
                detail = cast(dict[str, Any], response.json())
                if detail["status"] == "completed":
                    break

            assert detail["status"] == "completed"
            surveyor_execution = detail.get("surveyor_execution")
            assert isinstance(surveyor_execution, dict)
            assert surveyor_execution["status"] == "completed"

            profiler_runs = [r for r in detail["runs"] if r["entry_path"] == "profiler"]
            surveyor_runs = [r for r in detail["runs"] if r["entry_path"] == "surveyor"]
            assert len(profiler_runs) == 1
            assert len(surveyor_runs) == 3
            assert len(detail["runs"]) == 4

            names = [a["agent_name"] for a in profiler_runs[0]["agent_executions"]]
            assert names == list(PROFILER_ENTRY_AGENT_NAMES)

            survey_conv = await client.get(
                f"/api/agents/workflow_runs/{wf_id}/agents/surveyor/conversation"
            )
            assert survey_conv.status_code == 200
            assert "assistant_response" in survey_conv.json()

            profiler_run_id = profiler_runs[0]["id"]
            prof_conv = await client.get(
                f"/api/agents/runs/{profiler_run_id}/agents/profiler/conversation"
            )
            assert prof_conv.status_code == 200
            assert "assistant_response" in prof_conv.json()
