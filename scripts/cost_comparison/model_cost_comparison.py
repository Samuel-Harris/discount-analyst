#!/usr/bin/env python3
"""Compare cost and speed across AI models by running the Market Analyst agent.

Usage:
    uv run python scripts/cost_comparison/model_cost_comparison.py
    uv run python scripts/cost_comparison/model_cost_comparison.py --model claude-sonnet-4-5
    uv run python scripts/cost_comparison/model_cost_comparison.py --continue-from claude-opus-4-6
    uv run python scripts/cost_comparison/model_cost_comparison.py --ticker AAPL --risk-free-rate 0.045 --research-report-path path/to/report.md
"""

from __future__ import annotations

import argparse
import asyncio
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

import logfire
from pydantic import BaseModel
from rich.console import Console
from rich.table import Table

from genai_prices import Usage, calc_price

from discount_analyst.shared.ai_models_config import AIModelsConfig, ModelName
from discount_analyst.shared.settings import settings
from discount_analyst.shared.data_types import MarketAnalystOutput
from discount_analyst.dcf_analysis.data_types import (
    DCFAnalysisParameters,
    DCFAnalysisResult,
)
from discount_analyst.dcf_analysis.dcf_analysis import DCFAnalysis
from discount_analyst.market_analyst.market_analyst import create_market_analyst_agent
from discount_analyst.market_analyst.user_prompt import create_user_prompt

# Models that auto-cache (OpenAI, Gemini); no way to disable — skip when --caching disabled.
AUTO_CACHE_MODELS: frozenset[ModelName] = frozenset(
    {
        ModelName.GPT_5_1,
        ModelName.GPT_5_2,
        ModelName.GEMINI_3_PRO_PREVIEW,
        ModelName.GEMINI_3_1_PRO_PREVIEW,
    }
)


console = Console()


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
    """One (model, cache_enabled) combination to run."""

    model_name: ModelName
    cache_enabled: bool


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


def _calc_actual_cost(r: RunResult) -> FormattedCostResult | None:
    """Return formatted cost strings for display, or None if no usage or pricing is unavailable."""
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


_SCRIPT_DIR = Path(__file__).resolve().parent


def _default_research_report_path() -> str:
    return str(_SCRIPT_DIR / "inputs" / "amzn.md")


def _outputs_dir() -> Path:
    d = _SCRIPT_DIR / "outputs"
    d.mkdir(exist_ok=True)
    return d


def write_model_output(
    run_output: ModelRunOutput, timestamp: str, *, cache_suffix: str = "cache"
) -> Path:
    """Serialise the full run output (agent + DCF) to JSON and return the path written."""
    safe_model = run_output.model_name.replace(".", "-")
    filename = f"{timestamp}-{safe_model}-{cache_suffix}-{run_output.ticker}.json"
    path = _outputs_dir() / filename
    path.write_text(run_output.model_dump_json(indent=2))
    return path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run Market Analyst across one or more models and compare cost and speed."
    )
    parser.add_argument(
        "--model",
        type=lambda s: ModelName(s),
        default=None,
        choices=[e.value for e in ModelName],
        help="Model to run (default: all models).",
    )
    parser.add_argument(
        "--continue-from",
        type=lambda s: ModelName(s),
        default=None,
        choices=[e.value for e in ModelName],
        metavar="MODEL",
        help=(
            "Skip all models that appear before MODEL in the configured order and "
            "run from MODEL onwards. Cannot be combined with --model."
        ),
    )
    parser.add_argument(
        "--ticker",
        type=str,
        default="AMZN",
        help="Stock ticker for the run (default: AMZN).",
    )
    parser.add_argument(
        "--risk-free-rate",
        type=float,
        default=0.045,
        help="Risk-free rate for DCF WACC calculation, as a decimal (default: 0.045).",
    )
    parser.add_argument(
        "--research-report-path",
        type=str,
        default=None,
        help="Path to research report markdown (default: scripts/cost_comparison/inputs/amzn.md).",
    )
    parser.add_argument(
        "--caching",
        choices=("enabled", "disabled", "both"),
        default="both",
        help=(
            "Prompt caching: enabled (all with cache), disabled (Anthropic no-cache only; "
            "OpenAI/Gemini skipped), both (default: Anthropic cache+no-cache, others once with cache)."
        ),
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print which configs would run (model, cache mode, output file) and exit without running.",
    )
    args = parser.parse_args()
    if args.model is not None and args.continue_from is not None:
        parser.error("--model and --continue-from are mutually exclusive.")
    if args.research_report_path is None:
        args.research_report_path = _default_research_report_path()
    return args


def load_research_report(path: str) -> str:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Research report not found: {path}")
    return p.read_text()


def build_run_configs(caching: str, models_to_run: list[ModelName]) -> list[RunConfig]:
    """Build list of (model, cache_enabled) configs from --caching and model list."""
    configs: list[RunConfig] = []
    for model_name in models_to_run:
        is_auto_cache = model_name in AUTO_CACHE_MODELS
        if caching == "enabled":
            configs.append(RunConfig(model_name=model_name, cache_enabled=True))
        elif caching == "disabled":
            if is_auto_cache:
                console.print(
                    f"  [yellow]Skipping {model_name.value} (auto-caches, no disable)[/yellow]"
                )
            else:
                configs.append(RunConfig(model_name=model_name, cache_enabled=False))
        else:  # both
            if is_auto_cache:
                configs.append(RunConfig(model_name=model_name, cache_enabled=True))
            else:
                configs.append(RunConfig(model_name=model_name, cache_enabled=True))
                configs.append(RunConfig(model_name=model_name, cache_enabled=False))
    return configs


def _output_filename(
    timestamp: str, model_name: str, ticker: str, cache_enabled: bool
) -> str:
    """Return output filename for a run (same pattern as write_model_output)."""
    safe_model = model_name.replace(".", "-")
    suffix = "cache" if cache_enabled else "no-cache"
    return f"{timestamp}-{safe_model}-{suffix}-{ticker}.json"


async def run_one_model(
    model_name: ModelName,
    user_prompt: str,
    cache_enabled: bool,
) -> RunResult:
    """Run the Market Analyst agent for one model and return timing + usage."""
    config = AIModelsConfig(model_name=model_name, cache_messages=cache_enabled)
    agent = create_market_analyst_agent(config)
    usage_limits = config.market_analyst.usage_limits

    start = time.perf_counter()
    try:
        async with agent.run_stream(
            user_prompt, usage_limits=usage_limits
        ) as streamed_run:
            async for _ in streamed_run.stream_output(debounce_by=None):
                pass  # drain stream; Anthropic requires streaming for long requests
        output = await streamed_run.get_output()
        usage = streamed_run.usage()
        elapsed_s = time.perf_counter() - start
        return RunResult(
            model_name=model_name,
            cache_enabled=cache_enabled,
            elapsed_s=elapsed_s,
            input_tokens=usage.input_tokens,
            output_tokens=usage.output_tokens,
            cache_write_tokens=usage.cache_write_tokens,
            cache_read_tokens=usage.cache_read_tokens,
            tool_calls=usage.tool_calls,
            error=None,
            output=output,
        )
    except Exception as e:  # noqa: BLE001
        elapsed_s = time.perf_counter() - start
        return RunResult(
            model_name=model_name,
            cache_enabled=cache_enabled,
            elapsed_s=elapsed_s,
            input_tokens=0,
            output_tokens=0,
            cache_write_tokens=0,
            cache_read_tokens=0,
            tool_calls=0,
            error=str(e),
            output=None,
        )


async def main() -> None:
    args = parse_args()

    all_models = list(ModelName)
    if args.model is not None:
        models_to_run: list[ModelName] = [args.model]
    elif args.continue_from is not None:
        start_idx = all_models.index(args.continue_from)
        models_to_run = all_models[start_idx:]
    else:
        models_to_run = all_models

    run_configs = build_run_configs(args.caching, models_to_run)

    if args.dry_run:
        timestamp = datetime.now().strftime("%Y%m%dT%H%M%S")
        table = Table(
            title="Dry run: configs that would be executed",
            show_header=True,
            header_style="bold magenta",
        )
        table.add_column("Model", style="cyan", no_wrap=True)
        table.add_column("Cache", justify="center")
        table.add_column("Output File", style="dim")
        for cfg in run_configs:
            fname = _output_filename(
                timestamp, cfg.model_name.value, args.ticker, cfg.cache_enabled
            )
            table.add_row(
                cfg.model_name.value,
                "yes" if cfg.cache_enabled else "no",
                fname,
            )
        console.print(table)
        return

    logfire.configure(token=settings.pydantic.logfire_api_key, scrubbing=False)
    logfire.instrument_pydantic_ai()

    research_report = load_research_report(args.research_report_path)
    user_prompt = create_user_prompt(
        ticker=args.ticker, research_report=research_report
    )

    console.print(
        f"Running Market Analyst for [bold]{args.ticker}[/bold] "
        f"across {len(run_configs)} config(s) (report: {args.research_report_path})."
    )

    timestamp = datetime.now().strftime("%Y%m%dT%H%M%S")

    results: list[RunResult] = []
    for cfg in run_configs:
        cache_label = "cache" if cfg.cache_enabled else "no-cache"
        console.print(
            f"  Running [cyan]{cfg.model_name.value}[/cyan] ([dim]{cache_label}[/dim])..."
        )
        result = await run_one_model(cfg.model_name, user_prompt, cfg.cache_enabled)
        results.append(result)
        if result.error:
            console.print(f"    [red]Error: {result.error}[/red]")
        else:
            console.print(
                f"    [green]{result.elapsed_s:.1f}s[/green] | "
                f"in={result.input_tokens} out={result.output_tokens} "
                f"| tools={result.tool_calls}"
            )
            if result.output is not None:
                dcf_result: DCFAnalysisResult | None = None
                dcf_error: str | None = None
                try:
                    dcf_params = DCFAnalysisParameters(
                        stock_data=result.output.stock_data,
                        stock_assumptions=result.output.stock_assumptions,
                        risk_free_rate=args.risk_free_rate,
                    )
                    dcf_result = DCFAnalysis(dcf_params).dcf_analysis()
                    current_price = (
                        result.output.stock_data.market_cap
                        / result.output.stock_data.n_shares_outstanding
                    )
                    upside = (
                        dcf_result.intrinsic_share_price - current_price
                    ) / current_price
                    sign = "+" if upside >= 0 else ""
                    color = "green" if upside >= 0 else "red"
                    console.print(
                        f"    DCF: intrinsic [bold]{dcf_result.intrinsic_share_price:.2f}[/bold] "
                        f"vs market [{color}]{current_price:.2f}[/{color}] "
                        f"([{color}]{sign}{upside:.1%}[/{color}])"
                    )
                except Exception as exc:  # noqa: BLE001
                    dcf_error = str(exc)
                    console.print(f"    [yellow]DCF error: {dcf_error}[/yellow]")

                run_output = ModelRunOutput(
                    ticker=args.ticker,
                    model_name=result.model_name.value,
                    risk_free_rate=args.risk_free_rate,
                    market_analyst=result.output,
                    dcf_result=dcf_result,
                    dcf_error=dcf_error,
                )
                cache_suffix = "cache" if result.cache_enabled else "no-cache"
                out_path = write_model_output(
                    run_output, timestamp, cache_suffix=cache_suffix
                )
                console.print(f"    Saved [dim]{out_path}[/dim]")

    # Table 1: Speed & Tokens
    table_tokens = Table(
        title="Speed & Tokens",
        show_header=True,
        header_style="bold magenta",
    )
    table_tokens.add_column("Model", style="cyan", no_wrap=True)
    table_tokens.add_column("Cache", justify="center")
    table_tokens.add_column("Time (s)", justify="right")
    table_tokens.add_column("Input Tok", justify="right")
    table_tokens.add_column("Output Tok", justify="right")
    table_tokens.add_column("Cache Write Tok", justify="right")
    table_tokens.add_column("Cache Read Tok", justify="right")
    table_tokens.add_column("Tool Calls", justify="right")
    table_tokens.add_column("Status", style="red")

    for r in results:
        status = r.error or "OK"
        table_tokens.add_row(
            r.model_name.value,
            "yes" if r.cache_enabled else "no",
            f"{r.elapsed_s:.2f}",
            f"{r.input_tokens:,}",
            f"{r.output_tokens:,}",
            f"{r.cache_write_tokens:,}",
            f"{r.cache_read_tokens:,}",
            str(r.tool_calls),
            status,
        )

    console.print()
    console.print(table_tokens)

    # Table 2: Cost Breakdown
    table_cost = Table(
        title="Cost Breakdown",
        show_header=True,
        header_style="bold magenta",
    )
    table_cost.add_column("Model", style="cyan", no_wrap=True)
    table_cost.add_column("Cache", justify="center")
    table_cost.add_column("Input Cost", justify="right")
    table_cost.add_column("Output Cost", justify="right")
    table_cost.add_column("Cache Write", justify="right")
    table_cost.add_column("Cache Read", justify="right")
    table_cost.add_column("Total Cost", justify="right")
    table_cost.add_column("Pricing", justify="center")

    for r in results:
        if r.error:
            table_cost.add_row(
                r.model_name.value,
                "yes" if r.cache_enabled else "no",
                "-",
                "-",
                "-",
                "-",
                "-",
                "-",
            )
            continue
        cost_result = _calc_actual_cost(r)
        if cost_result is None:
            if not r.has_usage():
                table_cost.add_row(
                    r.model_name.value,
                    "yes" if r.cache_enabled else "no",
                    "-",
                    "-",
                    "-",
                    "-",
                    "[dim]no usage[/dim]",
                    "-",
                )
            else:
                table_cost.add_row(
                    r.model_name.value,
                    "yes" if r.cache_enabled else "no",
                    "?",
                    "?",
                    "?",
                    "?",
                    "?",
                    "-",
                )
            continue
        pricing_source = (
            "[yellow]fallback[/yellow]" if cost_result.used_fallback else "genai-prices"
        )
        table_cost.add_row(
            r.model_name.value,
            "yes" if r.cache_enabled else "no",
            cost_result.input_cost,
            cost_result.output_cost,
            cost_result.cache_write_cost,
            cost_result.cache_read_cost,
            cost_result.total_cost,
            pricing_source,
        )

    console.print()
    console.print(table_cost)


if __name__ == "__main__":
    asyncio.run(main())
