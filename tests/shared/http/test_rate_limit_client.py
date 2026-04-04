"""Unit tests for streaming retry helpers."""

import asyncio
from collections.abc import Iterator
from typing import Any, cast
from unittest.mock import patch

import pytest
from openai import APIError
from pydantic_ai.messages import ModelRequest, ModelResponse, TextPart
from pydantic_ai.usage import RunUsage, UsageLimits

from discount_analyst.shared.http import rate_limit_client as rlc
from discount_analyst.shared.http.rate_limit_client import (
    api_error_indicates_rate_limit,
    should_retry_streaming_error,
    stream_with_retries,
    streaming_retry_sleep_seconds,
)


def _api_error(message: str) -> APIError:
    """Minimal ``APIError`` for unit tests (SDK types ``request`` as non-optional)."""
    return APIError(message, request=cast(Any, None), body=None)


def test_api_error_indicates_rate_limit_tpm_message() -> None:
    exc = _api_error(
        "Rate limit reached for gpt-5.1 on tokens per min (TPM): "
        "Please try again in 9.749s.",
    )
    assert api_error_indicates_rate_limit(exc) is True


def test_api_error_indicates_rate_limit_negative() -> None:
    exc = _api_error("Invalid API key")
    assert api_error_indicates_rate_limit(exc) is False


def test_should_retry_streaming_error_rate_limit_message() -> None:
    exc = _api_error("429 Too many requests — rate limit exceeded")
    assert should_retry_streaming_error(exc) is True


def test_streaming_retry_sleep_parses_try_again_hint() -> None:
    exc = _api_error("Rate limit reached. Please try again in 12.5s.")
    assert streaming_retry_sleep_seconds(exc, attempt=0) == 13.5


def test_streaming_retry_sleep_fallback_exponential() -> None:
    exc = _api_error("Invalid API key")
    assert streaming_retry_sleep_seconds(exc, attempt=0) == 10.0


class _FakeStreamResult:
    """Minimal stand-in for ``StreamedRunResult``."""

    def __init__(
        self,
        messages: list[Any],
        usage: RunUsage,
        response: ModelResponse,
        *,
        is_complete: bool = False,
        raise_from_stream: BaseException | None = None,
        stream_payload: str = "ok",
    ) -> None:
        self._messages = messages
        self._usage = usage
        self._response = response
        self.is_complete = is_complete
        self._raise_from_stream = raise_from_stream
        self._stream_payload = stream_payload

    def all_messages(self, **kwargs: Any) -> list[Any]:
        return list(self._messages)

    def usage(self) -> RunUsage:
        return self._usage

    @property
    def response(self) -> ModelResponse:
        return self._response

    async def stream_output(self, **kwargs: Any):
        if self._raise_from_stream is not None:
            raise self._raise_from_stream
        yield self._stream_payload

    async def get_output(self) -> str:
        return self._stream_payload


class _RecordingFakeAgent:
    """Yields async context managers from a queue; records ``run_stream`` kwargs."""

    def __init__(self, contexts: Iterator[Any]) -> None:
        self.calls: list[dict[str, Any]] = []
        self._contexts = contexts

    def run_stream(
        self,
        user_prompt: str | None = None,
        *,
        message_history: list[Any] | None = None,
        usage_limits: Any = None,
        usage: RunUsage | None = None,
        **kwargs: Any,
    ) -> Any:
        self.calls.append(
            {
                "user_prompt": user_prompt,
                "message_history": message_history,
                "usage_limits": usage_limits,
                "usage": usage,
            }
        )
        return next(self._contexts)


class _FakeRunStreamCM:
    """Async CM mimicking ``agent.run_stream()`` for tests."""

    def __init__(self, result: Any, *, enter_exc: BaseException | None = None) -> None:
        self._result = result
        self._enter_exc = enter_exc

    async def __aenter__(self) -> Any:
        if self._enter_exc is not None:
            raise self._enter_exc
        return self._result

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: Any,
    ) -> None:
        return None


async def _noop_sleep(_seconds: float) -> None:
    return None


@pytest.fixture
def no_stream_sleep() -> Any:
    with patch.object(rlc.asyncio, "sleep", new=_noop_sleep):
        yield


def test_stream_with_retries_second_attempt_passes_history_and_usage(
    no_stream_sleep: None,
) -> None:
    completed = ModelRequest.user_text_prompt("hello")
    u1 = RunUsage(requests=1, input_tokens=10, output_tokens=3)
    partial_response = ModelResponse(parts=[TextPart(content="PARTIAL_ASSISTANT_ONLY")])
    stream_err = _api_error("Rate limit reached. Please try again in 1s.")
    r1 = _FakeStreamResult(
        [completed],
        u1,
        partial_response,
        is_complete=False,
        raise_from_stream=stream_err,
    )
    r2 = _FakeStreamResult([completed], RunUsage(), ModelResponse(parts=[]))
    agent = _RecordingFakeAgent(iter([_FakeRunStreamCM(r1), _FakeRunStreamCM(r2)]))

    async def run() -> None:
        async with stream_with_retries(
            agent=agent,  # type: ignore[arg-type]
            user_prompt="hello",
            usage_limits=UsageLimits(),
        ) as res:
            chunks: list[str] = []
            async for x in res.stream_output():
                chunks.append(x)
            assert chunks == ["ok"]
            assert await res.get_output() == "ok"

    asyncio.run(run())

    assert len(agent.calls) == 2
    assert agent.calls[0]["user_prompt"] == "hello"
    assert agent.calls[0]["message_history"] is None
    assert agent.calls[0]["usage"] is None

    assert agent.calls[1]["user_prompt"] is None
    assert agent.calls[1]["message_history"] is not None
    assert len(agent.calls[1]["message_history"]) == 1
    assert agent.calls[1]["message_history"][0] == completed
    assert agent.calls[1]["usage"] is not None
    assert agent.calls[1]["usage"].requests == u1.requests
    assert agent.calls[1]["usage"].input_tokens == u1.input_tokens
    assert agent.calls[1]["usage"] is not u1


def test_stream_with_retries_history_excludes_partial_response_only(
    no_stream_sleep: None,
) -> None:
    """Regression: ``message_history`` must come from ``all_messages()``, not ``response``."""
    completed = ModelRequest.user_text_prompt("user line")
    rich_partial = ModelResponse(parts=[TextPart(content="ONLY_IN_RESPONSE_PROPERTY")])
    u = RunUsage(requests=1, input_tokens=5, output_tokens=0)
    r1 = _FakeStreamResult(
        [completed],
        u,
        rich_partial,
        is_complete=False,
        raise_from_stream=_api_error("Rate limit reached. Please try again in 1s."),
    )
    r2 = _FakeStreamResult([completed], RunUsage(), ModelResponse(parts=[]))

    agent = _RecordingFakeAgent(iter([_FakeRunStreamCM(r1), _FakeRunStreamCM(r2)]))

    async def run() -> None:
        async with stream_with_retries(
            agent=agent,  # type: ignore[arg-type]
            user_prompt="user line",
            usage_limits=UsageLimits(),
        ) as res:
            async for _ in res.stream_output():
                pass

    asyncio.run(run())

    hist = agent.calls[1]["message_history"]
    assert hist is not None
    assert len(hist) == 1
    assert isinstance(hist[0], ModelRequest)
    assert all(not isinstance(m, ModelResponse) for m in hist)


def test_stream_with_retries_enter_failure_keeps_user_prompt(
    no_stream_sleep: None,
) -> None:
    retryable = _api_error("Rate limit reached. Please try again in 1s.")
    ok = ModelRequest.user_text_prompt("x")
    r2 = _FakeStreamResult([ok], RunUsage(), ModelResponse(parts=[]))

    agent = _RecordingFakeAgent(
        iter(
            [
                _FakeRunStreamCM(None, enter_exc=retryable),
                _FakeRunStreamCM(r2),
            ]
        )
    )

    async def run() -> None:
        async with stream_with_retries(
            agent=agent,  # type: ignore[arg-type]
            user_prompt="x",
            usage_limits=UsageLimits(),
        ) as res:
            async for _ in res.stream_output():
                pass
            assert await res.get_output() == "ok"

    asyncio.run(run())

    assert len(agent.calls) == 2
    assert agent.calls[0]["user_prompt"] == "x"
    assert agent.calls[0]["message_history"] is None
    assert agent.calls[1]["user_prompt"] == "x"
    assert agent.calls[1]["message_history"] is None
