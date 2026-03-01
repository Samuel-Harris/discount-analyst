#!/usr/bin/env python3
"""Pretty-print all saved run results for a given ticker.

Usage:
    uv run python scripts/cost_comparison/view_ticker_results.py AMZN
    uv run python scripts/cost_comparison/view_ticker_results.py AAPL --detail
    uv run python scripts/cost_comparison/view_ticker_results.py AMZN --compare-cache
    uv run python scripts/cost_comparison/view_ticker_results.py AMZN --compare-cost
    uv run python scripts/cost_comparison/view_ticker_results.py AMZN --compare-web-search
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import NamedTuple

from rich.columns import Columns
from rich.console import Console, Group as RichGroup
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from scripts.shared import (
    ModelRunOutput,
    ModelName,
    RunResult,
    calc_actual_cost,
    calc_raw_cost,
)

console = Console()

_OUTPUTS_DIR = Path(__file__).resolve().parent / "outputs"


class ParsedFilename(NamedTuple):
    """Metadata extracted from an output filename."""

    timestamp: str
    cache_mode: str
    search_mode: str
    display_date: str


class ModelSearchKey(NamedTuple):
    """Key for grouping runs by model and search mode."""

    model_name: str
    search_mode: str


class RunConfigKey(NamedTuple):
    """Key for deduplicating runs by model, cache, and search mode."""

    model_name: str
    cache_mode: str
    search_mode: str


class ModelCacheKey(NamedTuple):
    """Key for grouping runs by model and cache mode (for web-search comparison)."""

    model_name: str
    cache_mode: str


# Cost per tool call for web search (Perplexity or built-in) in USD.
TOOL_CALL_COST_PER_CALL = 0.005

# Search mode values (from filename parsing).
SEARCH_MODE_PERPLEXITY = "perplexity"
SEARCH_MODE_WEB_SEARCH = "web-search"


def _search_mode_display(search_mode: str) -> str:
    """Return display label for search mode (web-search -> built-in)."""
    return "built-in" if search_mode == SEARCH_MODE_WEB_SEARCH else search_mode


class LoadedRun(NamedTuple):
    """A run loaded from disk with metadata parsed from the filename."""

    timestamp: str
    cache_mode: str
    search_mode: str
    display_date: str
    run: ModelRunOutput


def _parse_filename(filename: str) -> ParsedFilename:
    """Extract metadata from an output filename.

    Supported formats:
      new: {YYYYMMDDTHHMMSS}-{model}-{cache|no-cache}-{perplexity|web-search}-{TICKER}.json
      old: {YYYYMMDDTHHMMSS}-{model}-{cache|no-cache}-{TICKER}.json

    Detection works from the tail of the stem:
      parts[-1] = TICKER
      parts[-2] = "perplexity"         → new format, perplexity search
      parts[-2] = "search", [-3]="web" → new format, web-search
      otherwise                         → legacy format (assumed perplexity)
    """
    stem = Path(filename).stem  # strip .json
    parts = stem.split("-")
    timestamp = parts[0]

    if parts[-2] == SEARCH_MODE_PERPLEXITY:
        search_mode = SEARCH_MODE_PERPLEXITY
        cache_mode = "no-cache" if len(parts) >= 4 and parts[-4] == "no" else "cache"
    elif parts[-2] == "search" and len(parts) >= 3 and parts[-3] == "web":
        search_mode = SEARCH_MODE_WEB_SEARCH
        cache_mode = "no-cache" if len(parts) >= 6 and parts[-5] == "no" else "cache"
    else:
        # Legacy format without search suffix
        search_mode = SEARCH_MODE_PERPLEXITY
        cache_mode = "no-cache" if len(parts) >= 3 and parts[-3] == "no" else "cache"

    raw_ts = timestamp  # e.g. 20260224T012914
    try:
        display_date = f"{raw_ts[:4]}-{raw_ts[4:6]}-{raw_ts[6:8]} {raw_ts[9:11]}:{raw_ts[11:13]}:{raw_ts[13:15]}"
    except IndexError:
        display_date = raw_ts

    return ParsedFilename(
        timestamp=timestamp,
        cache_mode=cache_mode,
        search_mode=search_mode,
        display_date=display_date,
    )


def _fmt_billions(value: float) -> str:
    if abs(value) >= 1e12:
        return f"${value / 1e12:.2f}T"
    if abs(value) >= 1e9:
        return f"${value / 1e9:.2f}B"
    if abs(value) >= 1e6:
        return f"${value / 1e6:.2f}M"
    return f"${value:.2f}"


def _fmt_pct(value: float) -> str:
    return f"{value:.1%}"


def _run_has_usage(run: ModelRunOutput) -> bool:
    """True if this run has stored cost/speed data."""
    return (
        run.elapsed_s is not None
        and run.input_tokens is not None
        and run.output_tokens is not None
    )


def _run_to_result(run: ModelRunOutput, cache_mode: str) -> RunResult | None:
    """Build a RunResult from stored ModelRunOutput for cost calculation. Returns None if usage missing or model unknown."""
    if not _run_has_usage(run):
        return None
    try:
        model_name = ModelName(run.model_name)
    except ValueError:
        return None
    return RunResult(
        model_name=model_name,
        cache_enabled=(cache_mode == "cache"),
        elapsed_s=run.elapsed_s or 0.0,
        input_tokens=run.input_tokens or 0,
        output_tokens=run.output_tokens or 0,
        cache_write_tokens=run.cache_write_tokens or 0,
        cache_read_tokens=run.cache_read_tokens or 0,
        tool_calls=run.tool_calls or 0,
        error=None,
        output=None,
    )


def _build_cost_speed_comparison_table(runs: list[LoadedRun]) -> Table | None:
    """Build a single table comparing cost, speed, and token usage across all models."""
    runs_with_usage = [x for x in runs if _run_has_usage(x.run)]
    if not runs_with_usage:
        return None

    rows: list[tuple[str, ...]] = []
    for loaded in sorted(
        runs_with_usage, key=lambda x: (x.run.model_name, x.cache_mode, x.search_mode)
    ):
        r = _run_to_result(loaded.run, loaded.cache_mode)
        if r is None:
            continue
        cost = calc_actual_cost(r)
        total_cost = cost.total_cost if cost else "N/A"
        rows.append(
            (
                loaded.run.model_name,
                loaded.cache_mode,
                _search_mode_display(loaded.search_mode),
                f"{r.elapsed_s:.2f}",
                f"{r.input_tokens:,}",
                f"{r.output_tokens:,}",
                f"{r.cache_write_tokens:,}",
                f"{r.cache_read_tokens:,}",
                str(r.tool_calls),
                total_cost,
            )
        )

    if not rows:
        return None
    table = Table(
        title="Model cost & speed comparison",
        show_header=True,
        header_style="bold magenta",
        show_lines=True,
    )
    table.add_column("Model", style="cyan", no_wrap=True)
    table.add_column("Cache", justify="center")
    table.add_column("Web Search", justify="center")
    table.add_column("Time (s)", justify="right")
    table.add_column("Input Tok", justify="right")
    table.add_column("Output Tok", justify="right")
    table.add_column("Cache Write", justify="right")
    table.add_column("Cache Read", justify="right")
    table.add_column("Tool Calls", justify="right")
    table.add_column("Total Cost", justify="right")
    for row in rows:
        table.add_row(*row)
    return table


def _build_cache_comparison_tables(runs: list[LoadedRun]) -> list[Table]:
    """For each (model, search_mode) that has both cache and no-cache runs with usage data, build a comparison table."""
    by_model: dict[ModelSearchKey, list[LoadedRun]] = defaultdict(list)
    for loaded in runs:
        key = ModelSearchKey(
            model_name=loaded.run.model_name, search_mode=loaded.search_mode
        )
        by_model[key].append(loaded)

    tables: list[Table] = []
    for key in sorted(by_model.keys()):
        model_runs = by_model[key]
        model_name, search_mode = key.model_name, key.search_mode
        cache_runs = [x for x in model_runs if x.cache_mode == "cache"]
        no_cache_runs = [x for x in model_runs if x.cache_mode == "no-cache"]
        if not cache_runs or not no_cache_runs:
            continue

        # Prefer runs that have usage; take latest of each if multiple
        def with_usage(lst: list[LoadedRun]) -> list[LoadedRun]:
            have = [x for x in lst if _run_has_usage(x.run)]
            return have[-1:] if have else lst[-1:]

        cache_pick = with_usage(cache_runs)
        no_cache_pick = with_usage(no_cache_runs)
        rows: list[tuple[str, ...]] = []
        cache_result: RunResult | None = None
        no_cache_result: RunResult | None = None
        for label, picked in [("cache", cache_pick), ("no-cache", no_cache_pick)]:
            if not picked:
                continue
            loaded = picked[0]
            r = _run_to_result(loaded.run, loaded.cache_mode)
            if r is None:
                rows.append((label, "-", "-", "-", "-", "-", "-"))
                continue
            if label == "cache":
                cache_result = r
            else:
                no_cache_result = r
            cost = calc_actual_cost(r)
            time_s = f"{r.elapsed_s:.2f}"
            in_tok = f"{r.input_tokens:,}"
            out_tok = f"{r.output_tokens:,}"
            cw_tok = f"{r.cache_write_tokens:,}"
            cr_tok = f"{r.cache_read_tokens:,}"
            total_cost = cost.total_cost if cost else "N/A"
            rows.append((label, time_s, in_tok, out_tok, cw_tok, cr_tok, total_cost))

        # Add savings row when we have both cache and no-cache with valid data
        if cache_result and no_cache_result:

            def _fmt_savings(pct: float) -> str:
                color = "green" if pct >= 0 else "red"
                return f"[{color}]{pct:.1f}%[/{color}]"

            time_savings: str
            cost_savings: str
            if no_cache_result.elapsed_s > 0:
                pct = (
                    (no_cache_result.elapsed_s - cache_result.elapsed_s)
                    / no_cache_result.elapsed_s
                    * 100
                )
                time_savings = _fmt_savings(pct)
            else:
                time_savings = "-"
            no_cost = calc_raw_cost(no_cache_result)
            cache_cost = calc_raw_cost(cache_result)
            if no_cost is not None and cache_cost is not None and no_cost > 0:
                pct = (no_cost - cache_cost) / no_cost * 100
                cost_savings = _fmt_savings(pct)
            else:
                cost_savings = "-"
            rows.append(("Savings", time_savings, "-", "-", "-", "-", cost_savings))

        if not rows:
            continue
        search_label = _search_mode_display(search_mode)
        table = Table(
            title=f"Cache vs no-cache: [cyan]{model_name}[/cyan]  [dim]{search_label}[/dim]",
            show_header=True,
            header_style="bold magenta",
            show_lines=True,
        )
        table.add_column("Mode", style="cyan", no_wrap=True)
        table.add_column("Time (s)", justify="right")
        table.add_column("Input Tok", justify="right")
        table.add_column("Output Tok", justify="right")
        table.add_column("Cache Write", justify="right")
        table.add_column("Cache Read", justify="right")
        table.add_column("Total Cost", justify="right")
        for row in rows:
            table.add_row(*row)
        tables.append(table)
    return tables


def _build_web_search_comparison_tables(runs: list[LoadedRun]) -> list[Table]:
    """For each (model, cache_mode) that has both perplexity and web-search runs, build a comparison table with total estimated cost (base + tool_calls * $0.005)."""
    by_model_cache: dict[ModelCacheKey, list[LoadedRun]] = defaultdict(list)
    for loaded in runs:
        key = ModelCacheKey(
            model_name=loaded.run.model_name, cache_mode=loaded.cache_mode
        )
        by_model_cache[key].append(loaded)

    tables: list[Table] = []
    for key in sorted(by_model_cache.keys()):
        model_runs = by_model_cache[key]
        model_name, cache_mode = key.model_name, key.cache_mode
        perplexity_runs = [
            x for x in model_runs if x.search_mode == SEARCH_MODE_PERPLEXITY
        ]
        web_search_runs = [
            x for x in model_runs if x.search_mode == SEARCH_MODE_WEB_SEARCH
        ]
        if not perplexity_runs or not web_search_runs:
            continue

        def with_usage(lst: list[LoadedRun]) -> list[LoadedRun]:
            have = [x for x in lst if _run_has_usage(x.run)]
            return have[-1:] if have else lst[-1:]

        perplexity_pick = with_usage(perplexity_runs)
        web_search_pick = with_usage(web_search_runs)
        rows: list[tuple[str, ...]] = []
        perplexity_result: RunResult | None = None
        web_search_result: RunResult | None = None
        perplexity_total_est: float | None = None
        web_search_total_est: float | None = None
        for label, picked in [
            (SEARCH_MODE_PERPLEXITY, perplexity_pick),
            (_search_mode_display(SEARCH_MODE_WEB_SEARCH), web_search_pick),
        ]:
            if not picked:
                continue
            loaded = picked[0]
            r = _run_to_result(loaded.run, loaded.cache_mode)
            if r is None:
                rows.append((label, "-", "-", "-", "-", "-", "-", "-"))
                continue
            if label == SEARCH_MODE_PERPLEXITY:
                perplexity_result = r
            else:
                web_search_result = r
            base_cost = calc_raw_cost(r)
            tool_cost = r.tool_calls * TOOL_CALL_COST_PER_CALL
            if base_cost is not None:
                total_est = base_cost + tool_cost
                base_str = f"${base_cost:.4f}"
                tool_str = f"${tool_cost:.4f}"
                total_str = f"${total_est:.4f}"
                if label == SEARCH_MODE_PERPLEXITY:
                    perplexity_total_est = total_est
                else:
                    web_search_total_est = total_est
            else:
                base_str = "N/A"
                tool_str = f"${tool_cost:.4f}"
                total_str = "N/A"
            rows.append(
                (
                    label,
                    f"{r.elapsed_s:.2f}",
                    f"{r.input_tokens:,}",
                    f"{r.output_tokens:,}",
                    str(r.tool_calls),
                    base_str,
                    tool_str,
                    total_str,
                )
            )

        # Add savings row (web-search vs perplexity) when we have both with valid data
        if perplexity_result and web_search_result:

            def _fmt_savings(pct: float) -> str:
                color = "green" if pct >= 0 else "red"
                return f"[{color}]{pct:.1f}%[/{color}]"

            time_savings: str
            cost_savings: str
            if perplexity_result.elapsed_s > 0:
                pct = (
                    (perplexity_result.elapsed_s - web_search_result.elapsed_s)
                    / perplexity_result.elapsed_s
                    * 100
                )
                time_savings = _fmt_savings(pct)
            else:
                time_savings = "-"
            if (
                perplexity_total_est is not None
                and web_search_total_est is not None
                and perplexity_total_est > 0
            ):
                pct = (
                    (perplexity_total_est - web_search_total_est)
                    / perplexity_total_est
                    * 100
                )
                cost_savings = _fmt_savings(pct)
            else:
                cost_savings = "-"
            rows.append(
                ("Savings", time_savings, "-", "-", "-", "-", "-", cost_savings)
            )

        if not rows:
            continue
        table = Table(
            title=f"Web search comparison: [cyan]{model_name}[/cyan]  [dim]{cache_mode}[/dim]",
            show_header=True,
            header_style="bold magenta",
            show_lines=True,
        )
        table.add_column("Web Search", style="cyan", no_wrap=True)
        table.add_column("Time (s)", justify="right")
        table.add_column("Input Tok", justify="right")
        table.add_column("Output Tok", justify="right")
        table.add_column("Tool Calls", justify="right")
        table.add_column("Base Cost", justify="right")
        table.add_column("Tool Cost", justify="right")
        table.add_column("Total Est. Cost", justify="right")
        for row in rows:
            table.add_row(*row)
        tables.append(table)
    return tables


def _build_summary_table(runs: list[LoadedRun]) -> Table:
    """Build a summary table row per run."""
    table = Table(
        title="Run Summary",
        show_header=True,
        header_style="bold magenta",
        show_lines=True,
    )
    table.add_column("Date / Time", style="dim", no_wrap=True)
    table.add_column("Model", style="cyan", no_wrap=True)
    table.add_column("Cache", justify="center")
    table.add_column("Web Search", justify="center")
    table.add_column("Fcst Yrs", justify="right")
    table.add_column("Rev Growth", justify="right")
    table.add_column("EBIT Margin", justify="right")
    table.add_column("Perp Growth", justify="right")
    table.add_column("Intrinsic Price", justify="right")
    table.add_column("Market Price", justify="right")
    table.add_column("Upside", justify="right")
    table.add_column("DCF Status", justify="center")

    for loaded in runs:
        run = loaded.run
        cache_mode = loaded.cache_mode
        display_date = loaded.display_date
        sd = run.market_analyst.stock_data
        sa = run.market_analyst.stock_assumptions
        market_price = sd.market_cap / sd.n_shares_outstanding

        if run.dcf_result is not None:
            intrinsic = run.dcf_result.intrinsic_share_price
            upside = (intrinsic - market_price) / market_price
            sign = "+" if upside >= 0 else ""
            color = "green" if upside >= 0 else "red"
            intrinsic_str = f"${intrinsic:.2f}"
            upside_str = f"[{color}]{sign}{upside:.1%}[/{color}]"
            status_str = "[green]OK[/green]"
        else:
            intrinsic_str = "[dim]-[/dim]"
            upside_str = "[dim]-[/dim]"
            status_str = "[red]Error[/red]"

        table.add_row(
            display_date,
            run.model_name,
            "yes" if cache_mode == "cache" else "no",
            _search_mode_display(loaded.search_mode),
            str(sa.forecast_period_years),
            _fmt_pct(sa.assumed_forecast_period_annual_revenue_growth_rate),
            _fmt_pct(sa.assumed_ebit_margin),
            _fmt_pct(sa.assumed_perpetuity_cash_flow_growth_rate),
            intrinsic_str,
            f"${market_price:.2f}",
            upside_str,
            status_str,
        )

    return table


def _build_stock_data_table(run: ModelRunOutput) -> Table:
    sd = run.market_analyst.stock_data
    table = Table(show_header=False, box=None, padding=(0, 1))
    table.add_column("Field", style="bold")
    table.add_column("Value", justify="right")

    rows = [
        ("Revenue", _fmt_billions(sd.revenue)),
        ("EBIT", _fmt_billions(sd.ebit)),
        ("EBIT Margin", _fmt_pct(sd.ebit_margin)),
        ("CapEx", _fmt_billions(sd.capital_expenditure)),
        ("CapEx / Revenue", _fmt_pct(sd.capex_as_percentage_of_revenue)),
        ("Market Cap", _fmt_billions(sd.market_cap)),
        ("Enterprise Value", _fmt_billions(sd.enterprise_value)),
        ("Net Debt", _fmt_billions(sd.net_debt)),
        ("Gross Debt", _fmt_billions(sd.gross_debt)),
        ("Interest Expense", _fmt_billions(sd.total_interest_expense)),
        ("Implied Int. Rate", _fmt_pct(sd.implied_interest_rate)),
        ("Beta", f"{sd.beta:.2f}"),
        ("Shares Outstanding", f"{sd.n_shares_outstanding / 1e9:.2f}B"),
        ("Market Price", f"${sd.market_cap / sd.n_shares_outstanding:.2f}"),
        ("Scale", sd.company_scale),
    ]
    for field, value in rows:
        table.add_row(field, value)
    return table


def _build_assumptions_table(run: ModelRunOutput) -> Table:
    sa = run.market_analyst.stock_assumptions
    table = Table(show_header=False, box=None, padding=(0, 1))
    table.add_column("Assumption", style="bold")
    table.add_column("Value", justify="right")

    rows = [
        ("Forecast Period", f"{sa.forecast_period_years} years"),
        (
            "Revenue Growth",
            _fmt_pct(sa.assumed_forecast_period_annual_revenue_growth_rate),
        ),
        ("EBIT Margin", _fmt_pct(sa.assumed_ebit_margin)),
        ("D&A Rate", _fmt_pct(sa.assumed_depreciation_and_amortization_rate)),
        ("CapEx Rate", _fmt_pct(sa.assumed_capex_rate)),
        ("WC Rate", _fmt_pct(sa.assumed_change_in_working_capital_rate)),
        ("Tax Rate", _fmt_pct(sa.assumed_tax_rate)),
        ("Perp. Growth", _fmt_pct(sa.assumed_perpetuity_cash_flow_growth_rate)),
        ("Risk-Free Rate", f"{run.risk_free_rate:.3f}"),
    ]
    for field, value in rows:
        table.add_row(field, value)
    return table


def _build_detail_panel(
    filename: str,
    cache_mode: str,
    search_mode: str,
    display_date: str,
    run: ModelRunOutput,
    *,
    show_reasoning: bool,
) -> Panel:
    sd = run.market_analyst.stock_data
    sa = run.market_analyst.stock_assumptions
    market_price = sd.market_cap / sd.n_shares_outstanding

    content_parts: list[str] = []

    # DCF result / error
    if run.dcf_result is not None:
        intrinsic = run.dcf_result.intrinsic_share_price
        upside = (intrinsic - market_price) / market_price
        sign = "+" if upside >= 0 else ""
        color = "green" if upside >= 0 else "red"
        content_parts.append(
            f"[bold]DCF:[/bold] intrinsic [bold cyan]${intrinsic:.2f}[/bold cyan] "
            f"vs market [bold]{market_price:.2f}[/bold]  "
            f"[{color}]{sign}{upside:.1%}[/{color}]"
        )
    elif run.dcf_error:
        content_parts.append(f"[bold]DCF:[/bold] [red]{run.dcf_error}[/red]")
    else:
        content_parts.append("[bold]DCF:[/bold] [dim]no result[/dim]")

    # Side-by-side tables via Columns
    stock_panel = Panel(
        _build_stock_data_table(run),
        title="[bold]Stock Data[/bold]",
        border_style="blue",
        expand=False,
    )
    assumptions_panel = Panel(
        _build_assumptions_table(run),
        title="[bold]Assumptions[/bold]",
        border_style="yellow",
        expand=False,
    )

    # Reasoning
    reasoning_text = ""
    if show_reasoning and sa.reasoning:
        reasoning_text = f"\n[bold]Reasoning:[/bold]\n[dim]{sa.reasoning}[/dim]"

    group_items: list = [Text.from_markup(content_parts[0])]
    group_items.append(Columns([stock_panel, assumptions_panel], expand=False))
    if reasoning_text:
        group_items.append(Text.from_markup(reasoning_text))

    cache_label = "cache" if cache_mode == "cache" else "no-cache"
    search_label = _search_mode_display(search_mode)
    title = (
        f"[cyan]{run.model_name}[/cyan]  [dim]{cache_label}[/dim]  "
        f"[dim]{search_label}[/dim]  "
        f"[dim]{display_date}[/dim]  [dim]{filename}[/dim]"
    )
    return Panel(RichGroup(*group_items), title=title, border_style="magenta")


def load_runs_for_ticker(ticker: str) -> list[LoadedRun]:
    """Load all output files for *ticker* sorted by timestamp ascending."""
    out_dir = _OUTPUTS_DIR
    pattern = f"*-{ticker.upper()}.json"
    files = sorted(out_dir.glob(pattern))
    if not files:
        return []

    results: list[LoadedRun] = []
    for path in files:
        try:
            data = json.loads(path.read_text())
            run = ModelRunOutput.model_validate(data)
        except Exception as exc:  # noqa: BLE001
            console.print(
                f"[yellow]Warning: could not load {path.name}: {exc}[/yellow]"
            )
            continue
        parsed = _parse_filename(path.name)
        results.append(
            LoadedRun(
                timestamp=parsed.timestamp,
                cache_mode=parsed.cache_mode,
                search_mode=parsed.search_mode,
                display_date=parsed.display_date,
                run=run,
            )
        )

    return results


def _deduplicate_to_latest(runs: list[LoadedRun]) -> list[LoadedRun]:
    """Keep only the latest run per (model_name, cache_mode, search_mode). Timestamp format sorts chronologically."""
    by_config: dict[RunConfigKey, LoadedRun] = {}
    for loaded in runs:
        key = RunConfigKey(
            model_name=loaded.run.model_name,
            cache_mode=loaded.cache_mode,
            search_mode=loaded.search_mode,
        )
        existing = by_config.get(key)
        if existing is None or loaded.timestamp > existing.timestamp:
            by_config[key] = loaded
    return sorted(
        by_config.values(),
        key=lambda x: (x.run.model_name, x.cache_mode, x.search_mode),
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Pretty-print all saved run results for a ticker from outputs/."
    )
    parser.add_argument("ticker", type=str, help="Stock ticker (e.g. AMZN, AAPL).")
    parser.add_argument(
        "--detail",
        action="store_true",
        help="Show a detailed panel per run in addition to the summary table.",
    )
    parser.add_argument(
        "--reasoning",
        action="store_true",
        help="Include the model's full reasoning text in detail panels (implies --detail).",
    )
    parser.add_argument(
        "--compare-cache",
        action="store_true",
        help="Compare cost and speed for cache vs no-cache runs per model (requires usage data in saved JSON).",
    )
    parser.add_argument(
        "--compare-cost",
        action="store_true",
        help="Compare model cost, speed, tokens (input/output/cache write/read) across all runs (requires usage data in saved JSON).",
    )
    parser.add_argument(
        "--compare-web-search",
        action="store_true",
        help="Compare cost of built-in web search vs Perplexity per model; adds tool cost ($0.005/call) and total estimated cost columns.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    ticker = args.ticker.upper()
    show_detail = args.detail or args.reasoning

    runs = _deduplicate_to_latest(load_runs_for_ticker(ticker))

    if not runs:
        console.print(
            f"[red]No output files found for ticker [bold]{ticker}[/bold] "
            f"in {_OUTPUTS_DIR}[/red]"
        )
        raise SystemExit(1)

    console.print()
    console.rule(f"[bold]{ticker}[/bold] — {len(runs)} run(s)")
    console.print()

    console.print(_build_summary_table(runs))

    if args.compare_cache:
        comparison_tables = _build_cache_comparison_tables(runs)
        if comparison_tables:
            console.print()
            for table in comparison_tables:
                console.print(table)
                console.print()
        else:
            console.print()
            console.print(
                "[dim]No cache vs no-cache comparison available: either no model has "
                "both runs, or saved files lack usage data. Re-run model_cost_comparison.py "
                "to record cost/speed (new runs will include it).[/dim]"
            )
            console.print()

    if args.compare_cost:
        cost_table = _build_cost_speed_comparison_table(runs)
        if cost_table:
            console.print()
            console.print(cost_table)
            console.print()
        else:
            console.print()
            console.print(
                "[dim]No cost/speed comparison available: saved files lack usage data. "
                "Re-run model_cost_comparison.py to record cost/speed (new runs will include it).[/dim]"
            )
            console.print()

    if args.compare_web_search:
        web_search_tables = _build_web_search_comparison_tables(runs)
        if web_search_tables:
            console.print()
            for table in web_search_tables:
                console.print(table)
                console.print()
        else:
            console.print()
            console.print(
                "[dim]No web-search vs perplexity comparison available: need both perplexity and web-search runs per model. "
                "Re-run model_cost_comparison.py with --web-search both.[/dim]"
            )
            console.print()

    if show_detail:
        console.print()
        for loaded in runs:
            filename = f"{loaded.timestamp}-{loaded.run.model_name.replace('.', '-')}-{loaded.cache_mode}-{loaded.search_mode}-{ticker}.json"
            panel = _build_detail_panel(
                filename,
                loaded.cache_mode,
                loaded.search_mode,
                loaded.display_date,
                loaded.run,
                show_reasoning=args.reasoning,
            )
            console.print(panel)
            console.print()


if __name__ == "__main__":
    main()
