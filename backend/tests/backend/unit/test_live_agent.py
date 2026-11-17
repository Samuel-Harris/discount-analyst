"""Unsuccessful attempt cost stays attached to the agent error."""

from __future__ import annotations

from decimal import Decimal
from typing import Any, cast

import pytest
from pydantic_ai.agent.abstract import AbstractAgent
from pydantic_ai.usage import RunUsage, UsageLimits

from discount_analyst.adapters.orchestration.live_agent import run_dashboard_agent
from discount_analyst.adapters.persistence.crud.attempt_costs import (
    insert_attempt_cost_once,
)
from discount_analyst.agents.runtime.streamed_agent_run import StreamedAgentRunOutcome
from discount_analyst.agents.runtime.streamed_run_usage import attach_streamed_run_usage
from discount_analyst.agents.runtime.terminal_run import execution_terminal_options
from discount_analyst.config.testing_settings import dashboard_settings_for_tests
from discount_analyst.domain.workflow_cost import AttemptCost


def _run_kwargs() -> dict[str, Any]:
    settings = dashboard_settings_for_tests()
    return {
        "execution_id": "exec-1",
        "agent": cast(AbstractAgent[Any, str], object()),
        "user_prompt": "prompt",
        "usage_limits": UsageLimits(),
        "terminal": execution_terminal_options(
            settings,
            execution_id="exec-1",
            enabled=False,
        ),
    }


@pytest.mark.asyncio
async def test_cost_insert_error_keeps_the_agent_exception(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def ignore_log(*args: object, **kwargs: object) -> None:
        del args, kwargs

    monkeypatch.setattr(
        "discount_analyst.adapters.orchestration.live_agent.AI_LOGFIRE.exception",
        ignore_log,
    )

    async def fail_db(fn: Any, *args: Any, **kwargs: Any) -> None:
        del fn, args, kwargs
        raise RuntimeError("db down")

    async def raise_priced(**kwargs: object) -> None:
        del kwargs
        exc = ValueError("model failed")
        attach_streamed_run_usage(exc, RunUsage(requests=1, cost=Decimal("1.25")))
        raise exc

    monkeypatch.setattr(
        "discount_analyst.adapters.orchestration.live_agent.run_streamed_agent",
        raise_priced,
    )

    with pytest.raises(ValueError, match="model failed"):
        await run_dashboard_agent(db=fail_db, **_run_kwargs())


@pytest.mark.asyncio
async def test_failed_run_records_the_attached_cost(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    recorded: list[tuple[Any, dict[str, Any]]] = []

    async def record_db(fn: Any, *args: Any, **kwargs: Any) -> None:
        del args
        recorded.append((fn, kwargs))

    async def raise_priced(**kwargs: object) -> None:
        del kwargs
        exc = ValueError("model failed")
        attach_streamed_run_usage(exc, RunUsage(requests=1, cost=Decimal("1.25")))
        raise exc

    monkeypatch.setattr(
        "discount_analyst.adapters.orchestration.live_agent.run_streamed_agent",
        raise_priced,
    )

    with pytest.raises(ValueError, match="model failed"):
        await run_dashboard_agent(db=record_db, **_run_kwargs())

    assert recorded == [
        (
            insert_attempt_cost_once,
            {
                "execution_id": "exec-1",
                "successful": False,
                "attempt_cost": AttemptCost(cost_usd=Decimal("1.25")),
            },
        )
    ]


@pytest.mark.asyncio
async def test_unpriced_failure_does_not_write_a_cost(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fail_if_called(fn: Any, *args: Any, **kwargs: Any) -> None:
        del fn, args, kwargs
        raise AssertionError("unpriced failure must not write a cost")

    async def raise_unpriced(**kwargs: object) -> None:
        del kwargs
        exc = ValueError("model failed")
        attach_streamed_run_usage(exc, RunUsage(requests=0, cost=Decimal("9")))
        raise exc

    monkeypatch.setattr(
        "discount_analyst.adapters.orchestration.live_agent.run_streamed_agent",
        raise_unpriced,
    )

    with pytest.raises(ValueError, match="model failed"):
        await run_dashboard_agent(db=fail_if_called, **_run_kwargs())


@pytest.mark.asyncio
async def test_successful_run_returns_the_outcome(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    outcome: StreamedAgentRunOutcome[str] = StreamedAgentRunOutcome(
        output="ok",
        usage=RunUsage(requests=1, cost=Decimal("1.25")),
        all_messages=[],
        elapsed_s=0.1,
    )
    seen: dict[str, Any] = {}

    async def succeed(**kwargs: Any) -> StreamedAgentRunOutcome[str]:
        seen.update(kwargs)
        return outcome

    async def fail_if_called(fn: Any, *args: Any, **kwargs: Any) -> None:
        del fn, args, kwargs
        raise AssertionError("a successful run must not record a failed cost")

    monkeypatch.setattr(
        "discount_analyst.adapters.orchestration.live_agent.run_streamed_agent",
        succeed,
    )
    kwargs = _run_kwargs()

    assert await run_dashboard_agent(db=fail_if_called, **kwargs) is outcome
    assert seen["agent"] is kwargs["agent"]
    assert seen["user_prompt"] == "prompt"
    assert seen["usage_limits"] is kwargs["usage_limits"]
    assert seen["terminal"] is kwargs["terminal"]
