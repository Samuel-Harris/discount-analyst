"""Shared data types, constants, and helpers for scripts (cost comparison, DCF analysis)."""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from pydantic import AliasChoices, BaseModel, ConfigDict, Field
from pydantic_ai.messages import ModelMessage, ModelResponse

from genai_prices import Usage, calc_price

from discount_analyst.appraiser.data_types import AppraiserOutput
from discount_analyst.dcf_analysis.data_types import DCFAnalysisResult
from discount_analyst.shared.config.ai_models_config import AIModelsConfig, ModelName
from discount_analyst.shared.models.data_types import SurveyorOutput

# Models that auto-cache (OpenAI, Gemini); no way to disable — skip when --caching disabled.
AUTO_CACHE_MODELS: frozenset[ModelName] = frozenset(
    {
        ModelName.GPT_5_1,
        ModelName.GPT_5_2,
        ModelName.GPT_5_4,
        ModelName.GEMINI_3_PRO_PREVIEW,
        ModelName.GEMINI_3_1_PRO_PREVIEW,
    }
)


@dataclass(frozen=True, slots=True)
class AgentCliDefaults:
    """Default model and web-search backend for `scripts/agents/` entry points."""

    model: ModelName
    use_perplexity: bool


DEFAULT_AGENT_CLI_DEFAULTS = AgentCliDefaults(
    model=ModelName.GPT_5_1,
    use_perplexity=False,
)


def add_agent_cli_model_argument(
    parser: argparse.ArgumentParser,
    *,
    default_override: AgentCliDefaults | None = None,
) -> None:
    """Register ``--model`` using shared agent CLI defaults."""
    resolved_defaults = default_override or DEFAULT_AGENT_CLI_DEFAULTS
    parser.add_argument(
        "--model",
        type=ModelName,
        choices=[e.value for e in ModelName],
        default=resolved_defaults.model,
        help=f"AI model to use (default: {resolved_defaults.model})",
    )


def add_agent_cli_web_search_arguments(
    parser: argparse.ArgumentParser,
    *,
    default_override: AgentCliDefaults | None = None,
) -> None:
    """Register ``--perplexity`` / ``--no-perplexity`` (mutually exclusive).

    Namespace attribute: ``use_perplexity``.
    """
    resolved_defaults = default_override or DEFAULT_AGENT_CLI_DEFAULTS
    parser.set_defaults(use_perplexity=resolved_defaults.use_perplexity)
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--perplexity",
        action="store_true",
        dest="use_perplexity",
        help="Use Perplexity API for web_search and sec_filings_search.",
    )
    group.add_argument(
        "--no-perplexity",
        action="store_false",
        dest="use_perplexity",
        help="Use model-native web search tools (default).",
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


class TurnUsage(BaseModel):
    """Usage stats for one model-response turn within a run."""

    turn: int = Field(ge=1)
    input_tokens: int = Field(ge=0)
    output_tokens: int = Field(ge=0)
    cache_write_tokens: int = Field(default=0, ge=0)
    cache_read_tokens: int = Field(default=0, ge=0)
    total_tokens: int = Field(ge=0)
    cumulative_input_tokens: int = Field(ge=0)
    cumulative_output_tokens: int = Field(ge=0)
    cumulative_total_tokens: int = Field(ge=0)


def _default_turn_usage_list() -> list[TurnUsage]:
    return []


class ModelRunOutput(BaseModel):
    """Complete serialisable record for one model run written to outputs/."""

    model_config = ConfigDict(populate_by_name=True)

    ticker: str
    model_name: str
    risk_free_rate: float
    appraiser: AppraiserOutput = Field(
        validation_alias=AliasChoices("market_analyst", "appraiser"),
    )
    dcf_result: DCFAnalysisResult | None = None
    dcf_error: str | None = None
    elapsed_s: float
    input_tokens: int
    output_tokens: int
    cache_write_tokens: int
    cache_read_tokens: int
    tool_calls: int
    turn_usage: list[TurnUsage] = Field(default_factory=_default_turn_usage_list)


class SurveyorRunOutput(BaseModel):
    """Complete serialisable record for one Surveyor run written to outputs/."""

    model_name: str
    elapsed_s: float
    input_tokens: int
    output_tokens: int
    turn_usage: list[TurnUsage] = Field(default_factory=_default_turn_usage_list)
    output: SurveyorOutput


def extract_turn_usage(messages: list[ModelMessage]) -> list[TurnUsage]:
    """Extract per-turn usage by walking ModelResponse messages in order."""
    turns: list[TurnUsage] = []
    cumulative_input = 0
    cumulative_output = 0
    cumulative_total = 0

    for message in messages:
        if not isinstance(message, ModelResponse):
            continue

        usage = message.usage
        input_tokens = getattr(usage, "input_tokens", 0)
        output_tokens = getattr(usage, "output_tokens", 0)
        cache_write_tokens = getattr(usage, "cache_write_tokens", 0)
        cache_read_tokens = getattr(usage, "cache_read_tokens", 0)
        total_tokens = getattr(usage, "total_tokens", input_tokens + output_tokens)

        cumulative_input += input_tokens
        cumulative_output += output_tokens
        cumulative_total += total_tokens
        turns.append(
            TurnUsage(
                turn=len(turns) + 1,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cache_write_tokens=cache_write_tokens,
                cache_read_tokens=cache_read_tokens,
                total_tokens=total_tokens,
                cumulative_input_tokens=cumulative_input,
                cumulative_output_tokens=cumulative_output,
                cumulative_total_tokens=cumulative_total,
            )
        )

    return turns


def write_surveyor_output(
    *,
    run_output: SurveyorRunOutput,
    timestamp: str,
    output_dir: Path,
) -> Path:
    """Serialise the Surveyor run output to JSON and return the path written.

    Filename format: {timestamp}-surveyor-{model}.json
    """
    safe_model = run_output.model_name.replace(".", "-")
    filename = f"{timestamp}-surveyor-{safe_model}.json"
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / filename
    path.write_text(run_output.model_dump_json(indent=2))
    return path


# Fallback pricing when genai_prices does not have the model (e.g. very new models).
# Update as needed; genai_prices is used for actual cost when the model is in its snapshot.
MODEL_PRICING_FALLBACK: dict[ModelName, ModelPricing] = {}


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
    output: AppraiserOutput | None = field(default=None, repr=False)
    turn_usage: list[TurnUsage] = field(default_factory=_default_turn_usage_list)

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
    provider_id = config.model.provider
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
