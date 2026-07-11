"""User-facing error messages for dashboard pipeline agent failures."""

from __future__ import annotations

from pydantic_ai.exceptions import UnexpectedModelBehavior


def extract_agent_error_message(exc: BaseException) -> str:
    """Extract a user-friendly error message, especially for tool failures.

    UnexpectedModelBehavior wraps the underlying cause (e.g., ModelRetry with
    a 402 Payment Required from FMP). This extracts the root cause message.
    """
    if isinstance(exc, UnexpectedModelBehavior):
        cause = exc.__cause__
        if cause is not None:
            cause_msg = str(cause)
            if "402" in cause_msg:
                return f"API quota exceeded (402 Payment Required): {cause_msg}"
            if "401" in cause_msg:
                return f"API authentication failed (401): {cause_msg}"
            if "403" in cause_msg:
                return f"API access denied (403 Forbidden): {cause_msg}"
            return f"Tool failure: {cause_msg}"
        return str(exc)
    return str(exc)
