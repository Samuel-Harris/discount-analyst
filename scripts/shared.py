"""Shared data types, constants, and helpers for scripts (cost comparison, DCF analysis)."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from pydantic import BaseModel

from genai_prices import Usage, calc_price

from discount_analyst.shared.ai_models_config import AIModelsConfig, ModelName
from discount_analyst.shared.data_types import MarketAnalystOutput
from discount_analyst.dcf_analysis.data_types import DCFAnalysisResult

# Models that auto-cache (OpenAI, Gemini); no way to disable — skip when --caching disabled.
AUTO_CACHE_MODELS: frozenset[ModelName] = frozenset(
    {
        ModelName.GPT_5_1,
        ModelName.GPT_5_2,
        ModelName.GEMINI_3_PRO_PREVIEW,
        ModelName.GEMINI_3_1_PRO_PREVIEW,
    }
)


@dataclass(frozen=True)
class ModelPricing:
    """Price per million tokens (USD)."""

    input_per_mtok: float
    output_per_mtok: float
    cache_write_per_mtok: float = 0.0
    cache_read_per_mtok: float = 0.0


@dataclass(frozen=True)
class CostBreakdown:
    """Raw USD cost components for a single model run."""

    input_cost: float
    output_cost: float
    cache_write_cost: float
    cache_read_cost: float
    total_cost: float


@dataclass(frozen=True)
class FormattedCostResult:
    """Pre-formatted cost strings ready for Rich table display."""

    input_cost: str
    output_cost: str
    cache_write_cost: str
    cache_read_cost: str
    total_cost: str
    used_fallback: bool


class ModelRunOutput(BaseModel):
    """Complete serialisable record for one model run written to outputs/."""

    ticker: str
    model_name: str
    risk_free_rate: float
    market_analyst: MarketAnalystOutput
    dcf_result: DCFAnalysisResult | None = None
    dcf_error: str | None = None
    elapsed_s: float
    input_tokens: int
    output_tokens: int
    cache_write_tokens: int
    cache_read_tokens: int
    tool_calls: int


# Fallback pricing when genai_prices does not have the model (e.g. very new models).
# Update as needed; genai_prices is used for actual cost when the model is in its snapshot.
MODEL_PRICING_FALLBACK: dict[ModelName, ModelPricing] = {
    ModelName.CLAUDE_OPUS_4_5: ModelPricing(
        input_per_mtok=15.0,
        output_per_mtok=75.0,
        cache_write_per_mtok=3.75,
        cache_read_per_mtok=0.30,
    ),
    ModelName.CLAUDE_SONNET_4_5: ModelPricing(
        input_per_mtok=3.0,
        output_per_mtok=15.0,
        cache_write_per_mtok=0.90,
        cache_read_per_mtok=0.09,
    ),
    ModelName.CLAUDE_OPUS_4_6: ModelPricing(
        input_per_mtok=15.0,
        output_per_mtok=75.0,
        cache_write_per_mtok=3.75,
        cache_read_per_mtok=0.30,
    ),
    ModelName.CLAUDE_SONNET_4_6: ModelPricing(
        input_per_mtok=3.0,
        output_per_mtok=15.0,
        cache_write_per_mtok=0.90,
        cache_read_per_mtok=0.09,
    ),
    ModelName.GPT_5_1: ModelPricing(
        input_per_mtok=2.50,
        output_per_mtok=10.0,
    ),
    ModelName.GPT_5_2: ModelPricing(
        input_per_mtok=2.50,
        output_per_mtok=10.0,
    ),
    ModelName.GEMINI_3_PRO_PREVIEW: ModelPricing(
        input_per_mtok=1.25,
        output_per_mtok=5.0,
    ),
    ModelName.GEMINI_3_1_PRO_PREVIEW: ModelPricing(
        input_per_mtok=1.25,
        output_per_mtok=5.0,
    ),
}


@dataclass(frozen=True)
class RunConfig:
    """One (model, cache_enabled, use_web_search) combination to run."""

    model_name: ModelName
    cache_enabled: bool
    use_web_search: bool = False


@dataclass
class RunResult:
    """Result of a single model run (or error)."""

    model_name: ModelName
    cache_enabled: bool
    elapsed_s: float
    input_tokens: int
    output_tokens: int
    cache_write_tokens: int
    cache_read_tokens: int
    tool_calls: int
    use_web_search: bool = False
    error: str | None = None
    output: MarketAnalystOutput | None = field(default=None, repr=False)

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens

    def has_usage(self) -> bool:
        """True if any token usage was recorded (mirrors UsageBase.has_values())."""
        return bool(
            self.input_tokens
            or self.output_tokens
            or self.cache_write_tokens
            or self.cache_read_tokens
        )

    def cost(
        self,
        input_per_mtok: float,
        output_per_mtok: float,
        cache_write_per_mtok: float = 0.0,
        cache_read_per_mtok: float = 0.0,
    ) -> CostBreakdown:
        """Return raw USD cost components computed from token counts and per-MTok rates."""
        in_c = (self.input_tokens / 1_000_000) * input_per_mtok
        out_c = (self.output_tokens / 1_000_000) * output_per_mtok
        cw_c = (self.cache_write_tokens / 1_000_000) * cache_write_per_mtok
        cr_c = (self.cache_read_tokens / 1_000_000) * cache_read_per_mtok
        return CostBreakdown(
            input_cost=in_c,
            output_cost=out_c,
            cache_write_cost=cw_c,
            cache_read_cost=cr_c,
            total_cost=in_c + out_c + cw_c + cr_c,
        )


def calc_actual_cost(r: RunResult) -> FormattedCostResult | None:
    """Return formatted cost strings for display, or None if no usage or pricing unavailable."""
    if not r.has_usage():
        return None
    config = AIModelsConfig(model_name=r.model_name)
    provider_id = config.market_analyst.provider
    usage = Usage(
        input_tokens=r.input_tokens,
        output_tokens=r.output_tokens,
        cache_write_tokens=r.cache_write_tokens,
        cache_read_tokens=r.cache_read_tokens,
    )
    try:
        price = calc_price(usage, r.model_name.value, provider_id=provider_id)
        return FormattedCostResult(
            input_cost=f"${float(price.input_price):.4f}",
            output_cost=f"${float(price.output_price):.4f}",
            cache_write_cost="-",
            cache_read_cost="-",
            total_cost=f"${float(price.total_price):.4f}",
            used_fallback=False,
        )
    except LookupError:
        pass
    pricing = MODEL_PRICING_FALLBACK.get(r.model_name)
    if not pricing:
        return None
    breakdown = r.cost(
        pricing.input_per_mtok,
        pricing.output_per_mtok,
        pricing.cache_write_per_mtok,
        pricing.cache_read_per_mtok,
    )
    return FormattedCostResult(
        input_cost=f"${breakdown.input_cost:.4f}",
        output_cost=f"${breakdown.output_cost:.4f}",
        cache_write_cost=f"${breakdown.cache_write_cost:.4f}",
        cache_read_cost=f"${breakdown.cache_read_cost:.4f}",
        total_cost=f"${breakdown.total_cost:.4f}",
        used_fallback=True,
    )


def calc_raw_cost(r: RunResult) -> float | None:
    """Return raw USD total cost, or None if no usage or pricing unavailable."""
    formatted = calc_actual_cost(r)
    if formatted is None:
        return None
    return float(formatted.total_cost.replace("$", ""))
    # Note: FormattedCostResult.total_cost is always "$X.XXXX" when not None


def output_filename(
    timestamp: str,
    model_name: str,
    ticker: str,
    cache_enabled: bool,
    use_web_search: bool = False,
) -> str:
    """Return output filename for a run (same pattern as write_model_output)."""
    safe_model = model_name.replace(".", "-")
    cache_part = "cache" if cache_enabled else "no-cache"
    search_part = "web-search" if use_web_search else "perplexity"
    return f"{timestamp}-{safe_model}-{cache_part}-{search_part}-{ticker}.json"


def write_model_output(
    *,
    run_output: ModelRunOutput,
    timestamp: str,
    output_dir: Path,
    cache_suffix: Literal["cache", "no-cache"] | None = None,
    search_suffix: Literal["web-search", "perplexity"] | None = None,
) -> Path:
    """Serialise the full run output (agent + DCF) to JSON and return the path written.

    When cache_suffix and search_suffix are omitted, the filename is
    {timestamp}-{model}-{ticker}.json. When set, they are included before the ticker.
    """
    safe_model = run_output.model_name.replace(".", "-")
    parts: list[str] = [timestamp, safe_model]
    if cache_suffix is not None:
        parts.append(cache_suffix)
    if search_suffix is not None:
        parts.append(search_suffix)
    parts.append(run_output.ticker)
    filename = "-".join(parts) + ".json"
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / filename
    path.write_text(run_output.model_dump_json(indent=2))
    return path
