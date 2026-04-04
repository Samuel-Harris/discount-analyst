"""Unit tests for streaming retry helpers."""

from collections.abc import Callable
from typing import Any, cast

import pytest
from openai import APIError
from pydantic_ai.usage import RunUsage, UsageLimits

from discount_analyst.shared.http import rate_limit_client
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


class _FakeStreamedRunResult:
    def __init__(
        self,
        *,
        outputs: list[str],
        final_output: str,
        messages: list[Any],
        usage: RunUsage,
        stream_error: BaseException | None = None,
        get_output_error: BaseException | None = None,
    ) -> None:
        self._outputs = outputs
        self._final_output = final_output
        self._messages = messages
        self._usage = usage
        self._stream_error = stream_error
        self._get_output_error = get_output_error

    async def stream_output(self, *, debounce_by: float | None = 0.1):
        del debounce_by
        for chunk in self._outputs:
            yield chunk
        if self._stream_error is not None:
            raise self._stream_error

    async def get_output(self) -> str:
        if self._get_output_error is not None:
            raise self._get_output_error
        return self._final_output

    def usage(self) -> RunUsage:
        return self._usage

    def all_messages(
        self, *, output_tool_return_content: str | None = None
    ) -> list[Any]:
        if output_tool_return_content is not None:
            raise NotImplementedError
        return self._messages


class _FakeRunStreamContextManager:
    def __init__(
        self,
        *,
        result: _FakeStreamedRunResult | None = None,
        enter_error: BaseException | None = None,
        on_exit: Callable[[], None] | None = None,
    ) -> None:
        self._result = result
        self._enter_error = enter_error
        self._on_exit = on_exit
        self.exit_calls: list[
            tuple[type[BaseException] | None, BaseException | None]
        ] = []

    async def __aenter__(self) -> _FakeStreamedRunResult:
        if self._enter_error is not None:
            raise self._enter_error
        if self._result is None:
            raise AssertionError("Fake context manager missing result")
        return self._result

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: Any,
    ) -> bool:
        del traceback
        self.exit_calls.append((exc_type, exc))
        if self._on_exit is not None:
            self._on_exit()
        return False


class _FakeAgent:
    def __init__(self, context_managers: list[_FakeRunStreamContextManager]) -> None:
        self._context_managers = context_managers
        self.calls: list[dict[str, Any]] = []

    def run_stream(
        self,
        user_prompt: str | None,
        *,
        message_history: list[Any] | None = None,
        usage_limits: UsageLimits | None = None,
        usage: RunUsage | None = None,
    ) -> _FakeRunStreamContextManager:
        call_index = len(self.calls)
        if call_index >= len(self._context_managers):
            raise AssertionError("Unexpected run_stream call")
        self.calls.append(
            {
                "user_prompt": user_prompt,
                "message_history": message_history,
                "usage_limits": usage_limits,
                "usage": usage,
            }
        )
        return self._context_managers[call_index]


@pytest.mark.anyio
async def test_stream_with_retries_resumes_with_copied_history_and_usage(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def _no_wait(exc: BaseException, attempt: int) -> float:
        del exc, attempt
        return 0.0

    monkeypatch.setattr(
        rate_limit_client,
        "streaming_retry_sleep_seconds",
        _no_wait,
    )

    first_messages = [{"turn": {"text": "first-attempt"}}]
    first_usage = RunUsage(input_tokens=11, output_tokens=7, details={"cached": 1})

    first_result = _FakeStreamedRunResult(
        outputs=["partial"],
        final_output="unused",
        messages=first_messages,
        usage=first_usage,
        stream_error=_api_error("Rate limit reached, please try again in 0.1s."),
    )

    def mutate_first_attempt_state() -> None:
        first_messages[0]["turn"]["text"] = "mutated-after-close"
        first_usage.details["cached"] = 999

    first_cm = _FakeRunStreamContextManager(
        result=first_result,
        on_exit=mutate_first_attempt_state,
    )
    second_usage = RunUsage(input_tokens=22, output_tokens=13)
    second_result = _FakeStreamedRunResult(
        outputs=["final"],
        final_output="done",
        messages=[{"turn": {"text": "second-attempt"}}],
        usage=second_usage,
    )
    second_cm = _FakeRunStreamContextManager(result=second_result)
    agent_impl = _FakeAgent([first_cm, second_cm])

    usage_limits = UsageLimits(request_limit=5)
    outputs: list[str] = []
    async with stream_with_retries(
        agent=cast(Any, agent_impl),
        user_prompt="hello",
        usage_limits=usage_limits,
    ) as result:
        async for chunk in result.stream_output(debounce_by=None):
            outputs.append(chunk)
        output = await result.get_output()
        usage = result.usage()

    assert outputs == ["partial", "final"]
    assert output == "done"
    assert usage is second_usage

    assert len(agent_impl.calls) == 2
    first_call, second_call = agent_impl.calls
    assert first_call["user_prompt"] == "hello"
    assert first_call["message_history"] is None
    assert first_call["usage"] is None
    assert first_call["usage_limits"] is usage_limits

    assert second_call["user_prompt"] is None
    assert second_call["usage_limits"] is usage_limits
    assert second_call["message_history"] == [{"turn": {"text": "first-attempt"}}]
    assert second_call["message_history"] is not first_messages
    assert second_call["message_history"][0] is not first_messages[0]
    assert second_call["usage"] is not first_usage
    assert second_call["usage"].details == {"cached": 1}

    assert len(first_cm.exit_calls) == 1
    assert first_cm.exit_calls[0][0] is APIError
    assert len(second_cm.exit_calls) == 1
    assert second_cm.exit_calls[0] == (None, None)


@pytest.mark.anyio
async def test_stream_with_retries_does_not_retry_non_retryable_interrupt() -> None:
    non_retryable = _api_error("Invalid API key")
    first_result = _FakeStreamedRunResult(
        outputs=[],
        final_output="unused",
        messages=[],
        usage=RunUsage(),
        stream_error=non_retryable,
    )
    first_cm = _FakeRunStreamContextManager(result=first_result)
    agent_impl = _FakeAgent([first_cm])

    async with stream_with_retries(
        agent=cast(Any, agent_impl),
        user_prompt="hello",
        usage_limits=UsageLimits(request_limit=3),
    ) as result:
        with pytest.raises(APIError, match="Invalid API key"):
            async for _chunk in result.stream_output():
                pass

    assert len(agent_impl.calls) == 1
    assert len(first_cm.exit_calls) == 1
    assert first_cm.exit_calls[0][0] is APIError


def test_stream_with_retries_requires_usage_limits() -> None:
    agent_impl = _FakeAgent([])
    with pytest.raises(TypeError):
        stream_with_retries(  # type: ignore[call-arg]
            agent=cast(Any, agent_impl),
            user_prompt="hello",
        )
