"""Unit tests for streaming retry helpers."""

from typing import Any, cast

from openai import APIError

from discount_analyst.shared.http.rate_limit_client import (
    api_error_indicates_rate_limit,
    should_retry_streaming_error,
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
