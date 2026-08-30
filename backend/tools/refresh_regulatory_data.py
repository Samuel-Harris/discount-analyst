"""Refresh official exchange, SEC EDGAR, and Companies House caches.

Run from the repository root::

    uv run discount-analyst admin refresh-regulatory-data
    uv run discount-analyst admin refresh-regulatory-data --exchanges
    uv run discount-analyst admin refresh-regulatory-data --sec
    uv run discount-analyst admin refresh-regulatory-data --companies-house
"""

from __future__ import annotations

import argparse
import asyncio
import sys

from rich.console import Console
from rich.table import Table

from discount_analyst.agents.tools.regulatory_data.models import SourceRefreshResult
from discount_analyst.agents.tools.regulatory_data.refresh import refresh_selected

console = Console()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Refresh official regulatory-data caches (NASDAQ Trader, LSE, SEC, Companies House)."
    )
    parser.add_argument(
        "--exchanges",
        action="store_true",
        help="Refresh NASDAQ Trader and LSE issuer lists.",
    )
    parser.add_argument(
        "--sec",
        action="store_true",
        help="Refresh SEC ticker map and companyfacts bulk extract.",
    )
    parser.add_argument(
        "--companies-house",
        action="store_true",
        help="Refresh Companies House company data and iXBRL accounts.",
    )
    return parser


def _print_results(results: list[SourceRefreshResult]) -> None:
    table = Table(title="Regulatory data refresh")
    table.add_column("Source")
    table.add_column("Version / date")
    table.add_column("Records", justify="right")
    table.add_column("Skipped / idempotent", justify="right")
    table.add_column("Cache path")
    table.add_column("Active snapshot")
    for result in results:
        table.add_row(
            result.source,
            result.downloaded_version_or_date,
            str(result.record_count),
            str(result.skipped_or_idempotent_count),
            result.cache_path,
            result.active_snapshot,
        )
    console.print(table)


async def _async_main(args: argparse.Namespace) -> int:
    results, failures = await refresh_selected(
        exchanges=args.exchanges,
        sec=args.sec,
        companies_house=args.companies_house,
    )
    if results:
        _print_results(results)
    for source, error in failures:
        console.print(f"[red]{source} failed:[/red] {error}")
    return 1 if failures else 0


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    raise SystemExit(asyncio.run(_async_main(args)))


if __name__ == "__main__":
    main(sys.argv[1:])
