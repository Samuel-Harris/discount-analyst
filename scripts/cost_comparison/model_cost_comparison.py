#!/usr/bin/env python3
"""Compare cost and speed across AI models by running the Appraiser agent.

Usage:
    uv run python scripts/cost_comparison/model_cost_comparison.py --ticker AMZN
    uv run python scripts/cost_comparison/model_cost_comparison.py --ticker AAPL --model claude-sonnet-4-5
    uv run python scripts/cost_comparison/model_cost_comparison.py --ticker AMZN --continue-from claude-opus-4-6
    uv run python scripts/cost_comparison/model_cost_comparison.py --ticker AAPL --research-report-path path/to/report.md --surveyor-report-path path/to/surveyor-report.json
    uv run python scripts/cost_comparison/model_cost_comparison.py --ticker AMZN --web-search built-in
    uv run python scripts/cost_comparison/model_cost_comparison.py --ticker AMZN --web-search both
    uv run python scripts/cost_comparison/model_cost_comparison.py --ticker AMZN --no-mcp
"""

from __future__ import annotations

import argparse
import asyncio
import time
from datetime import datetime
from pathlib import Path

import logfire
from rich.console import Console
from rich.table import Table

from discount_analyst.shared.config.ai_models_config import AIModelsConfig, ModelName
from discount_analyst.shared.config.settings import settings

from discount_analyst.dcf_analysis.data_types import (
    DCFAnalysisParameters,
    DCFAnalysisResult,
)
from discount_analyst.dcf_analysis.dcf_analysis import DCFAnalysis
from discount_analyst.agents.appraiser.appraiser import create_appraiser_agent
from discount_analyst.agents.appraiser.user_prompt import create_user_prompt
from discount_analyst.shared.http.rate_limit_client import stream_with_retries

from discount_analyst.shared.schemas.surveyor import SurveyorCandidate
from scripts.shared.constants import AUTO_CACHE_MODELS
from scripts.shared.cost import RunConfig, RunResult, calc_actual_cost
from scripts.shared.outputs import output_filename, write_model_output
from scripts.shared.schemas.run_outputs import AppraiserRunOutput
from scripts.shared.usage import extract_turn_usage

console = Console()

_SCRIPTS_DIR = Path(__file__).resolve().parent


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run Appraiser across one or more models and compare cost and speed."
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
        default=None,
        required=True,
        help="Stock ticker for the run.",
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
        help="Path to research report markdown (optional; defaults to inputs/{ticker}.md).",
    )
    parser.add_argument(
        "--surveyor-report-path",
        type=str,
        default=None,
        help=(
            "Path to surveyor-report.json (one SurveyorCandidate). "
            "Optional; defaults to inputs/{ticker}-surveyor-report.json."
        ),
    )
    parser.add_argument(
        "--caching",
        choices=("enabled", "disabled", "both"),
        default="enabled",
        help=(
            "Prompt caching: enabled (default: all models with cache), "
            "disabled (Anthropic no-cache only; OpenAI/Gemini skipped), "
            "both (Anthropic cache+no-cache, others once with cache). "
            "Use --no-cache-claude to add no-cache Claude variants on top of the default."
        ),
    )
    parser.add_argument(
        "--web-search",
        choices=("perplexity", "built-in", "both"),
        default="perplexity",
        help=(
            "Search tool to use: perplexity (default, Perplexity-backed tools), "
            "built-in (model-native WebSearchTool + WebFetchTool, no Perplexity), "
            "both (run a perplexity variant and a built-in variant for every model)."
        ),
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print which configs would run (model, cache mode, output file) and exit without running.",
    )
    parser.add_argument(
        "--no-mcp",
        action="store_true",
        help=(
            "Do not register EODHD/FMP MCP toolsets (required for Google models; "
            "optional for Anthropic/OpenAI)."
        ),
    )
    args = parser.parse_args()
    if args.model is not None and args.continue_from is not None:
        parser.error("--model and --continue-from are mutually exclusive.")
    if args.research_report_path is None:
        args.research_report_path = str(
            _SCRIPTS_DIR / "inputs" / f"{args.ticker.lower()}.md"
        )
    if args.surveyor_report_path is None:
        args.surveyor_report_path = str(
            _SCRIPTS_DIR / "inputs" / f"{args.ticker.lower()}-surveyor-report.json"
        )
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


def load_surveyor_candidate(path: str) -> SurveyorCandidate:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Surveyor report not found: {path}")
    return SurveyorCandidate.model_validate_json(p.read_text())


def build_run_configs(
    caching: str,
    models_to_run: list[ModelName],
    *,
    web_search: str = "perplexity",
) -> list[RunConfig]:
    """Build the ordered list of RunConfigs from CLI flags and model list.

    Base configs (Perplexity) are determined by --caching. Built-in web-search
    variants are always cached; use --caching both to also get no-cache runs for
    Anthropic models.

    Args:
        caching: One of "enabled", "disabled", "both".
        models_to_run: Ordered list of models to include.
        web_search: One of "perplexity" (default), "built-in", or "both".
            "perplexity"  — only Perplexity-backed runs.
            "built-in"    — only model-native WebSearchTool runs (no Perplexity).
            "both"        — a Perplexity run and a built-in run per model.
    """
    base_configs: list[RunConfig] = []
    for model_name in models_to_run:
        is_auto_cache = model_name in AUTO_CACHE_MODELS
        if caching == "enabled":
            base_configs.append(RunConfig(model_name=model_name, cache_enabled=True))
        elif caching == "disabled":
            if is_auto_cache:
                console.print(
                    f"  [yellow]Skipping {model_name.value} (auto-caches, no disable)[/yellow]"
                )
            else:
                base_configs.append(
                    RunConfig(model_name=model_name, cache_enabled=False)
                )
        else:  # both
            if is_auto_cache:
                base_configs.append(
                    RunConfig(model_name=model_name, cache_enabled=True)
                )
            else:
                base_configs.append(
                    RunConfig(model_name=model_name, cache_enabled=True)
                )
                base_configs.append(
                    RunConfig(model_name=model_name, cache_enabled=False)
                )

    # Built-in web-search variants: one cached run per unique model.
    builtin_configs: list[RunConfig] = []
    seen: set[ModelName] = set()
    for cfg in base_configs:
        if cfg.model_name not in seen:
            builtin_configs.append(
                RunConfig(
                    model_name=cfg.model_name,
                    cache_enabled=True,
                    use_web_search=True,
                )
            )
            seen.add(cfg.model_name)

    if web_search == "perplexity":
        return base_configs
    elif web_search == "built-in":
        return builtin_configs
    else:  # both
        return list(base_configs) + builtin_configs


async def run_one_model(
    model_name: ModelName,
    user_prompt: str,
    cache_enabled: bool,
    *,
    use_web_search: bool = False,
    use_mcp_financial_data: bool = True,
) -> RunResult:
    """Run the Market Analyst agent for one model and return timing + usage."""
    config = AIModelsConfig(model_name=model_name, cache_messages=cache_enabled)
    agent = create_appraiser_agent(
        config,
        use_perplexity=not use_web_search,
        use_mcp_financial_data=use_mcp_financial_data,
    )
    usage_limits = config.model.usage_limits

    start = time.perf_counter()
    try:
        async with stream_with_retries(
            agent=agent, user_prompt=user_prompt, usage_limits=usage_limits
        ) as streamed_run:
            async for _ in streamed_run.stream_output(debounce_by=None):
                pass  # drain stream; Anthropic requires streaming for long requests
            output = await streamed_run.get_output()
            usage = streamed_run.usage()
            turn_usage = extract_turn_usage(streamed_run.all_messages())
        elapsed_s = time.perf_counter() - start
        return RunResult(
            model_name=model_name,
            cache_enabled=cache_enabled,
            use_web_search=use_web_search,
            elapsed_s=elapsed_s,
            input_tokens=usage.input_tokens,
            output_tokens=usage.output_tokens,
            cache_write_tokens=usage.cache_write_tokens,
            cache_read_tokens=usage.cache_read_tokens,
            tool_calls=usage.tool_calls,
            error=None,
            output=output,
            turn_usage=turn_usage,
        )
    except Exception as e:  # noqa: BLE001
        elapsed_s = time.perf_counter() - start
        error_type = type(e).__name__
        error_msg = str(e)
        error_display = f"{error_type}: {error_msg}" if error_msg else error_type
        logfire.error(
            "Model run failed",
            model=model_name.value,
            cache_enabled=cache_enabled,
            error=error_msg,
            error_type=error_type,
        )
        return RunResult(
            model_name=model_name,
            cache_enabled=cache_enabled,
            use_web_search=use_web_search,
            elapsed_s=elapsed_s,
            input_tokens=0,
            output_tokens=0,
            cache_write_tokens=0,
            cache_read_tokens=0,
            tool_calls=0,
            error=error_display,
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

    run_configs = build_run_configs(
        args.caching,
        models_to_run,
        web_search=args.web_search,
    )

    if args.dry_run:
        timestamp = datetime.now().strftime("%Y%m%dT%H%M%S")
        table = Table(
            title="Dry run: configs that would be executed",
            show_header=True,
            header_style="bold magenta",
        )
        table.add_column("Model", style="cyan", no_wrap=True)
        table.add_column("Cache", justify="center")
        table.add_column("Web Search", justify="center")
        table.add_column("MCP", justify="center")
        table.add_column("Output File", style="dim")
        mcp_label = "no" if args.no_mcp else "yes"
        for cfg in run_configs:
            fname = output_filename(
                timestamp,
                cfg.model_name.value,
                args.ticker,
                cfg.cache_enabled,
                cfg.use_web_search,
            )
            table.add_row(
                cfg.model_name.value,
                "yes" if cfg.cache_enabled else "no",
                "yes" if cfg.use_web_search else "no",
                mcp_label,
                fname,
            )
        console.print(table)
        return

    logfire.configure(token=settings.pydantic.logfire_api_key, scrubbing=False)
    logfire.instrument_pydantic_ai()

    research_report = load_research_report(args.research_report_path)
    surveyor_candidate = load_surveyor_candidate(args.surveyor_report_path)
    user_prompt = create_user_prompt(
        ticker=args.ticker,
        research_report=research_report,
        surveyor_candidate=surveyor_candidate,
    )

    console.print(
        f"Running Market Analyst for [bold]{args.ticker}[/bold] "
        f"across {len(run_configs)} config(s) "
        f"(report: {args.research_report_path}, surveyor: {args.surveyor_report_path})."
    )

    timestamp = datetime.now().strftime("%Y%m%dT%H%M%S")

    results: list[RunResult] = []
    for cfg in run_configs:
        cache_label = "cache" if cfg.cache_enabled else "no-cache"
        search_label = "web-search" if cfg.use_web_search else "perplexity"
        console.print(
            f"  Running [cyan]{cfg.model_name.value}[/cyan] "
            f"([dim]{cache_label}[/dim], [dim]{search_label}[/dim])..."
        )
        result = await run_one_model(
            cfg.model_name,
            user_prompt,
            cfg.cache_enabled,
            use_web_search=cfg.use_web_search,
            use_mcp_financial_data=not args.no_mcp,
        )
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

                run_output = AppraiserRunOutput(
                    ticker=args.ticker,
                    model_name=result.model_name.value,
                    risk_free_rate=args.risk_free_rate,
                    appraiser=result.output,
                    dcf_result=dcf_result,
                    dcf_error=dcf_error,
                    elapsed_s=result.elapsed_s,
                    input_tokens=result.input_tokens,
                    output_tokens=result.output_tokens,
                    cache_write_tokens=result.cache_write_tokens,
                    cache_read_tokens=result.cache_read_tokens,
                    tool_calls=result.tool_calls,
                    turn_usage=result.turn_usage,
                )
                cache_suffix = "cache" if result.cache_enabled else "no-cache"
                search_suffix = "web-search" if cfg.use_web_search else "perplexity"
                output_dir = _SCRIPTS_DIR / "outputs"
                out_path = write_model_output(
                    run_output=run_output,
                    timestamp=timestamp,
                    cache_suffix=cache_suffix,
                    search_suffix=search_suffix,
                    output_dir=output_dir,
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
    table_tokens.add_column("Search", justify="center")
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
            "web" if r.use_web_search else "perplexity",
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
    table_cost.add_column("Search", justify="center")
    table_cost.add_column("Input Cost", justify="right")
    table_cost.add_column("Output Cost", justify="right")
    table_cost.add_column("Cache Write", justify="right")
    table_cost.add_column("Cache Read", justify="right")
    table_cost.add_column("Total Cost", justify="right")
    table_cost.add_column("Pricing", justify="center")

    for r in results:
        search_col = "web" if r.use_web_search else "perplexity"
        if r.error:
            table_cost.add_row(
                r.model_name.value,
                "yes" if r.cache_enabled else "no",
                search_col,
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
                    search_col,
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
                    search_col,
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
            search_col,
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
