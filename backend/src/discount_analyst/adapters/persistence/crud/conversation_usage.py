from typing import Any

from discount_analyst.adapters.persistence.models import AgentConversationMessage
from discount_analyst.domain.model_selection.context_windows import TokenUsage


def _optional_token_count(value: object) -> int | None:
    if isinstance(value, bool) or not isinstance(value, int):
        return None
    if value < 0:
        return None
    return value


def token_usage_from_message_payload(
    message_obj: dict[str, Any],
) -> TokenUsage | None:
    if str(message_obj.get("kind", "request")) != "response":
        return None
    raw_usage = message_obj.get("usage")
    if not isinstance(raw_usage, dict):
        return None
    input_tokens = _optional_token_count(raw_usage.get("input_tokens"))
    if input_tokens is None:
        return None
    return TokenUsage.from_counts(
        input_tokens=input_tokens,
        output_tokens=_optional_token_count(raw_usage.get("output_tokens")) or 0,
        cache_write_tokens=_optional_token_count(raw_usage.get("cache_write_tokens"))
        or 0,
        cache_read_tokens=_optional_token_count(raw_usage.get("cache_read_tokens"))
        or 0,
        total_tokens=_optional_token_count(raw_usage.get("total_tokens")),
    )


def token_usage_from_message_row(
    msg_row: AgentConversationMessage,
) -> TokenUsage | None:
    if msg_row.input_tokens is None:
        return None
    return TokenUsage.from_counts(
        input_tokens=msg_row.input_tokens,
        output_tokens=msg_row.output_tokens or 0,
        cache_write_tokens=msg_row.cache_write_tokens or 0,
        cache_read_tokens=msg_row.cache_read_tokens or 0,
        total_tokens=msg_row.total_tokens,
    )
