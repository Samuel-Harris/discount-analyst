"""Run a pydantic-ai agent with streaming, retries, and unified timing + outcome."""

from collections.abc import Callable
from dataclasses import dataclass
from time import perf_counter
from typing import Any

import logfire
from pydantic_ai.agent.abstract import AbstractAgent
from pydantic_ai.messages import ModelMessage
from pydantic_ai.usage import RunUsage, UsageLimits

from discount_analyst.agents.common.ai_logging import AI_LOGFIRE
from discount_analyst.agents.common.streaming_retries import stream_with_retries


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
) -> StreamedAgentRunOutcome[T]:
    """Stream to completion under ``stream_with_retries``, then return output and usage.

    ``elapsed_s`` covers the entire ``async with stream_with_retries`` block.
    """
    if agent.name is None:
        raise ValueError("Agent name is required for streamed runs and Logfire tagging")
    agent_tag = agent.name

    start = perf_counter()
    # Use baggage to propagate attributes to all child spans (including pydantic-ai
    # instrumentation spans). Baggage values become span attributes automatically.
    # The outer span uses AI_LOGFIRE.with_tags() for proper logfire.tags filtering;
    # child spans get the baggage attributes for custom filtering.
    # Note: agent_tag is typically uppercase (e.g. "SURVEYOR"); we lowercase for agent_name
    # to match the AgentNameDb enum values used in the database and logs.
    with logfire.set_baggage(ai_agent=agent_tag, agent_name=agent_tag.lower()):
        with AI_LOGFIRE.with_tags(agent_tag).span(
            "Run AI agent {agent_name}", agent_name=agent_tag
        ):
            async with stream_with_retries(
                agent=agent,
                user_prompt=user_prompt,
                usage_limits=usage_limits,
            ) as result:
                async for chunk in result.stream_output(debounce_by=stream_debounce_by):
                    if on_stream_chunk is not None:
                        on_stream_chunk(chunk)
                output = await result.get_output()
                usage = result.usage()
                all_messages = result.all_messages()
    elapsed_s = perf_counter() - start
    return StreamedAgentRunOutcome(
        output=output,
        usage=usage,
        all_messages=all_messages,
        elapsed_s=elapsed_s,
    )
