"""Unit tests for the extracted profiler dashboard pipeline stage."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest

from backend.dev import mock_outputs
from backend.pipeline.stages.profiler_stage import ProfilerStage
from backend.settings.config import DashboardSettings


class FakeProfilerPort:
    """In-memory port that records calls for ordering and argument assertions."""

    def __init__(self, *, profiler_exec_id: str | None) -> None:
        self.profiler_exec_id = profiler_exec_id
        self.calls: list[tuple[str, dict[str, Any]]] = []

    def _log(self, name: str, **kwargs: Any) -> None:
        self.calls.append((name, kwargs))

    async def get_agent_execution_id(self, run_id: str, agent_name: str) -> str | None:
        self._log("get_agent_execution_id", run_id=run_id, agent_name=agent_name)
        return self.profiler_exec_id

    async def mark_agent_execution(
        self,
        *,
        execution_id: str,
        status: str,
        output_json: str | None = None,
        started: bool = False,
        completed: bool = False,
        error_message: str | None = None,
    ) -> None:
        self._log(
            "mark_agent_execution",
            execution_id=execution_id,
            status=status,
            output_json=output_json,
            started=started,
            completed=completed,
            error_message=error_message,
        )

    async def recompute_workflow_status(self, workflow_run_id: str) -> None:
        self._log("recompute_workflow_status", workflow_run_id=workflow_run_id)

    async def store_agent_conversation(
        self,
        *,
        run_id: str,
        agent_name: str,
        system_prompt: str,
        messages: list[Any] | None = None,
        messages_json: str | None = None,
    ) -> None:
        self._log(
            "store_agent_conversation",
            run_id=run_id,
            agent_name=agent_name,
            system_prompt=system_prompt,
            messages=messages,
            messages_json=messages_json,
        )

    async def update_ticker_run_company_name(
        self, run_id: str, company_name: str
    ) -> None:
        self._log(
            "update_ticker_run_company_name",
            run_id=run_id,
            company_name=company_name,
        )


@pytest.mark.asyncio
async def test_profiler_stage_mock_path_records_expected_port_sequence() -> None:
    port = FakeProfilerPort(profiler_exec_id="exec-profiler")
    settings = DashboardSettings()
    stage = ProfilerStage()
    with patch("backend.pipeline.stages.profiler_stage.asyncio.sleep", new=AsyncMock()):
        candidate = await stage.run(
            port,
            settings,
            workflow_run_id="wf-1",
            run_id="run-1",
            ticker="M1.L",
            is_mock=True,
        )
    assert candidate.ticker == "M1.L"
    names = [c[0] for c in port.calls]
    assert names == [
        "get_agent_execution_id",
        "mark_agent_execution",
        "recompute_workflow_status",
        "mark_agent_execution",
        "store_agent_conversation",
        "update_ticker_run_company_name",
    ]
    assert port.calls[1][1]["status"] == "running"
    assert port.calls[1][1]["started"] is True
    assert port.calls[3][1]["status"] == "completed"
    assert port.calls[3][1]["completed"] is True
    assert port.calls[3][1]["output_json"] is not None
    assert port.calls[4][1]["agent_name"] == "profiler"
    assert port.calls[4][1]["messages_json"] is not None


@pytest.mark.asyncio
async def test_profiler_stage_raises_when_profiler_execution_missing() -> None:
    port = FakeProfilerPort(profiler_exec_id=None)
    settings = DashboardSettings()
    with pytest.raises(RuntimeError, match="Missing profiler execution"):
        await ProfilerStage().run(
            port,
            settings,
            workflow_run_id="wf-1",
            run_id="run-1",
            ticker="M1.L",
            is_mock=True,
        )


@pytest.mark.asyncio
async def test_profiler_stage_non_mock_path_uses_streamed_agent() -> None:
    port = FakeProfilerPort(profiler_exec_id="exec-p")
    settings = DashboardSettings()
    profiler_output = mock_outputs.mock_profiler_output(ticker="X.L")
    fake_outcome = SimpleNamespace(output=profiler_output, all_messages=[object()])
    with (
        patch(
            "backend.pipeline.stages.profiler_stage.run_streamed_agent",
            new=AsyncMock(return_value=fake_outcome),
        ),
        patch(
            "backend.pipeline.stages.profiler_stage.create_profiler_agent",
            return_value="fake-agent",
        ),
    ):
        candidate = await ProfilerStage().run(
            port,
            settings,
            workflow_run_id="wf-2",
            run_id="run-2",
            ticker="X.L",
            is_mock=False,
        )
    assert candidate.ticker == "X.L"
    assert port.calls[4][1]["messages"] == fake_outcome.all_messages
