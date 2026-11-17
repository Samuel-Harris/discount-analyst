"""Run a dashboard agent and keep unsuccessful spend when the attempt raises."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from pydantic_ai.agent.abstract import AbstractAgent
from pydantic_ai.usage import UsageLimits

from discount_analyst.adapters.orchestration.attempt_cost import (
    attempt_cost_from_usage,
)
from discount_analyst.adapters.persistence.crud.attempt_costs import (
    insert_attempt_cost_once,
)
from discount_analyst.agents.runtime.streamed_agent_run import (
    StreamedAgentRunOutcome,
    run_streamed_agent,
)
from discount_analyst.agents.runtime.streamed_run_usage import streamed_run_usage
from discount_analyst.agents.runtime.terminal_run import TerminalRunOptions
from discount_analyst.config.logging_constants import AI_LOGFIRE
from discount_analyst.domain.workflow_cost import AttemptCost


async def record_failed_attempt_cost(
    *,
    db: Callable[..., Awaitable[Any]],
    execution_id: str,
    attempt_cost: AttemptCost | None,
) -> None:
    """Store unsuccessful spend. A write failure must not replace the agent error."""
    if attempt_cost is None:
        return
    try:
        await db(
            insert_attempt_cost_once,
            execution_id=execution_id,
            successful=False,
            attempt_cost=attempt_cost,
        )
    except Exception:
        AI_LOGFIRE.exception(
            "Failed to record unsuccessful attempt cost",
            execution_id=execution_id,
        )


async def run_dashboard_agent[T](
    *,
    db: Callable[..., Awaitable[Any]],
    execution_id: str,
    agent: AbstractAgent[Any, T],
    user_prompt: str,
    usage_limits: UsageLimits,
    terminal: TerminalRunOptions,
) -> StreamedAgentRunOutcome[T]:
    """Run one already-built dashboard agent and record spend if the run raises."""
    try:
        return await run_streamed_agent(
            agent=agent,
            user_prompt=user_prompt,
            usage_limits=usage_limits,
            terminal=terminal,
        )
    except BaseException as exc:
        await record_failed_attempt_cost(
            db=db,
            execution_id=execution_id,
            attempt_cost=attempt_cost_from_usage(streamed_run_usage(exc)),
        )
        raise
