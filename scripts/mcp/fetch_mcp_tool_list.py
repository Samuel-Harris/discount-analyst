#!/usr/bin/env -S uv run python
"""Fetch MCP server tools from EODHD and FMP servers and write them as JSON.

Output: {"eodhd": [<tool dicts>], "fmp": [<tool dicts>]} — tools preserved exactly as returned.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

from rich.console import Console
from rich.table import Table

from discount_analyst.shared.mcp.financial_data import (
    create_eodhd_mcp_server,
    create_fmp_mcp_server,
)


async def fetch_tools_from_mcp() -> dict[str, list[dict]]:
    """Fetch MCP tool definitions from EODHD and FMP servers.

    Returns tools grouped by server, with each tool preserved exactly as returned.
    """
    eodhd = create_eodhd_mcp_server()
    fmp = create_fmp_mcp_server()

    eodhd_tools: list[dict] = []
    async with eodhd:
        for mcp_tool in await eodhd.list_tools():
            eodhd_tools.append(mcp_tool.model_dump(mode="json"))
    eodhd_tools.sort(key=lambda t: t.get("name", ""))

    fmp_tools: list[dict] = []
    async with fmp:
        for mcp_tool in await fmp.list_tools():
            fmp_tools.append(mcp_tool.model_dump(mode="json"))
    fmp_tools.sort(key=lambda t: t.get("name", ""))

    return {"eodhd": eodhd_tools, "fmp": fmp_tools}


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Fetch MCP server tools from EODHD and FMP servers."
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help="Write tool definitions as JSON to this file",
    )
    parser.add_argument(
        "-l",
        "--list",
        action="store_true",
        help="Print the name of each tool to the console",
    )
    args = parser.parse_args()

    console = Console()
    tools_by_server = asyncio.run(fetch_tools_from_mcp())

    eodhd_count = len(tools_by_server.get("eodhd", []))
    fmp_count = len(tools_by_server.get("fmp", []))
    total_count = eodhd_count + fmp_count

    table = Table(title="MCP Tools")
    table.add_column("Server", style="cyan")
    table.add_column("Count", justify="right", style="green")
    table.add_row("EODHD", str(eodhd_count))
    table.add_row("FMP", str(fmp_count))
    table.add_row("Total", str(total_count), style="bold")
    console.print(table)

    if args.list:
        for server, tools in tools_by_server.items():
            for tool in tools:
                console.print(f"{server}: {tool.get('name', '')}")

    if args.output:
        args.output.write_text(json.dumps(tools_by_server, indent=2))
        console.print(f"[green]Wrote {total_count} tools to {args.output}[/green]")

    return 0


if __name__ == "__main__":
    sys.exit(main())
