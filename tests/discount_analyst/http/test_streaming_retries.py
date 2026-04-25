"""Unit tests for streaming retry helpers."""

from collections.abc import Callable
from typing import Any, cast

import httpx
import pytest
from openai import APIError
from pydantic_ai import capture_run_messages
from pydantic_ai.exceptions import UnexpectedModelBehavior
from pydantic_ai.messages import (
    ModelRequest,
    ModelResponse,
    PartStartEvent,
    TextPart,
    UserPromptPart,
)
from pydantic_ai.usage import RunUsage, UsageLimits

import discount_analyst.agents.common.streaming_retries as streaming_retries_mod
from discount_analyst.agents.common.streaming_retries import (
    api_error_indicates_rate_limit,
    should_repair_structured_output_error,
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


def test_should_retry_streaming_error_remote_protocol_error() -> None:
    exc = httpx.RemoteProtocolError(
        "peer closed connection without sending complete message body "
        "(incomplete chunked read)"
    )
    assert should_retry_streaming_error(exc) is True


def test_should_retry_streaming_error_timeout_error() -> None:
    exc = TimeoutError("MCP server connection timed out")
    assert should_retry_streaming_error(exc) is True


def test_should_retry_streaming_error_exception_group_with_timeout() -> None:
    exc = ExceptionGroup("unhandled errors in a TaskGroup", [TimeoutError()])
    assert should_retry_streaming_error(exc) is True


def test_should_retry_streaming_error_exception_group_with_non_retryable() -> None:
    exc = ExceptionGroup("errors", [ValueError("not retryable")])
    assert should_retry_streaming_error(exc) is False


def test_should_repair_structured_output_error_validation_message() -> None:
    exc = UnexpectedModelBehavior("Exceeded maximum retries (1) for output validation")
    assert should_repair_structured_output_error(exc) is True


def test_should_repair_structured_output_error_tool_failure_negative() -> None:
    exc = UnexpectedModelBehavior("Tool failed after maximum retries")
    assert should_repair_structured_output_error(exc) is False


def test_streaming_retry_sleep_tpm_waits_60s() -> None:
    exc = _api_error(
        "Rate limit reached for gpt-5.1 on tokens per min (TPM): "
        "Limit 500000. Please try again in 1.5s."
    )
    assert streaming_retry_sleep_seconds(exc, attempt=0) == 60.0


def test_streaming_retry_sleep_rpm_waits_60s() -> None:
    exc = _api_error(
        "Rate limit reached on requests per min (RPM). Please try again in 2s."
    )
    assert streaming_retry_sleep_seconds(exc, attempt=0) == 60.0


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
        response: Any | None = None,
        stream_error: BaseException | None = None,
        get_output_error: BaseException | None = None,
    ) -> None:
        self._outputs = outputs
        self._final_output = final_output
        self._messages = messages
        self._usage = usage
        self._response = response
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

    @property
    def response(self) -> Any:
        if self._response is None:
            raise AttributeError("Fake result has no response")
        return self._response


class _FakeRunStreamContextManager:
    def __init__(
        self,
        *,
        result: _FakeStreamedRunResult | None = None,
        enter_error: BaseException | None = None,
        captured_messages: list[Any] | None = None,
        open_stream_events: list[Any] | None = None,
        on_exit: Callable[[], None] | None = None,
    ) -> None:
        self._result = result
        self._enter_error = enter_error
        self._captured_messages = captured_messages
        self._open_stream_events = open_stream_events
        self._event_stream_handler: Callable[[Any, Any], Any] | None = None
        self._on_exit = on_exit
        self.exit_calls: list[
            tuple[type[BaseException] | None, BaseException | None]
        ] = []

    def set_event_stream_handler(
        self,
        event_stream_handler: Callable[[Any, Any], Any] | None,
    ) -> None:
        self._event_stream_handler = event_stream_handler

    async def __aenter__(self) -> _FakeStreamedRunResult:
        if self._captured_messages is not None:
            with capture_run_messages() as messages:
                messages.extend(self._captured_messages)
        if (
            self._open_stream_events is not None
            and self._event_stream_handler is not None
        ):
            open_stream_events = self._open_stream_events

            async def _events():
                for event in open_stream_events:
                    yield event

            await self._event_stream_handler(None, _events())
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
        event_stream_handler: Callable[[Any, Any], Any] | None = None,
    ) -> _FakeRunStreamContextManager:
        call_index = len(self.calls)
        if call_index >= len(self._context_managers):
            raise AssertionError("Unexpected run_stream call")
        context_manager = self._context_managers[call_index]
        context_manager.set_event_stream_handler(event_stream_handler)
        self.calls.append(
            {
                "user_prompt": user_prompt,
                "message_history": message_history,
                "usage_limits": usage_limits,
                "usage": usage,
            }
        )
        return context_manager


def _user_prompt_text(message: Any) -> str:
    assert isinstance(message, ModelRequest)
    assert len(message.parts) == 1
    part = message.parts[0]
    assert isinstance(part, UserPromptPart)
    assert isinstance(part.content, str)
    return part.content


@pytest.mark.anyio
async def test_stream_with_retries_resumes_with_copied_history_and_usage(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def _no_wait(exc: BaseException, attempt: int) -> float:
        del exc, attempt
        return 0.0

    monkeypatch.setattr(
        streaming_retries_mod,
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
    assert second_call["message_history"][:1] == [{"turn": {"text": "first-attempt"}}]
    assert second_call["message_history"] is not first_messages
    assert second_call["message_history"][0] is not first_messages[0]
    retry_prompt = _user_prompt_text(second_call["message_history"][1])
    assert "Your previous response was interrupted before it finished." in retry_prompt
    assert "Partial draft from the interrupted response:" in retry_prompt
    assert "partial" in retry_prompt
    assert second_call["usage"] is not first_usage
    assert second_call["usage"].details == {"cached": 1}

    assert len(first_cm.exit_calls) == 1
    assert first_cm.exit_calls[0][0] is APIError
    assert len(second_cm.exit_calls) == 1
    assert second_cm.exit_calls[0] == (None, None)


@pytest.mark.anyio
async def test_stream_with_retries_preserves_checkpoint_across_open_retry(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def _no_wait(exc: BaseException, attempt: int) -> float:
        del exc, attempt
        return 0.0

    monkeypatch.setattr(
        streaming_retries_mod,
        "streaming_retry_sleep_seconds",
        _no_wait,
    )

    first_messages = [{"turn": {"text": "checkpointed"}}]
    first_usage = RunUsage(input_tokens=9, output_tokens=4, details={"reasoning": 2})
    first_result = _FakeStreamedRunResult(
        outputs=["partial"],
        final_output="unused",
        messages=first_messages,
        usage=first_usage,
        stream_error=_api_error("Rate limit reached, please try again in 0.1s."),
    )
    first_cm = _FakeRunStreamContextManager(result=first_result)
    failed_open_cm = _FakeRunStreamContextManager(
        enter_error=_api_error("Rate limit reached while opening stream.")
    )
    final_result = _FakeStreamedRunResult(
        outputs=["resumed"],
        final_output="done",
        messages=[{"turn": {"text": "resumed"}}],
        usage=RunUsage(input_tokens=20, output_tokens=10),
    )
    final_cm = _FakeRunStreamContextManager(result=final_result)
    agent_impl = _FakeAgent([first_cm, failed_open_cm, final_cm])

    outputs: list[str] = []
    async with stream_with_retries(
        agent=cast(Any, agent_impl),
        user_prompt="hello",
        usage_limits=UsageLimits(request_limit=5),
    ) as result:
        async for chunk in result.stream_output(debounce_by=None):
            outputs.append(chunk)

    assert outputs == ["partial", "resumed"]
    assert len(agent_impl.calls) == 3
    first_call, failed_open_call, final_call = agent_impl.calls
    assert first_call["user_prompt"] == "hello"
    assert first_call["message_history"] is None
    assert first_call["usage"] is None

    assert failed_open_call["user_prompt"] is None
    assert failed_open_call["message_history"][:1] == [
        {"turn": {"text": "checkpointed"}}
    ]
    assert failed_open_call["message_history"] is not first_messages
    retry_prompt = _user_prompt_text(failed_open_call["message_history"][1])
    assert "Partial draft from the interrupted response:" in retry_prompt
    assert "partial" in retry_prompt
    assert failed_open_call["usage"] is not first_usage
    assert failed_open_call["usage"].details == {"reasoning": 2}

    assert final_call["user_prompt"] is None
    assert final_call["message_history"][:1] == [{"turn": {"text": "checkpointed"}}]
    assert final_call["message_history"] is failed_open_call["message_history"]
    assert final_call["usage"] is failed_open_call["usage"]

    assert len(first_cm.exit_calls) == 1
    assert first_cm.exit_calls[0][0] is APIError
    assert failed_open_cm.exit_calls == []
    assert len(final_cm.exit_calls) == 1
    assert final_cm.exit_calls[0] == (None, None)


@pytest.mark.anyio
async def test_stream_with_retries_checkpoints_captured_open_messages_on_tpm(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sleep_calls: list[float] = []

    async def _record_sleep(delay: float) -> None:
        sleep_calls.append(delay)

    monkeypatch.setattr(streaming_retries_mod.asyncio, "sleep", _record_sleep)

    captured_messages = [{"turn": {"text": "tool-progress-before-tpm"}}]
    first_cm = _FakeRunStreamContextManager(
        enter_error=_api_error(
            "Rate limit reached for gpt-5.1 on tokens per min (TPM): "
            "Limit 500000. Please try again in 422ms."
        ),
        captured_messages=captured_messages,
        open_stream_events=[
            PartStartEvent(
                index=0,
                part=TextPart("I had started drafting the interrupted answer."),
            )
        ],
    )
    final_result = _FakeStreamedRunResult(
        outputs=["resumed"],
        final_output="done",
        messages=[{"turn": {"text": "after-tpm-retry"}}],
        usage=RunUsage(input_tokens=25, output_tokens=9),
    )
    final_cm = _FakeRunStreamContextManager(result=final_result)
    agent_impl = _FakeAgent([first_cm, final_cm])

    outputs: list[str] = []
    async with stream_with_retries(
        agent=cast(Any, agent_impl),
        user_prompt="hello",
        usage_limits=UsageLimits(request_limit=5),
    ) as result:
        async for chunk in result.stream_output(debounce_by=None):
            outputs.append(chunk)

    assert outputs == ["resumed"]
    assert sleep_calls == [60.0]

    assert len(agent_impl.calls) == 2
    first_call, second_call = agent_impl.calls
    assert first_call["user_prompt"] == "hello"
    assert first_call["message_history"] is None
    assert first_call["usage"] is None

    assert second_call["user_prompt"] is None
    assert second_call["message_history"][:1] == [
        {"turn": {"text": "tool-progress-before-tpm"}}
    ]
    assert second_call["message_history"] is not captured_messages
    assert second_call["message_history"][0] is not captured_messages[0]
    retry_prompt = _user_prompt_text(second_call["message_history"][1])
    assert "Continue from the point where it stopped" in retry_prompt
    assert "I had started drafting the interrupted answer." in retry_prompt
    assert second_call["usage"] is None

    assert first_cm.exit_calls == []
    assert len(final_cm.exit_calls) == 1
    assert final_cm.exit_calls[0] == (None, None)


@pytest.mark.anyio
async def test_stream_with_retries_does_not_replay_prompt_on_uncheckpointed_open_failure() -> (
    None
):
    open_error = _api_error("Rate limit reached while opening stream.")
    failed_open_cm = _FakeRunStreamContextManager(enter_error=open_error)
    agent_impl = _FakeAgent([failed_open_cm])

    with pytest.raises(APIError, match="Rate limit reached") as exc_info:
        async with stream_with_retries(
            agent=cast(Any, agent_impl),
            user_prompt="hello",
            usage_limits=UsageLimits(request_limit=5),
        ):
            pass

    assert exc_info.value is open_error
    assert getattr(exc_info.value, "__notes__", []) == [
        "Stream retry was not attempted because no message-history checkpoint "
        "was available; the original prompt was not replayed."
    ]
    assert agent_impl.calls == [
        {
            "user_prompt": "hello",
            "message_history": None,
            "usage_limits": UsageLimits(request_limit=5),
            "usage": None,
        }
    ]
    assert failed_open_cm.exit_calls == []


@pytest.mark.anyio
async def test_stream_with_retries_retries_tool_startup_timeout_before_checkpoint(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def _no_wait(exc: BaseException, attempt: int) -> float:
        del exc, attempt
        return 0.0

    monkeypatch.setattr(
        streaming_retries_mod,
        "streaming_retry_sleep_seconds",
        _no_wait,
    )

    failed_open_cm = _FakeRunStreamContextManager(
        enter_error=ExceptionGroup(
            "unhandled errors in a TaskGroup",
            [TimeoutError("MCP server connection timed out")],
        )
    )
    final_result = _FakeStreamedRunResult(
        outputs=["started"],
        final_output="done",
        messages=[{"turn": {"text": "started"}}],
        usage=RunUsage(input_tokens=8, output_tokens=3),
    )
    final_cm = _FakeRunStreamContextManager(result=final_result)
    agent_impl = _FakeAgent([failed_open_cm, final_cm])

    outputs: list[str] = []
    async with stream_with_retries(
        agent=cast(Any, agent_impl),
        user_prompt="hello",
        usage_limits=UsageLimits(request_limit=5),
    ) as result:
        async for chunk in result.stream_output(debounce_by=None):
            outputs.append(chunk)

    assert outputs == ["started"]
    assert len(agent_impl.calls) == 2
    first_call, second_call = agent_impl.calls
    assert first_call["user_prompt"] == "hello"
    assert first_call["message_history"] is None
    assert first_call["usage"] is None
    assert second_call["user_prompt"] == "hello"
    assert second_call["message_history"] is None
    assert second_call["usage"] is None
    assert failed_open_cm.exit_calls == []
    assert len(final_cm.exit_calls) == 1
    assert final_cm.exit_calls[0] == (None, None)


@pytest.mark.anyio
async def test_stream_with_retries_get_output_retry_preserves_history_and_usage(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def _no_wait(exc: BaseException, attempt: int) -> float:
        del exc, attempt
        return 0.0

    monkeypatch.setattr(
        streaming_retries_mod,
        "streaming_retry_sleep_seconds",
        _no_wait,
    )

    first_messages = [{"turn": {"text": "before-get-output"}}]
    first_usage = RunUsage(input_tokens=13, output_tokens=8, details={"cached": 3})
    first_result = _FakeStreamedRunResult(
        outputs=["partial"],
        final_output="unused",
        messages=first_messages,
        usage=first_usage,
        get_output_error=_api_error("Rate limit reached while getting output."),
    )
    second_result = _FakeStreamedRunResult(
        outputs=[],
        final_output="done",
        messages=[{"turn": {"text": "after-get-output"}}],
        usage=RunUsage(input_tokens=21, output_tokens=12),
    )
    first_cm = _FakeRunStreamContextManager(result=first_result)
    second_cm = _FakeRunStreamContextManager(result=second_result)
    agent_impl = _FakeAgent([first_cm, second_cm])

    outputs: list[str] = []
    async with stream_with_retries(
        agent=cast(Any, agent_impl),
        user_prompt="hello",
        usage_limits=UsageLimits(request_limit=5),
    ) as result:
        async for chunk in result.stream_output(debounce_by=None):
            outputs.append(chunk)
        output = await result.get_output()
        usage = result.usage()

    assert outputs == ["partial"]
    assert output == "done"
    assert usage is second_result.usage()

    assert len(agent_impl.calls) == 2
    first_call, second_call = agent_impl.calls
    assert first_call["user_prompt"] == "hello"
    assert first_call["message_history"] is None
    assert first_call["usage"] is None

    assert second_call["user_prompt"] is None
    assert second_call["message_history"][:1] == [
        {"turn": {"text": "before-get-output"}}
    ]
    assert second_call["message_history"] is not first_messages
    retry_prompt = _user_prompt_text(second_call["message_history"][1])
    assert "Partial draft from the interrupted response:" in retry_prompt
    assert "partial" in retry_prompt
    assert second_call["usage"] is not first_usage
    assert second_call["usage"].details == {"cached": 3}

    assert len(first_cm.exit_calls) == 1
    assert first_cm.exit_calls[0][0] is APIError
    assert len(second_cm.exit_calls) == 1
    assert second_cm.exit_calls[0] == (None, None)


@pytest.mark.anyio
async def test_stream_with_retries_get_output_retry_uses_response_partial(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def _no_wait(exc: BaseException, attempt: int) -> float:
        del exc, attempt
        return 0.0

    monkeypatch.setattr(
        streaming_retries_mod,
        "streaming_retry_sleep_seconds",
        _no_wait,
    )

    first_messages = [{"turn": {"text": "before-response-partial"}}]
    first_result = _FakeStreamedRunResult(
        outputs=[],
        final_output="unused",
        messages=first_messages,
        usage=RunUsage(input_tokens=13, output_tokens=8),
        response=ModelResponse(
            parts=[TextPart("Draft recovered from response state.")]
        ),
        get_output_error=_api_error("Rate limit reached while getting output."),
    )
    second_result = _FakeStreamedRunResult(
        outputs=[],
        final_output="done",
        messages=[{"turn": {"text": "after-response-partial"}}],
        usage=RunUsage(input_tokens=21, output_tokens=12),
    )
    first_cm = _FakeRunStreamContextManager(result=first_result)
    second_cm = _FakeRunStreamContextManager(result=second_result)
    agent_impl = _FakeAgent([first_cm, second_cm])

    async with stream_with_retries(
        agent=cast(Any, agent_impl),
        user_prompt="hello",
        usage_limits=UsageLimits(request_limit=5),
    ) as result:
        output = await result.get_output()

    assert output == "done"
    assert len(agent_impl.calls) == 2
    second_call = agent_impl.calls[1]
    assert second_call["user_prompt"] is None
    assert second_call["message_history"][:1] == [
        {"turn": {"text": "before-response-partial"}}
    ]
    retry_prompt = _user_prompt_text(second_call["message_history"][1])
    assert "Draft recovered from response state." in retry_prompt


@pytest.mark.anyio
async def test_stream_with_retries_repairs_structured_output_validation_failure() -> (
    None
):
    validation_error = UnexpectedModelBehavior(
        "Exceeded maximum retries (1) for output validation: missing field"
    )
    first_messages = [{"turn": {"text": "invalid-structured-output"}}]
    first_result = _FakeStreamedRunResult(
        outputs=["invalid"],
        final_output="unused",
        messages=first_messages,
        usage=RunUsage(input_tokens=12, output_tokens=6),
        get_output_error=validation_error,
    )
    repaired_result = _FakeStreamedRunResult(
        outputs=[],
        final_output="repaired",
        messages=[{"turn": {"text": "repaired-structured-output"}}],
        usage=RunUsage(input_tokens=18, output_tokens=9),
    )
    first_cm = _FakeRunStreamContextManager(result=first_result)
    repaired_cm = _FakeRunStreamContextManager(result=repaired_result)
    agent_impl = _FakeAgent([first_cm, repaired_cm])

    outputs: list[str] = []
    async with stream_with_retries(
        agent=cast(Any, agent_impl),
        user_prompt="hello",
        usage_limits=UsageLimits(request_limit=5),
    ) as result:
        async for chunk in result.stream_output(debounce_by=None):
            outputs.append(chunk)
        output = await result.get_output()

    assert outputs == ["invalid"]
    assert output == "repaired"
    assert len(agent_impl.calls) == 2
    second_call = agent_impl.calls[1]
    assert second_call["user_prompt"] is None
    assert second_call["message_history"][:1] == [
        {"turn": {"text": "invalid-structured-output"}}
    ]
    repair_prompt = _user_prompt_text(second_call["message_history"][1])
    assert "could not be validated" in repair_prompt
    assert "missing field" in repair_prompt
    assert second_call["usage"].input_tokens == 12
    assert len(first_cm.exit_calls) == 1
    assert first_cm.exit_calls[0][0] is UnexpectedModelBehavior
    assert len(repaired_cm.exit_calls) == 1
    assert repaired_cm.exit_calls[0] == (None, None)


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
