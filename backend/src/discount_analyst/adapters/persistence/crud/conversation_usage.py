from collections.abc import Mapping
from typing import cast

from discount_analyst.adapters.persistence.models import AgentConversationMessage
from discount_analyst.domain.model_selection.context_windows import TokenUsage


def _optional_token_count(value: object) -> int | None:
    if isinstance(value, bool) or not isinstance(value, int):
        return None
    if value < 0:
        return None
    return value


def _mapping_get(container: object, key: str) -> object:
    if not isinstance(container, Mapping):
        return None
    return cast(Mapping[str, object], container).get(key)


def token_usage_from_message_payload(
    message_obj: Mapping[str, object],
) -> TokenUsage | None:
    if str(message_obj.get("kind", "request")) != "response":
        return None
    usage_fields = _mapping_get(message_obj, "usage")
    input_tokens = _optional_token_count(_mapping_get(usage_fields, "input_tokens"))
    if input_tokens is None:
        return None
    return TokenUsage.from_counts(
        input_tokens=input_tokens,
        output_tokens=_optional_token_count(_mapping_get(usage_fields, "output_tokens"))
        or 0,
        cache_write_tokens=_optional_token_count(
            _mapping_get(usage_fields, "cache_write_tokens")
        )
        or 0,
        cache_read_tokens=_optional_token_count(
            _mapping_get(usage_fields, "cache_read_tokens")
        )
        or 0,
        total_tokens=_optional_token_count(_mapping_get(usage_fields, "total_tokens")),
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
