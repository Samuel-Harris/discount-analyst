"""Unsuccessful attempt cost stays attached to the agent error."""

from __future__ import annotations

from typing import Any

import pytest
from pydantic_ai.usage import RunUsage

from discount_analyst.adapters.orchestration.live_agent import run_and_record_failure
from discount_analyst.agents.runtime.streamed_run_usage import attach_streamed_run_usage


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

    async def start() -> None:
        exc = ValueError("model failed")
        attach_streamed_run_usage(exc, RunUsage(requests=1))
        raise exc

    with pytest.raises(ValueError, match="model failed"):
        await run_and_record_failure(db=fail_db, execution_id="exec-1", start=start)
