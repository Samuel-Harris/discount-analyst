<!-- Parent: ../AGENTS.md -->
<!-- Generated: 2026-03-07 | Updated: 2026-03-08 -->

# mcp

## Purpose

MCP (Model Context Protocol) tool management: fetching tool definitions from EODHD and FMP servers, and curating a subset via a web dashboard.

## Key Files

| File                  | Description                                                                 |
| --------------------- | --------------------------------------------------------------------------- |
| `fetch_mcp_tool_list.py` | Fetches MCP tools from EODHD and FMP servers, writes `tool_list.json`.   |
| `tool_list.json`      | Full tool list (read-only): `{"eodhd": [...], "fmp": [...]}`.              |
| `curated_tool_list.json` | Curated tool names by server: `{"eodhd": ["name1"], "fmp": ["name2"]}`.  |
| `dashboard.py`        | **Deprecated.** Marimo web app; use the React dashboard in `dashboards/` instead. |

## Run Commands

| Command | Description |
| ------- | ----------- |
| `uv run python scripts/mcp/fetch_mcp_tool_list.py -o scripts/mcp/tool_list.json` | Regenerate `tool_list.json`. |
| `cd dashboards && pnpm dev` | Launch the MCP Tool Dashboard (React). |

## For AI Agents

### Working In This Directory

- Do not modify `tool_list.json`; regenerate it with `fetch_mcp_tool_list.py`.
- The React dashboard in `dashboards/` reads `tool_list.json` and writes `curated_tool_list.json` on Save.
