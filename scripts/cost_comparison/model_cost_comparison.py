#!/usr/bin/env python3
"""Compare cost and speed across AI models by running the Market Analyst agent.

Usage:
    uv run python scripts/cost_comparison/model_cost_comparison.py
    uv run python scripts/cost_comparison/model_cost_comparison.py --model claude-sonnet-4-5
    uv run python scripts/cost_comparison/model_cost_comparison.py --ticker AAPL --research-report-path path/to/report.md
"""

from __future__ import annotations

import argparse
import asyncio
import time
from dataclasses import dataclass
from pathlib import Path

from rich.console import Console
from rich.table import Table

from genai_prices import Usage, calc_price

from discount_analyst.shared.ai_models_config import AIModelsConfig, ModelName
from discount_analyst.market_analyst.market_analyst import create_market_analyst_agent
from discount_analyst.market_analyst.user_prompt import create_user_prompt


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


@dataclass
class RunResult:
    """Result of a single model run (or error)."""

    model_name: ModelName
    elapsed_s: float
    input_tokens: int
    output_tokens: int
    cache_write_tokens: int
    cache_read_tokens: int
    tool_calls: int
    error: str | None = None

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


def _default_research_report_path() -> str:
    repo_root = Path(__file__).resolve().parent.parent.parent
    return str(repo_root / "scripts" / "cost_comparison" / "amzn.md")


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
        "--ticker",
        type=str,
        default="AMZN",
        help="Stock ticker for the run (default: AMZN).",
    )
    parser.add_argument(
        "--research-report-path",
        type=str,
        default=None,
        help="Path to research report markdown (default: scripts/cost_comparison/amzn.md).",
    )
    args = parser.parse_args()
    if args.research_report_path is None:
        args.research_report_path = _default_research_report_path()
    return args


def load_research_report(path: str) -> str:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Research report not found: {path}")
    return p.read_text()


async def run_one_model(
    model_name: ModelName,
    user_prompt: str,
) -> RunResult:
    """Run the Market Analyst agent for one model and return timing + usage."""
    config = AIModelsConfig(model_name=model_name)
    agent = create_market_analyst_agent(config)
    usage_limits = config.market_analyst.usage_limits

    start = time.perf_counter()
    try:
        async with agent.iter(user_prompt, usage_limits=usage_limits) as agent_run:
            async for _ in agent_run:
                pass
        usage = agent_run.usage()
        elapsed_s = time.perf_counter() - start
        return RunResult(
            model_name=model_name,
            elapsed_s=elapsed_s,
            input_tokens=usage.input_tokens,
            output_tokens=usage.output_tokens,
            cache_write_tokens=usage.cache_write_tokens,
            cache_read_tokens=usage.cache_read_tokens,
            tool_calls=usage.tool_calls,
            error=None,
        )
    except Exception as e:  # noqa: BLE001
        elapsed_s = time.perf_counter() - start
        return RunResult(
            model_name=model_name,
            elapsed_s=elapsed_s,
            input_tokens=0,
            output_tokens=0,
            cache_write_tokens=0,
            cache_read_tokens=0,
            tool_calls=0,
            error=str(e),
        )


async def main() -> None:
    args = parse_args()
    research_report = load_research_report(args.research_report_path)
    user_prompt = create_user_prompt(
        ticker=args.ticker, research_report=research_report
    )

    models_to_run: list[ModelName] = (
        [args.model] if args.model is not None else list(ModelName)
    )

    console.print(
        f"Running Market Analyst for [bold]{args.ticker}[/bold] "
        f"across {len(models_to_run)} model(s) (report: {args.research_report_path})."
    )

    results: list[RunResult] = []
    for model_name in models_to_run:
        console.print(f"  Running [cyan]{model_name.value}[/cyan]...")
        result = await run_one_model(model_name, user_prompt)
        results.append(result)
        if result.error:
            console.print(f"    [red]Error: {result.error}[/red]")
        else:
            console.print(
                f"    [green]{result.elapsed_s:.1f}s[/green] | "
                f"in={result.input_tokens} out={result.output_tokens} "
                f"| tools={result.tool_calls}"
            )

    # Table 1: Speed & Tokens
    table_tokens = Table(
        title="Speed & Tokens",
        show_header=True,
        header_style="bold magenta",
    )
    table_tokens.add_column("Model", style="cyan", no_wrap=True)
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
