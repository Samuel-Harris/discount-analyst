from collections.abc import Iterator
from typing import Any

from pydantic_ai.messages import ModelMessage, ModelResponse

from discount_analyst.domain.model_selection.context_windows import TokenUsage
from discount_analyst.domain.model_selection.model_name import ModelName


def parse_model_name(raw: object) -> ModelName | None:
    if isinstance(raw, ModelName):
        return raw
    if raw is None:
        return None
    try:
        return ModelName(str(raw))
    except ValueError:
        return None


def _non_negative_int(value: object, *, default: int = 0) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        return default
    if value < 0:
        return default
    return value


def _optional_non_negative_int(value: object) -> int | None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        return None
    return value


def token_usage_from_model_response(message: ModelResponse) -> TokenUsage:
    usage = message.usage
    return TokenUsage.from_counts(
        input_tokens=_non_negative_int(getattr(usage, "input_tokens", 0)),
        output_tokens=_non_negative_int(getattr(usage, "output_tokens", 0)),
        cache_write_tokens=_non_negative_int(getattr(usage, "cache_write_tokens", 0)),
        cache_read_tokens=_non_negative_int(getattr(usage, "cache_read_tokens", 0)),
        total_tokens=_optional_non_negative_int(getattr(usage, "total_tokens", None)),
    )


def iter_model_response_token_usage(
    messages: list[ModelMessage],
) -> Iterator[TokenUsage]:
    for message in messages:
        if isinstance(message, ModelResponse):
            yield token_usage_from_model_response(message)


def agent_model_name(agent: Any) -> ModelName | None:
    model = getattr(agent, "model", None)
    return parse_model_name(getattr(model, "model_name", None))
