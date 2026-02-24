#!/usr/bin/env python3
"""Pretty-print all saved run results for a given ticker.

Usage:
    uv run python scripts/cost_comparison/view_ticker_results.py AMZN
    uv run python scripts/cost_comparison/view_ticker_results.py AAPL --detail
    uv run python scripts/cost_comparison/view_ticker_results.py AMZN --compare-cache
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from collections import defaultdict

from rich.columns import Columns
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

sys.path.insert(0, str(Path(__file__).resolve().parent))
from shared import (  # noqa: E402
    ModelRunOutput,
    ModelName,
    RunResult,
    calc_actual_cost,
    outputs_dir,
)

console = Console()


def _parse_filename(filename: str) -> tuple[str, str, str]:
    """Extract (timestamp, cache_mode, display_date) from an output filename.

    Filename format: {YYYYMMDDTHHMMSS}-{model}-{cache|no-cache}-{TICKER}.json
    The suffix before the ticker is "cache" or "no-cache".
    Split by "-": parts[-1]=TICKER, parts[-2]="cache", parts[-3]="no" iff no-cache.
    """
    stem = Path(filename).stem  # strip .json
    parts = stem.split("-")
    timestamp = parts[0]
    # parts[-1]=TICKER, parts[-2]="cache", parts[-3]="no" means no-cache
    if len(parts) >= 3 and parts[-3] == "no":
        cache_mode = "no-cache"
    else:
        cache_mode = "cache"

    raw_ts = timestamp  # e.g. 20260224T012914
    try:
        display_date = f"{raw_ts[:4]}-{raw_ts[4:6]}-{raw_ts[6:8]} {raw_ts[9:11]}:{raw_ts[11:13]}:{raw_ts[13:15]}"
    except IndexError:
        display_date = raw_ts

    return timestamp, cache_mode, display_date


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


def _build_cache_comparison_tables(
    runs: list[tuple[str, str, str, ModelRunOutput]],
) -> list[Table]:
    """For each model that has both cache and no-cache runs with usage data, build a comparison table."""
    by_model: dict[str, list[tuple[str, str, str, ModelRunOutput]]] = defaultdict(list)
    for ts, cache_mode, display_date, run in runs:
        by_model[run.model_name].append((ts, cache_mode, display_date, run))

    tables: list[Table] = []
    for model_name in sorted(by_model.keys()):
        model_runs = by_model[model_name]
        cache_runs = [(t, c, d, r) for t, c, d, r in model_runs if c == "cache"]
        no_cache_runs = [(t, c, d, r) for t, c, d, r in model_runs if c == "no-cache"]
        if not cache_runs or not no_cache_runs:
            continue

        # Prefer runs that have usage; take latest of each if multiple
        def with_usage(
            lst: list[tuple[str, str, str, ModelRunOutput]],
        ) -> list[tuple[str, str, str, ModelRunOutput]]:
            have = [x for x in lst if _run_has_usage(x[3])]
            return have[-1:] if have else lst[-1:]

        cache_pick = with_usage(cache_runs)
        no_cache_pick = with_usage(no_cache_runs)
        rows: list[tuple[str, ...]] = []
        for label, picked in [("cache", cache_pick), ("no-cache", no_cache_pick)]:
            if not picked:
                continue
            _ts, cache_mode, display_date, run = picked[0]
            r = _run_to_result(run, cache_mode)
            if r is None:
                rows.append((label, "-", "-", "-", "-", "-", "-", "-"))
                continue
            cost = calc_actual_cost(r)
            time_s = f"{r.elapsed_s:.2f}"
            in_tok = f"{r.input_tokens:,}"
            out_tok = f"{r.output_tokens:,}"
            cw_tok = f"{r.cache_write_tokens:,}"
            cr_tok = f"{r.cache_read_tokens:,}"
            total_cost = cost.total_cost if cost else "N/A"
            rows.append((label, time_s, in_tok, out_tok, cw_tok, cr_tok, total_cost))

        if not rows:
            continue
        table = Table(
            title=f"Cache vs no-cache: [cyan]{model_name}[/cyan]",
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


def _build_summary_table(runs: list[tuple[str, str, str, ModelRunOutput]]) -> Table:
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
    table.add_column("Fcst Yrs", justify="right")
    table.add_column("Rev Growth", justify="right")
    table.add_column("EBIT Margin", justify="right")
    table.add_column("Perp Growth", justify="right")
    table.add_column("Intrinsic Price", justify="right")
    table.add_column("Market Price", justify="right")
    table.add_column("Upside", justify="right")
    table.add_column("DCF Status", justify="center")

    for _ts, cache_mode, display_date, run in runs:
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

    from rich.console import Group as RichGroup

    group_items: list = [Text.from_markup(content_parts[0])]
    group_items.append(Columns([stock_panel, assumptions_panel], expand=False))
    if reasoning_text:
        group_items.append(Text.from_markup(reasoning_text))

    cache_label = "cache" if cache_mode == "cache" else "no-cache"
    title = (
        f"[cyan]{run.model_name}[/cyan]  [dim]{cache_label}[/dim]  "
        f"[dim]{display_date}[/dim]  [dim]{filename}[/dim]"
    )
    return Panel(RichGroup(*group_items), title=title, border_style="magenta")


def load_runs_for_ticker(ticker: str) -> list[tuple[str, str, str, ModelRunOutput]]:
    """Load all output files for *ticker* sorted by timestamp ascending."""
    out_dir = outputs_dir()
    pattern = f"*-{ticker.upper()}.json"
    files = sorted(out_dir.glob(pattern))
    if not files:
        return []

    results: list[tuple[str, str, str, ModelRunOutput]] = []
    for path in files:
        try:
            data = json.loads(path.read_text())
            run = ModelRunOutput.model_validate(data)
        except Exception as exc:  # noqa: BLE001
            console.print(
                f"[yellow]Warning: could not load {path.name}: {exc}[/yellow]"
            )
            continue
        ts, cache_mode, display_date = _parse_filename(path.name)
        results.append((ts, cache_mode, display_date, run))

    return results


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
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    ticker = args.ticker.upper()
    show_detail = args.detail or args.reasoning

    runs = load_runs_for_ticker(ticker)

    if not runs:
        console.print(
            f"[red]No output files found for ticker [bold]{ticker}[/bold] "
            f"in {outputs_dir()}[/red]"
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

    if show_detail:
        console.print()
        for ts, cache_mode, display_date, run in runs:
            filename = (
                f"{ts}-{run.model_name.replace('.', '-')}-{cache_mode}-{ticker}.json"
            )
            panel = _build_detail_panel(
                filename,
                cache_mode,
                display_date,
                run,
                show_reasoning=args.reasoning,
            )
            console.print(panel)
            console.print()


if __name__ == "__main__":
    main()
