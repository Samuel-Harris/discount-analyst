"""Tests for ``run_streamed_agent``."""

from typing import Any, cast

import pytest
from pydantic_ai.usage import RunUsage, UsageLimits

import discount_analyst.agents.common.streamed_agent_run as streamed_agent_run_mod
import discount_analyst.agents.common.streaming_retries as streaming_retries
from discount_analyst.agents.common.streamed_agent_run import (
    StreamedAgentRunOutcome,
    run_streamed_agent,
)


class _FakeStreamedRunResult:
    def __init__(self) -> None:
        self._usage = RunUsage(input_tokens=3, output_tokens=5)
        self.last_debounce: float | None = None

    async def stream_output(self, *, debounce_by: float | None = 0.1):
        self.last_debounce = debounce_by
        yield "x"

    async def get_output(self) -> str:
        return "done"

    def usage(self) -> RunUsage:
        return self._usage

    def all_messages(
        self, *, output_tool_return_content: str | None = None
    ) -> list[Any]:
        del output_tool_return_content
        return [{"role": "assistant"}]


class _FakeRunStreamContextManager:
    def __init__(self, result: _FakeStreamedRunResult) -> None:
        self._result = result

    async def __aenter__(self) -> _FakeStreamedRunResult:
        return self._result

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: Any,
    ) -> bool:
        del exc_type, exc, traceback
        return False


class _FakeAgent:
    def __init__(self, *, name: Any | None = "surveyor") -> None:
        self.name = name
        self.streamed_result = _FakeStreamedRunResult()

    def run_stream(
        self,
        user_prompt: str | None,
        *,
        message_history: list[Any] | None = None,
        usage_limits: UsageLimits | None = None,
        usage: RunUsage | None = None,
    ) -> _FakeRunStreamContextManager:
        del user_prompt, message_history, usage_limits, usage
        return _FakeRunStreamContextManager(self.streamed_result)


class _FakeSpan:
    def __init__(
        self,
        *,
        parent: "_FakeLogfire",
        tags: tuple[str, ...],
        message: str,
        attrs: dict[str, Any],
    ) -> None:
        self._parent = parent
        self._tags = tags
        self._message = message
        self._attrs = attrs

    def __enter__(self) -> "_FakeSpan":
        self._parent.entered_spans.append((self._tags, self._message, self._attrs))
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: Any,
    ) -> bool:
        del exc_type, exc, traceback
        return False


class _FakeTaggedLogfire:
    def __init__(self, *, parent: "_FakeLogfire", tags: tuple[str, ...]) -> None:
        self._parent = parent
        self._tags = tags

    def span(self, message: str, **attrs: Any) -> _FakeSpan:
        return _FakeSpan(
            parent=self._parent,
            tags=self._tags,
            message=message,
            attrs=attrs,
        )


class _FakeLogfire:
    def __init__(self) -> None:
        self.with_tags_calls: list[tuple[str, ...]] = []
        self.entered_spans: list[tuple[tuple[str, ...], str, dict[str, Any]]] = []

    def with_tags(self, *tags: str) -> _FakeTaggedLogfire:
        self.with_tags_calls.append(tags)
        return _FakeTaggedLogfire(parent=self, tags=tags)


@pytest.mark.anyio
async def test_run_streamed_agent_callback_debounce_and_outcome(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def _no_wait(exc: BaseException, attempt: int) -> float:
        del exc, attempt
        return 0.0

    monkeypatch.setattr(
        streaming_retries,
        "streaming_retry_sleep_seconds",
        _no_wait,
    )
    fake_logfire = _FakeLogfire()
    monkeypatch.setattr(streamed_agent_run_mod, "AI_LOGFIRE", fake_logfire)

    agent = _FakeAgent(name="surveyor")
    seen: list[str] = []
    outcome = await run_streamed_agent(
        agent=cast(Any, agent),
        user_prompt="hi",
        usage_limits=UsageLimits(request_limit=2),
        stream_debounce_by=0.2,
        on_stream_chunk=seen.append,
    )

    assert agent.streamed_result.last_debounce == 0.2
    assert isinstance(outcome, StreamedAgentRunOutcome)
    assert outcome.output == "done"
    assert outcome.usage.input_tokens == 3
    assert outcome.all_messages == [{"role": "assistant"}]
    assert seen == ["x"]
    assert outcome.elapsed_s >= 0.0
    assert fake_logfire.with_tags_calls == [("surveyor",)]
    assert fake_logfire.entered_spans == [
        (
            ("surveyor",),
            "Run AI agent {agent_name}",
            {"agent_name": "surveyor"},
        )
    ]


@pytest.mark.anyio
async def test_run_streamed_agent_raises_when_name_is_none(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def _no_wait(exc: BaseException, attempt: int) -> float:
        del exc, attempt
        return 0.0

    monkeypatch.setattr(
        streaming_retries,
        "streaming_retry_sleep_seconds",
        _no_wait,
    )
    fake_logfire = _FakeLogfire()
    monkeypatch.setattr(streamed_agent_run_mod, "AI_LOGFIRE", fake_logfire)

    agent = _FakeAgent(name=None)
    with pytest.raises(ValueError, match="Agent name is required"):
        await run_streamed_agent(
            agent=cast(Any, agent),
            user_prompt="hi",
            usage_limits=UsageLimits(request_limit=2),
        )

    assert fake_logfire.with_tags_calls == []
