import asyncio
import json
from collections.abc import AsyncIterable
from copy import deepcopy
from contextlib import AbstractAsyncContextManager
from typing import Any, AsyncIterator, cast

import httpx
from openai import (
    APIConnectionError,
    APIError,
    APITimeoutError,
    InternalServerError,
    RateLimitError,
)
from pydantic import BaseModel
from pydantic_ai import capture_run_messages
from pydantic_ai.agent.abstract import AbstractAgent
from pydantic_ai.messages import (
    AgentStreamEvent,
    BuiltinToolCallPart,
    ModelMessage,
    ModelRequest,
    ModelResponse,
    PartDeltaEvent,
    PartStartEvent,
    TextPart,
    TextPartDelta,
    ToolCallPart,
    ToolCallPartDelta,
    UserPromptPart,
)
from pydantic_ai.result import StreamedRunResult
from pydantic_ai.usage import RunUsage, UsageLimits

from discount_analyst.http.retrying_client import (
    FALLBACK_MAX_WEIGHT_SECONDS,
    RETRY_WAIT_MULTIPLIER,
)
from discount_analyst.agents.common.ai_logging import AI_LOGFIRE

# Streaming can fail mid-`stream_output()` (e.g. OpenAI TPM) after a successful `run_stream` start.
MAX_STREAM_RETRY_ATTEMPTS = 6


_TPM_RPM_WAIT_SECONDS = 60.0


def _partial_output_retry_prompt(partial_output: str) -> str:
    return (
        "Your previous response was interrupted before it finished. Continue from "
        "the point where it stopped, using the partial draft below as context. "
        "Do not restart or repeat completed material unless it is necessary for "
        "coherence.\n\n"
        "Partial draft from the interrupted response:\n\n"
        f"{partial_output}"
    )


def _openai_error_text(exc: BaseException) -> str:
    if isinstance(exc, APIError):
        msg = getattr(exc, "message", None)
        if msg:
            return str(msg)
    return str(exc)


def api_error_indicates_rate_limit(exc: APIError) -> bool:
    """True when OpenAI signals quota / TPM / RPM limits (not all APIError cases)."""
    text = _openai_error_text(exc).lower()
    return any(
        needle in text
        for needle in (
            "rate limit",
            "tokens per min",
            "requests per min",
            "tpm",
            "rpm",
            "too many requests",
        )
    )


def _is_retryable_single_error(exc: BaseException) -> bool:
    """Check if a single exception (not a group) is retryable."""
    if isinstance(
        exc,
        (
            RateLimitError,
            InternalServerError,
            APITimeoutError,
            APIConnectionError,
            httpx.RemoteProtocolError,
            TimeoutError,  # MCP and other transient timeouts
        ),
    ):
        return True
    if isinstance(exc, APIError):
        return api_error_indicates_rate_limit(exc)
    return False


def should_retry_streaming_error(exc: BaseException) -> bool:
    """Whether to backoff and restart a streamed agent run.

    Handles ExceptionGroups (from anyio TaskGroups) by checking if all
    sub-exceptions are retryable.
    """
    # Handle ExceptionGroup (e.g., from MCP's anyio TaskGroup)
    if isinstance(exc, BaseExceptionGroup):
        # Retry if all sub-exceptions are retryable transient errors
        sub_exceptions = cast(tuple[BaseException, ...], exc.exceptions)
        return all(_is_retryable_single_error(e) for e in sub_exceptions)
    return _is_retryable_single_error(exc)


def _is_tool_startup_timeout(exc: BaseException) -> bool:
    """True for MCP/tool startup timeouts that occur before model progress."""
    if type(exc) is TimeoutError:
        return True
    if isinstance(exc, BaseExceptionGroup):
        sub_exceptions = cast(tuple[BaseException, ...], exc.exceptions)
        return all(_is_tool_startup_timeout(e) for e in sub_exceptions)
    return False


def _stream_wait(attempt: int) -> float:
    """Wait time for streaming retries (exponential backoff, capped)."""
    return min(
        RETRY_WAIT_MULTIPLIER * (2**attempt),
        FALLBACK_MAX_WEIGHT_SECONDS,
    )


def _is_tpm_or_rpm_error(text: str) -> bool:
    """Check if the error indicates a TPM or RPM rate limit."""
    text_lower = text.lower()
    return any(
        indicator in text_lower
        for indicator in ("tokens per min", "tpm", "requests per min", "rpm")
    )


def streaming_retry_sleep_seconds(exc: BaseException, attempt: int) -> float:
    """Sleep before retry; wait 60s for TPM/RPM limits to let the window clear."""
    text = _openai_error_text(exc)

    # TPM/RPM limits need a full window to clear — OpenAI's suggested wait is
    # too short because it assumes no other requests are consuming quota.
    if _is_tpm_or_rpm_error(text):
        return _TPM_RPM_WAIT_SECONDS

    # For other transient errors, use exponential backoff.
    return min(_stream_wait(attempt), FALLBACK_MAX_WEIGHT_SECONDS)


def _stringify_partial_output(output: Any) -> str | None:
    if output is None:
        return None
    if isinstance(output, str):
        text = output
    elif isinstance(output, BaseModel):
        text = output.model_dump_json(indent=2)
    else:
        text = json.dumps(output, default=str, indent=2)
    text = text.strip()
    return text or None


def _tool_args_as_text(part: ToolCallPart | BuiltinToolCallPart) -> str | None:
    if not part.has_content():
        return None
    return part.args_as_json_str()


def _model_response_partial_output(response: ModelResponse) -> str | None:
    parts: list[str] = []
    for part in response.parts:
        if isinstance(part, TextPart) and part.content.strip():
            parts.append(part.content.strip())
        elif isinstance(part, ToolCallPart | BuiltinToolCallPart):
            if args := _tool_args_as_text(part):
                parts.append(args)
    text = "\n\n".join(parts).strip()
    return text or None


def _event_partial_output(event: AgentStreamEvent) -> str | None:
    if isinstance(event, PartStartEvent):
        part = event.part
        if isinstance(part, TextPart):
            return part.content
        if isinstance(part, ToolCallPart | BuiltinToolCallPart):
            return _tool_args_as_text(part)
    if isinstance(event, PartDeltaEvent):
        delta = event.delta
        if isinstance(delta, TextPartDelta):
            return delta.content_delta
        if isinstance(delta, ToolCallPartDelta):
            if isinstance(delta.args_delta, str):
                return delta.args_delta
            if isinstance(delta.args_delta, dict):
                return json.dumps(delta.args_delta, default=str)
    return None


class StreamWithRetriesContext[T]:
    """Own stream attempts and reopen safely on retryable interruptions."""

    def __init__(
        self,
        *,
        agent: AbstractAgent[Any, T],
        user_prompt: str,
        usage_limits: UsageLimits,
    ) -> None:
        self._agent = agent
        self._user_prompt = user_prompt
        self._usage_limits = usage_limits

        self._next_message_history: list[ModelMessage] | None = None
        self._next_usage: RunUsage | None = None

        self._run_stream_context_manager: (
            AbstractAsyncContextManager[StreamedRunResult[Any, T]] | None
        ) = None
        self._active_streamed_result: StreamedRunResult[Any, T] | None = None
        self._partial_output_snapshot: str | None = None
        self._attempt_index = 0

        self._result = StreamedResultWrapper(self)

    async def __aenter__(self) -> "StreamedResultWrapper[T]":
        await self._open_attempt_with_retries()
        return self._result

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: Any,
    ) -> None:
        await self._close_active_attempt(exc_type, exc, traceback)

    @property
    def active_streamed_result(self) -> StreamedRunResult[Any, T]:
        if self._active_streamed_result is None:
            raise RuntimeError("No active stream attempt is open.")
        return self._active_streamed_result

    async def reopen_after_stream_interrupt(self, exc: BaseException) -> None:
        """Handle a stream error, optionally reopening a fresh attempt."""
        if not should_retry_streaming_error(exc) or self._attempt_index >= (
            MAX_STREAM_RETRY_ATTEMPTS - 1
        ):
            await self._close_active_attempt(type(exc), exc, exc.__traceback__)
            raise exc

        self.capture_partial_output_from_active_result()
        if not self._checkpoint_active_attempt():
            await self._close_active_attempt(type(exc), exc, exc.__traceback__)
            self._raise_unresumable_open_failure(exc)
        self._append_partial_output_retry_message()

        await self._close_active_attempt(type(exc), exc, exc.__traceback__)
        wait = streaming_retry_sleep_seconds(exc, self._attempt_index)
        AI_LOGFIRE.info(
            "Agent stream interrupted, retrying",
            attempt=self._attempt_index + 1,
            max_attempts=MAX_STREAM_RETRY_ATTEMPTS,
            wait_s=wait,
            error=str(exc),
        )
        await asyncio.sleep(wait)
        self._attempt_index += 1
        await self._open_attempt_with_retries()

    async def _open_attempt_with_retries(self) -> None:
        while True:
            with capture_run_messages() as captured_messages:
                context_manager = self._agent.run_stream(
                    self._next_user_prompt(),
                    message_history=self._next_message_history,
                    usage_limits=self._usage_limits,
                    usage=self._next_usage,
                    event_stream_handler=self._capture_open_stream_events,
                )
                try:
                    result = await context_manager.__aenter__()
                except BaseException as exc:
                    self._checkpoint_captured_messages(captured_messages)
                    if not should_retry_streaming_error(exc) or self._attempt_index >= (
                        MAX_STREAM_RETRY_ATTEMPTS - 1
                    ):
                        raise
                    if self._next_message_history is None:
                        if not _is_tool_startup_timeout(exc):
                            self._raise_unresumable_open_failure(exc)
                        AI_LOGFIRE.info(
                            "Agent tool startup failed before stream progress, retrying",
                            attempt=self._attempt_index + 1,
                            max_attempts=MAX_STREAM_RETRY_ATTEMPTS,
                            error=str(exc),
                        )
                    self._append_partial_output_retry_message()
                    wait = streaming_retry_sleep_seconds(exc, self._attempt_index)
                    AI_LOGFIRE.info(
                        "Agent stream start failed, retrying",
                        attempt=self._attempt_index + 1,
                        max_attempts=MAX_STREAM_RETRY_ATTEMPTS,
                        wait_s=wait,
                        error=str(exc),
                    )
                    await asyncio.sleep(wait)
                    self._attempt_index += 1
                    continue

            self._run_stream_context_manager = context_manager
            self._active_streamed_result = result
            self._partial_output_snapshot = None
            return

    def _next_user_prompt(self) -> str | None:
        if self._next_message_history is None:
            return self._user_prompt
        return None

    def _checkpoint_active_attempt(self) -> bool:
        active_result = self._active_streamed_result
        if active_result is None:
            return False
        self._next_message_history = deepcopy(active_result.all_messages())
        self._next_usage = deepcopy(active_result.usage())
        return True

    def _checkpoint_captured_messages(self, messages: list[ModelMessage]) -> bool:
        if not messages:
            return False
        self._next_message_history = deepcopy(messages)
        return True

    def record_partial_output(self, output: Any) -> None:
        if text := _stringify_partial_output(output):
            self._partial_output_snapshot = text

    def capture_partial_output_from_active_result(self) -> None:
        active_result = self._active_streamed_result
        if active_result is None:
            return
        try:
            response = active_result.response
        except Exception:
            return
        if text := _model_response_partial_output(response):
            self._partial_output_snapshot = text

    async def _capture_open_stream_events(
        self,
        run_context: Any,
        events: AsyncIterable[AgentStreamEvent],
    ) -> None:
        del run_context
        partial_parts: dict[int, str] = {}
        async for event in events:
            if text := _event_partial_output(event):
                if isinstance(event, PartStartEvent):
                    partial_parts[event.index] = text
                elif isinstance(event, PartDeltaEvent):
                    partial_parts[event.index] = (
                        partial_parts.get(event.index, "") + text
                    )
                self._partial_output_snapshot = "\n\n".join(
                    part for _, part in sorted(partial_parts.items()) if part.strip()
                )

    def _append_partial_output_retry_message(self) -> bool:
        partial_output = self._partial_output_snapshot
        if self._next_message_history is None or partial_output is None:
            return False
        self._next_message_history.append(
            ModelRequest(
                parts=[UserPromptPart(_partial_output_retry_prompt(partial_output))]
            )
        )
        self._partial_output_snapshot = None
        return True

    def _raise_unresumable_open_failure(self, exc: BaseException) -> None:
        AI_LOGFIRE.info(
            "Agent stream start failed without resumable message history",
            attempt=self._attempt_index + 1,
            max_attempts=MAX_STREAM_RETRY_ATTEMPTS,
            error=str(exc),
        )
        exc.add_note(
            "Stream retry was not attempted because no message-history checkpoint "
            "was available; the original prompt was not replayed."
        )
        raise exc

    async def _close_active_attempt(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: Any,
    ) -> None:
        context_manager = self._run_stream_context_manager
        if context_manager is None:
            return
        try:
            await context_manager.__aexit__(exc_type, exc, traceback)
        finally:
            self._run_stream_context_manager = None
            self._active_streamed_result = None


class StreamedResultWrapper[T]:
    """Retry-aware facade that delegates to the active streamed result."""

    def __init__(self, retries_context: StreamWithRetriesContext[T]) -> None:
        self._retries_context = retries_context

    @property
    def _active_result(self) -> StreamedRunResult[Any, T]:
        return self._retries_context.active_streamed_result

    async def stream_output(
        self, *, debounce_by: float | None = 0.1
    ) -> AsyncIterator[T]:
        for _ in range(MAX_STREAM_RETRY_ATTEMPTS):
            try:
                async for output in self._active_result.stream_output(
                    debounce_by=debounce_by
                ):
                    self._retries_context.record_partial_output(output)
                    yield output
            except BaseException as exc:
                await self._retries_context.reopen_after_stream_interrupt(exc)
                continue
            return
        raise RuntimeError("Stream retries exhausted without terminal result")

    async def get_output(self) -> T:
        for _ in range(MAX_STREAM_RETRY_ATTEMPTS):
            try:
                return await self._active_result.get_output()
            except BaseException as exc:
                self._retries_context.capture_partial_output_from_active_result()
                await self._retries_context.reopen_after_stream_interrupt(exc)
        raise RuntimeError("Output retries exhausted without terminal result")

    def usage(self) -> RunUsage:
        return self._active_result.usage()

    def all_messages(
        self, *, output_tool_return_content: str | None = None
    ) -> list[ModelMessage]:
        return self._active_result.all_messages(
            output_tool_return_content=output_tool_return_content
        )


def stream_with_retries[T](
    *,
    agent: AbstractAgent[Any, T],
    user_prompt: str,
    usage_limits: UsageLimits,
) -> StreamWithRetriesContext[T]:
    """Stream agent output with retries on transient API errors.

    Tenacity's @retry does not work with async generators: exceptions can occur
    during stream iteration (e.g. ``stream_output()``), not only entering
    ``run_stream``. This context manager keeps attempt lifecycle state so
    retryable interruptions can reopen safely with resumed message history/usage.
    """
    return StreamWithRetriesContext(
        agent=agent,
        user_prompt=user_prompt,
        usage_limits=usage_limits,
    )
