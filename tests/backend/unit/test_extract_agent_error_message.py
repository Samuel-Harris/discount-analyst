"""Tests for _extract_agent_error_message in sqlmodel_runner."""

from pydantic_ai.exceptions import UnexpectedModelBehavior

from backend.pipeline.sqlmodel_runner import _extract_agent_error_message


def test_plain_exception_returns_str() -> None:
    exc = ValueError("Something went wrong")
    assert _extract_agent_error_message(exc) == "Something went wrong"


def test_unexpected_model_behavior_without_cause() -> None:
    exc = UnexpectedModelBehavior("Tool failed after max retries")
    assert _extract_agent_error_message(exc) == "Tool failed after max retries"


def test_unexpected_model_behavior_with_402_cause() -> None:
    cause = RuntimeError("MCP tool returned 402 Payment Required")
    exc = UnexpectedModelBehavior("Tool failed")
    exc.__cause__ = cause
    result = _extract_agent_error_message(exc)
    assert "402" in result
    assert "quota exceeded" in result.lower()


def test_unexpected_model_behavior_with_401_cause() -> None:
    cause = RuntimeError("API returned 401 Unauthorized")
    exc = UnexpectedModelBehavior("Tool failed")
    exc.__cause__ = cause
    result = _extract_agent_error_message(exc)
    assert "401" in result
    assert "authentication" in result.lower()


def test_unexpected_model_behavior_with_403_cause() -> None:
    cause = RuntimeError("Access denied 403 Forbidden")
    exc = UnexpectedModelBehavior("Tool failed")
    exc.__cause__ = cause
    result = _extract_agent_error_message(exc)
    assert "403" in result
    assert "denied" in result.lower()


def test_unexpected_model_behavior_with_generic_cause() -> None:
    cause = RuntimeError("Connection timeout")
    exc = UnexpectedModelBehavior("Tool failed")
    exc.__cause__ = cause
    result = _extract_agent_error_message(exc)
    assert "Tool failure:" in result
    assert "Connection timeout" in result
