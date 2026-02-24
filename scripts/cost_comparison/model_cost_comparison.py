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
import sys
import time
from datetime import datetime
from pathlib import Path

import logfire
from rich.console import Console
from rich.table import Table

from discount_analyst.shared.ai_models_config import AIModelsConfig, ModelName
from discount_analyst.shared.settings import settings
from discount_analyst.dcf_analysis.data_types import (
    DCFAnalysisParameters,
    DCFAnalysisResult,
)
from discount_analyst.dcf_analysis.dcf_analysis import DCFAnalysis
from discount_analyst.market_analyst.market_analyst import create_market_analyst_agent
from discount_analyst.market_analyst.user_prompt import create_user_prompt

sys.path.insert(0, str(Path(__file__).resolve().parent))
from shared import (  # noqa: E402
    AUTO_CACHE_MODELS,
    ModelRunOutput,
    RunConfig,
    RunResult,
    calc_actual_cost,
    output_filename,
    write_model_output,
)

console = Console()

_SCRIPT_DIR = Path(__file__).resolve().parent


def _default_research_report_path() -> str:
    return str(_SCRIPT_DIR / "inputs" / "amzn.md")


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
        default=0.037276,
        help="Risk-free rate for DCF WACC calculation, as a decimal (default: 0.037276, the UK risk-free rate as of 2026-02-24).",
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
    if not (0 < args.risk_free_rate <= 0.15):
        parser.error(
            f"--risk-free-rate must be a decimal between 0 and 0.15 (e.g. 0.045 for 4.5%). "
            f"Got {args.risk_free_rate}. Did you pass a percentage? Use 0.0373 for 3.73%."
        )
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
            fname = output_filename(
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
                    elapsed_s=result.elapsed_s,
                    input_tokens=result.input_tokens,
                    output_tokens=result.output_tokens,
                    cache_write_tokens=result.cache_write_tokens,
                    cache_read_tokens=result.cache_read_tokens,
                    tool_calls=result.tool_calls,
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
        cost_result = calc_actual_cost(r)
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
