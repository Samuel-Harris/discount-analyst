from discount_analyst.domain.model_selection.context_windows import (
    CONTEXT_WINDOW_TOKENS,
    TokenUsage,
    attach_context_window,
    context_window_tokens_for,
    context_window_used_pct,
)
from discount_analyst.domain.model_selection.model_name import ModelName


def test_every_model_name_has_a_context_window() -> None:
    assert set(CONTEXT_WINDOW_TOKENS) == set(ModelName)


def test_context_window_tokens_for_known_and_missing_models() -> None:
    assert context_window_tokens_for(ModelName.GPT_5_6_LUNA) == 1_050_000
    assert context_window_tokens_for(None) is None


def test_attach_context_window_includes_percentage_when_window_is_known() -> None:
    usage = TokenUsage.from_counts(
        input_tokens=105_000,
        output_tokens=10,
        cache_write_tokens=0,
        cache_read_tokens=1_000,
        total_tokens=105_010,
    )
    snapshot = attach_context_window(usage, ModelName.GPT_5_6_LUNA)
    assert snapshot.context_window_tokens == 1_050_000
    assert snapshot.context_window_used_pct == 10.0
    assert snapshot.to_json_dict()["context_window_used_pct"] == 10.0
    assert context_window_used_pct(105_000, 1_050_000) == 10.0


def test_attach_context_window_omits_window_when_model_is_unknown() -> None:
    usage = TokenUsage.from_counts(
        input_tokens=12,
        output_tokens=3,
        cache_write_tokens=0,
        cache_read_tokens=0,
    )
    snapshot = attach_context_window(usage, None)
    payload = snapshot.to_json_dict()
    assert "context_window_tokens" not in payload
    assert "context_window_used_pct" not in payload
    assert payload["input_tokens"] == 12
    assert payload["total_tokens"] == 15


def test_token_usage_from_counts_fills_missing_total() -> None:
    usage = TokenUsage.from_counts(input_tokens=10, output_tokens=4)
    assert usage.total_tokens == 14
