"""Tests for InfallibleToolset wrapper."""

from discount_analyst.integrations.infallible_toolset import format_tool_error


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
