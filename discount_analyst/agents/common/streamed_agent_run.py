"""Run a pydantic-ai agent with streaming, retries, and unified timing + outcome."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from time import perf_counter
from typing import Any

import logfire
from pydantic_ai.agent.abstract import AbstractAgent
from pydantic_ai.messages import ModelMessage
from pydantic_ai.usage import RunUsage, UsageLimits

from common.config import Settings, settings as process_settings
from discount_analyst.agents.common.ai_logging import AI_LOGFIRE
from discount_analyst.agents.common.streaming_retries import stream_with_retries
from discount_analyst.agents.common.terminal_run import (
    TerminalRunOptions,
    terminal_run_options,
)
from discount_analyst.integrations.terminal import (
    close_terminal_http,
    delete_terminal_session,
    ensure_terminal_ready,
)


@dataclass(frozen=True, slots=True)
class StreamedAgentRunOutcome[T]:
    """Result of a fully drained streamed agent run (including retry wrapper exit)."""

    output: T
    usage: RunUsage
    all_messages: list[ModelMessage]
    elapsed_s: float


async def run_streamed_agent[T](
    *,
    agent: AbstractAgent[Any, T],
    user_prompt: str,
    usage_limits: UsageLimits,
    stream_debounce_by: float | None = 0.1,
    on_stream_chunk: Callable[[T], None] | None = None,
    terminal: TerminalRunOptions | None = None,
    run_settings: Settings | None = None,
) -> StreamedAgentRunOutcome[T]:
    """Stream to completion under ``stream_with_retries``, then return output and usage.

    ``elapsed_s`` covers the entire ``async with stream_with_retries`` block.

    Pass ``terminal`` to align tool registration (via ``create_agent``) with sandbox
    session binding and orchestrator cleanup. When omitted, options are derived from
    ``run_settings`` or process :mod:`common.config.settings`.
    """
    if agent.name is None:
        raise ValueError("Agent name is required for streamed runs and Logfire tagging")
    agent_tag = agent.name

    cfg = run_settings or process_settings
    terminal_opts = terminal or terminal_run_options(cfg)

    if terminal_opts.enabled:
        await ensure_terminal_ready(service_url=terminal_opts.runtime.service_url)

    start = perf_counter()
    output: T
    usage: RunUsage
    all_messages: list[ModelMessage]
    with logfire.set_baggage(ai_agent=agent_tag, agent_name=agent_tag.lower()):
        with AI_LOGFIRE.with_tags(agent_tag).span(
            "Run AI agent {agent_name}", agent_name=agent_tag
        ):
            try:
                async with stream_with_retries(
                    agent=agent,
                    user_prompt=user_prompt,
                    usage_limits=usage_limits,
                ) as result:
                    async for chunk in result.stream_output(
                        debounce_by=stream_debounce_by
                    ):
                        if on_stream_chunk is not None:
                            on_stream_chunk(chunk)
                    output = await result.get_output()
                    usage = result.usage()
                    all_messages = result.all_messages()
            finally:
                if terminal_opts.enabled:
                    await delete_terminal_session(
                        terminal_opts.runtime.service_url,
                        terminal_opts.require_session_id(),
                    )
                    await close_terminal_http(terminal_opts.session_state)
    elapsed_s = perf_counter() - start
    return StreamedAgentRunOutcome(
        output=output,
        usage=usage,
        all_messages=all_messages,
        elapsed_s=elapsed_s,
    )
