from dataclasses import asdict, dataclass

from discount_analyst.domain.model_selection.model_name import ModelName

CONTEXT_WINDOW_TOKENS: dict[ModelName, int] = {
    ModelName.CLAUDE_OPUS_4_5: 200_000,
    ModelName.CLAUDE_SONNET_4_5: 200_000,
    ModelName.CLAUDE_OPUS_4_6: 1_000_000,
    ModelName.CLAUDE_SONNET_4_6: 1_000_000,
    ModelName.CLAUDE_HAIKU_4_6: 200_000,
    ModelName.GPT_5_1: 400_000,
    ModelName.GPT_5_2: 400_000,
    ModelName.GPT_5_4: 1_000_000,
    ModelName.GPT_5_6_LUNA: 1_050_000,
    ModelName.GEMINI_3_PRO_PREVIEW: 1_000_000,
    ModelName.GEMINI_3_1_PRO_PREVIEW: 1_000_000,
    ModelName.DEEPSEEK_V4_FLASH: 1_048_576,
    ModelName.DEEPSEEK_V4_PRO: 1_048_576,
}


@dataclass(frozen=True, slots=True)
class TokenUsage:
    input_tokens: int
    output_tokens: int
    cache_write_tokens: int
    cache_read_tokens: int
    total_tokens: int

    @classmethod
    def from_counts(
        cls,
        *,
        input_tokens: int,
        output_tokens: int = 0,
        cache_write_tokens: int = 0,
        cache_read_tokens: int = 0,
        total_tokens: int | None = None,
    ) -> TokenUsage:
        return cls(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cache_write_tokens=cache_write_tokens,
            cache_read_tokens=cache_read_tokens,
            total_tokens=(
                input_tokens + output_tokens if total_tokens is None else total_tokens
            ),
        )


@dataclass(frozen=True, slots=True)
class ContextUsageSnapshot:
    input_tokens: int
    output_tokens: int
    cache_write_tokens: int
    cache_read_tokens: int
    total_tokens: int
    context_window_tokens: int | None = None
    context_window_used_pct: float | None = None

    def to_json_dict(self) -> dict[str, int | float]:
        return {key: value for key, value in asdict(self).items() if value is not None}


def context_window_tokens_for(model_name: ModelName | None) -> int | None:
    if model_name is None:
        return None
    return CONTEXT_WINDOW_TOKENS.get(model_name)


def context_window_used_pct(input_tokens: int, context_window_tokens: int) -> float:
    return round(100 * input_tokens / context_window_tokens, 1)


def attach_context_window(
    usage: TokenUsage, model_name: ModelName | None
) -> ContextUsageSnapshot:
    window = context_window_tokens_for(model_name)
    return ContextUsageSnapshot(
        input_tokens=usage.input_tokens,
        output_tokens=usage.output_tokens,
        cache_write_tokens=usage.cache_write_tokens,
        cache_read_tokens=usage.cache_read_tokens,
        total_tokens=usage.total_tokens,
        context_window_tokens=window,
        context_window_used_pct=(
            None
            if window is None
            else context_window_used_pct(usage.input_tokens, window)
        ),
    )
