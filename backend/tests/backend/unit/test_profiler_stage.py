"""Unit tests for the extracted profiler dashboard pipeline stage."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest

from discount_analyst.adapters.simulation import mock_outputs
from discount_analyst.adapters.orchestration.stages.profiler_stage import ProfilerStage
from discount_analyst.config.testing_settings import dashboard_settings_for_tests
from discount_analyst.config.settings import Settings


class FakeProfilerHost:
    """In-memory host that records calls for ordering and argument assertions."""

    def __init__(self, *, profiler_exec_id: str | None, settings: Settings) -> None:
        self._settings = settings
        self.profiler_exec_id = profiler_exec_id
        self.calls: list[tuple[str, dict[str, Any]]] = []

    @property
    def settings(self) -> Settings:
        return self._settings

    def _log(self, name: str, **kwargs: Any) -> None:
        self.calls.append((name, kwargs))

    async def get_exec_id(self, run_id: str, agent_name: str) -> str | None:
        self._log("get_exec_id", run_id=run_id, agent_name=agent_name)
        return self.profiler_exec_id

    async def mark_exec(
        self,
        *,
        execution_id: str,
        status: str,
        output_json: str | None = None,
        started: bool = False,
        completed: bool = False,
        error_message: str | None = None,
        model_name: object = None,
    ) -> None:
        self._log(
            "mark_exec",
            execution_id=execution_id,
            status=status,
            output_json=output_json,
            started=started,
            completed=completed,
            error_message=error_message,
            model_name=model_name,
        )

    async def recompute(self, workflow_run_id: str) -> None:
        self._log("recompute", workflow_run_id=workflow_run_id)

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
    settings = dashboard_settings_for_tests()
    host = FakeProfilerHost(profiler_exec_id="exec-profiler", settings=settings)
    stage = ProfilerStage()
    with patch(
        "discount_analyst.adapters.orchestration.stages.profiler_stage.asyncio.sleep",
        new=AsyncMock(),
    ):
        candidate = await stage.run(
            host,
            workflow_run_id="wf-1",
            run_id="run-1",
            ticker="M1.L",
            is_mock=True,
        )
    assert candidate.ticker == "M1.L"
    names = [c[0] for c in host.calls]
    assert names == [
        "get_exec_id",
        "mark_exec",
        "recompute",
        "mark_exec",
        "store_agent_conversation",
        "update_ticker_run_company_name",
    ]
    assert host.calls[1][1]["status"] == "running"
    assert host.calls[1][1]["started"] is True
    assert host.calls[1][1]["model_name"] is None
    assert host.calls[3][1]["status"] == "completed"
    assert host.calls[3][1]["completed"] is True
    assert host.calls[3][1]["output_json"] is not None
    assert host.calls[4][1]["agent_name"] == "profiler"
    assert host.calls[4][1]["messages_json"] is not None


@pytest.mark.asyncio
async def test_profiler_stage_raises_when_profiler_execution_missing() -> None:
    settings = dashboard_settings_for_tests()
    host = FakeProfilerHost(profiler_exec_id=None, settings=settings)
    with pytest.raises(RuntimeError, match="Missing profiler execution"):
        await ProfilerStage().run(
            host,
            workflow_run_id="wf-1",
            run_id="run-1",
            ticker="M1.L",
            is_mock=True,
        )


@pytest.mark.asyncio
async def test_profiler_stage_non_mock_path_uses_run_agent_with_terminal() -> None:
    settings = dashboard_settings_for_tests()
    host = FakeProfilerHost(profiler_exec_id="exec-p", settings=settings)
    profiler_output = mock_outputs.mock_profiler_output(ticker="X.L")
    fake_outcome = SimpleNamespace(output=profiler_output, all_messages=[object()])
    with patch(
        "discount_analyst.adapters.orchestration.stages.profiler_stage.run_agent_with_terminal",
        new=AsyncMock(return_value=fake_outcome),
    ):
        candidate = await ProfilerStage().run(
            host,
            workflow_run_id="wf-2",
            run_id="run-2",
            ticker="X.L",
            is_mock=False,
        )
    assert candidate.ticker == "X.L"
    assert host.calls[1][1]["model_name"] == settings.default_model
    assert host.calls[4][1]["messages"] == fake_outcome.all_messages
