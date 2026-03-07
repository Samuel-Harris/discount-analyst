#!/usr/bin/env -S uv run python
"""Extract MCP server tools from EODHD and FMP servers or from a Logfire trace.

By default fetches tool definitions from the EODHD and FMP MCP servers and writes
them as JSON. Optionally, pass a trace file to extract tools from a Logfire trace
export (single object, array of spans, or NDJSON) using gen_ai.tool.definitions.

Output: [{"type": "function", "name": "...", "parameters": <json schema>}, ...]
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


MCP_PREFIXES = ("eodhd_", "fmp_")


def _is_mcp_tool(tool: dict) -> bool:
    """Return True if tool is from an MCP server (EODHD or FMP)."""
    name = tool.get("name") or ""
    return any(name.startswith(prefix) for prefix in MCP_PREFIXES)


def _normalize_tool_def(item: dict) -> dict:
    """Normalize a tool definition to { type, name, parameters } for JSON output."""
    name = item.get("name") or ""
    # Prefer 'parameters' (OpenAI style); fall back to 'inputSchema' (MCP style).
    parameters = item.get("parameters")
    if parameters is None and "inputSchema" in item:
        parameters = item.get("inputSchema") or {}
    if not isinstance(parameters, dict):
        parameters = {}
    return {"type": "function", "name": name, "parameters": parameters}


def _get_attributes_dict(span: dict) -> dict:
    """Extract attributes as a flat dict. Handles both {k:v} and [{key,value}] formats."""
    attrs = span.get("attributes") or {}
    if isinstance(attrs, dict):
        return attrs
    if isinstance(attrs, list):
        result: dict = {}
        for item in attrs:
            if isinstance(item, dict) and "key" in item and "value" in item:
                result[item["key"]] = item["value"]
        return result
    return {}


def _find_tool_definitions(obj: object) -> list[dict]:
    """Recursively find gen_ai.tool.definitions or tool-like arrays in structure."""
    tools: list[dict] = []

    if isinstance(obj, dict):
        # Check span attributes (flat dict or OTLP key-value list)
        attrs = _get_attributes_dict(obj)
        for key in ("gen_ai.tool.definitions", "gen_ai_tool_definitions"):
            defs = attrs.get(key)
            if isinstance(defs, str):
                try:
                    defs = json.loads(defs)
                except json.JSONDecodeError:
                    defs = None
            if isinstance(defs, list):
                for item in defs:
                    if isinstance(item, dict) and item.get("type") == "function":
                        tools.append(item)
        # Also check top-level (legacy / flattened export)
        for key in ("gen_ai.tool.definitions", "gen_ai_tool_definitions"):
            defs = obj.get(key)
            if isinstance(defs, str):
                try:
                    defs = json.loads(defs)
                except json.JSONDecodeError:
                    defs = None
            if isinstance(defs, list):
                for item in defs:
                    if isinstance(item, dict) and item.get("type") == "function":
                        tools.append(item)
        for value in obj.values():
            if value is not obj:
                tools.extend(_find_tool_definitions(value))
    elif isinstance(obj, list):
        for item in obj:
            tools.extend(_find_tool_definitions(item))

    return tools


def _flatten_spans(obj: object) -> list[dict]:
    """Extract all span-like dicts from OTLP trace or nested structure."""
    spans: list[dict] = []

    if isinstance(obj, dict):
        # OTLP format: resourceSpans[].scopeSpans[].spans[]
        for rs in obj.get("resourceSpans", []):
            for ss in rs.get("scopeSpans", []):
                spans.extend(ss.get("spans", []))
        # Flat spans array
        if "spans" in obj and not spans:
            spans = obj["spans"]
        # Single span (has span_id or span_name)
        if ("span_id" in obj or "span_name" in obj) and obj not in spans:
            spans.append(obj)
        for value in obj.values():
            if value is not obj:
                spans.extend(_flatten_spans(value))
    elif isinstance(obj, list):
        for item in obj:
            spans.extend(_flatten_spans(item))

    return spans


def _load_trace_data(path: Path) -> list[dict]:
    """Load trace data from file. Handles single object, array, OTLP, or NDJSON."""
    text = path.read_text()
    data: list[dict] = []

    # Try parsing as single JSON first
    text_stripped = text.strip()
    if text_stripped.startswith("["):
        raw = json.loads(text)
        data = _flatten_spans(raw) if raw else []
        if not data and isinstance(raw, list) and raw and isinstance(raw[0], dict):
            data = raw
    elif text_stripped.startswith("{"):
        try:
            obj = json.loads(text)
            data = _flatten_spans(obj)
            if not data:
                data = [obj]
        except json.JSONDecodeError:
            data = []
            for line in text.splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    item = json.loads(line)
                    data.extend(_flatten_spans(item) or [item])
                except json.JSONDecodeError:
                    pass
    else:
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                item = json.loads(line)
                data.extend(_flatten_spans(item) or [item])
            except json.JSONDecodeError:
                pass

    return data


def extract_mcp_tools(path: Path) -> tuple[list[dict], list[dict]]:
    """Extract MCP tool definitions from a Logfire trace file.

    Returns:
        (tools, spans) - MCP tools found and all spans examined.
    """
    data = _load_trace_data(path)
    all_tools: list[dict] = []
    seen_names: set[str] = set()

    for item in data:
        for tool in _find_tool_definitions(item):
            name = tool.get("name")
            if name and _is_mcp_tool(tool) and name not in seen_names:
                seen_names.add(name)
                all_tools.append(_normalize_tool_def(tool))

    # Sort by server prefix then name
    def sort_key(t: dict) -> tuple[str, str]:
        name = t.get("name", "")
        prefix = "eodhd" if name.startswith("eodhd_") else "fmp"
        return (prefix, name)

    all_tools.sort(key=sort_key)
    return all_tools, data


async def fetch_tools_from_mcp() -> list[dict]:
    """Fetch MCP tool definitions from EODHD and FMP servers.

    Returns a list of normalized tool dicts: { type, name, parameters }.
    """
    all_tools: list[dict] = []
    eodhd = create_eodhd_mcp_server()
    fmp = create_fmp_mcp_server()

    async with eodhd:
        for mcp_tool in await eodhd.list_tools():
            name = f"eodhd_{mcp_tool.name}"
            schema = getattr(mcp_tool, "inputSchema", None) or {}
            if not isinstance(schema, dict):
                schema = {}
            all_tools.append({"type": "function", "name": name, "parameters": schema})

    async with fmp:
        for mcp_tool in await fmp.list_tools():
            name = f"fmp_{mcp_tool.name}"
            schema = getattr(mcp_tool, "inputSchema", None) or {}
            if not isinstance(schema, dict):
                schema = {}
            all_tools.append({"type": "function", "name": name, "parameters": schema})

    def sort_key(t: dict) -> tuple[str, str]:
        n = t.get("name", "")
        prefix = "eodhd" if n.startswith("eodhd_") else "fmp"
        return (prefix, n)

    all_tools.sort(key=sort_key)
    return all_tools


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Extract MCP server tools from EODHD and FMP servers (default) or from a Logfire trace."
    )
    parser.add_argument(
        "trace_file",
        type=Path,
        nargs="?",
        default=None,
        help="If set, extract from this Logfire trace JSON file instead of fetching from MCP servers",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help="Also write full tool definitions as JSON to this file",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Show span names found (for debugging when no tools are found)",
    )
    args = parser.parse_args()

    console = Console()

    if args.trace_file is not None:
        if not args.trace_file.exists():
            console.print(f"[red]Error:[/red] File not found: {args.trace_file}")
            return 1
        tools, spans = extract_mcp_tools(args.trace_file)
    else:
        tools = asyncio.run(fetch_tools_from_mcp())
        spans = []

    if not tools:
        console.print("[yellow]No MCP tools found in trace.[/yellow]")
        if args.verbose and spans:
            table = Table(
                title="Spans in trace (gen_ai.tool.definitions is on the 'chat' span)"
            )
            table.add_column("span_name", style="cyan")
            table.add_column("span_id", style="dim")
            for s in spans:
                name = s.get("span_name") or s.get("name") or "(unnamed)"
                sid = s.get("span_id", "")[:12] + "…" if s.get("span_id") else ""
                table.add_row(str(name), sid)
            console.print(table)
        console.print(
            "Tool definitions live in the child [bold]chat[/bold] span "
            "(when the model is invoked), not the root agent span."
        )
        console.print(
            "Export the [bold]full trace[/bold] including all child spans from Logfire, "
            "or use the Logfire query API to fetch records for the trace."
        )
        return 0

    eodhd_count = sum(1 for t in tools if t.get("name", "").startswith("eodhd_"))
    fmp_count = sum(1 for t in tools if t.get("name", "").startswith("fmp_"))

    table = Table(title="MCP Tools")
    table.add_column("Server", style="cyan")
    table.add_column("Count", justify="right", style="green")
    table.add_row("EODHD", str(eodhd_count))
    table.add_row("FMP", str(fmp_count))
    table.add_row("Total", str(len(tools)), style="bold")
    console.print(table)

    if args.output:
        args.output.write_text(json.dumps(tools, indent=2))
        console.print(f"[green]Wrote {len(tools)} tools to {args.output}[/green]")

    return 0


if __name__ == "__main__":
    sys.exit(main())
