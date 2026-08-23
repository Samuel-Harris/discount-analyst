"""Tests for InfallibleToolset wrapper."""

from unittest.mock import MagicMock

import httpx
import pytest
from pydantic_ai.exceptions import ModelRetry
from pydantic_ai.tools import ToolDefinition

from discount_analyst.agents.tools.terminal.infallible_toolset import (
    INFALLIBLE_TOOL_EXECUTION,
    format_tool_error,
)


def test_format_tool_error_402() -> None:
    exc = RuntimeError("API returned 402 Payment Required")
    result = format_tool_error("fmp_quote", exc)
    assert "402" in result
    assert "quota exceeded" in result.lower()
    assert "fmp_quote" in result


def test_format_tool_error_401() -> None:
    exc = RuntimeError("401 Unauthorized")
    result = format_tool_error("eodhd_prices", exc)
    assert "401" in result
    assert "authentication" in result.lower()


def test_format_tool_error_403() -> None:
    exc = RuntimeError("403 Forbidden")
    result = format_tool_error("fmp_financials", exc)
    assert "403" in result
    assert "denied" in result.lower()


def test_format_tool_error_404() -> None:
    exc = RuntimeError("404 Not Found")
    result = format_tool_error("fmp_profile", exc)
    assert "404" in result
    assert "not found" in result.lower()


def test_format_tool_error_429() -> None:
    exc = RuntimeError("429 Too Many Requests")
    result = format_tool_error("fmp_quote", exc)
    assert "429" in result
    assert "rate limit" in result.lower()


def test_format_tool_error_rate_limit_text() -> None:
    exc = RuntimeError("Rate limit exceeded for this endpoint")
    result = format_tool_error("fmp_quote", exc)
    assert "rate limit" in result.lower()


def test_format_tool_error_timeout() -> None:
    exc = RuntimeError("Connection timeout after 30s")
    result = format_tool_error("eodhd_news", exc)
    assert "timed out" in result.lower()


def test_format_tool_error_generic() -> None:
    exc = RuntimeError("Unknown database error")
    result = format_tool_error("some_tool", exc)
    assert "Unknown database error" in result
    assert "some_tool" in result
    assert "different approach" in result.lower()


def _tool_def(*, name: str, kind: str) -> ToolDefinition:
    return ToolDefinition(name=name, kind=kind)  # type: ignore[arg-type]


async def _wrap_failing_handler(kind: str, exc: Exception) -> object:
    async def handler(_args: dict[str, object]) -> str:
        raise exc

    return await INFALLIBLE_TOOL_EXECUTION.wrap_tool_execute(
        MagicMock(),
        call=MagicMock(),
        tool_def=_tool_def(name="web_fetch", kind=kind),
        args={},
        handler=handler,
    )


async def test_wrap_tool_execute_converts_model_retry_403() -> None:
    result = await _wrap_failing_handler("function", ModelRetry("403 Forbidden"))
    assert isinstance(result, str)
    assert result == format_tool_error("web_fetch", ModelRetry("403 Forbidden"))
    assert "403" in result


async def test_wrap_tool_execute_converts_read_timeout() -> None:
    timeout = httpx.ReadTimeout("Read timeout")
    result = await _wrap_failing_handler("function", timeout)
    assert isinstance(result, str)
    assert "timed out" in result.lower()


async def test_wrap_tool_execute_output_kind_reraises_model_retry() -> None:
    with pytest.raises(ModelRetry, match="schema failed"):
        await _wrap_failing_handler("output", ModelRetry("schema failed"))
