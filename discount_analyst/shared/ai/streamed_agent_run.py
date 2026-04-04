"""Run a pydantic-ai agent with streaming, retries, and unified timing + outcome."""

from collections.abc import Callable
from dataclasses import dataclass
from time import perf_counter
from typing import Any

from pydantic_ai.agent.abstract import AbstractAgent
from pydantic_ai.messages import ModelMessage
from pydantic_ai.usage import RunUsage, UsageLimits

from discount_analyst.shared.http.rate_limit_client import stream_with_retries


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
    start = perf_counter()
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
