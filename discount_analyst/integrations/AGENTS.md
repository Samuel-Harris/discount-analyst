<!-- Parent: ../AGENTS.md -->
<!-- Generated: 2026-04-05 | Updated: 2026-07-06 -->

# integrations

## Purpose

Named external service adapters: bounded DuckDuckGo local web search fallback, Perplexity search tools, EODHD/FMP MCP `MCPToolset` factories (each wrapped with a plan-gated tool blacklist), async FMP/EODHD REST clients for pipeline data-quality gates, and the Docker-backed **terminal** sandbox (`terminal_exec`). Default web search/fetch capabilities are wired in `agents/common/agent_factory.py`.

FMP MCP blacklist is enabled by default via `BlacklistedMcpToolset` — whole tools are hidden from the model; multi-endpoint tools (e.g. `statements`, `company`) have blocked endpoint enum values removed from the visible schema and are still guarded at call time. Add entries in `mcp_tool_blacklist.py` when telemetry shows consistent plan-gating.

## FMP / EODHD MCP plan gating

Source of truth for enforcement: `mcp_tool_blacklist.py` (`FMP_BLACKLIST`, `EODHD_BLACKLIST`). The tables below record **Logfire telemetry** (project `discount-analyst`, Jun–Jul 2026) on the current FMP subscription tier — consistent `ACCESS DENIED` / higher-plan errors before the blacklist was added. When the plan changes, update the blacklist and this section together.

### FMP MCP — inaccessible (blacklisted)

**Whole tools** — hidden from the model; calls short-circuited if invoked anyway:

| Tool            | Typical failure                  | Plan hint (from MCP errors) |
| --------------- | -------------------------------- | --------------------------- |
| `analyst`       | All observed endpoints denied    | Higher plan                 |
| `news`          | e.g. `search-stock-news`         | Starter+                    |
| `insiderTrades` | e.g. `insider-trade-statistics`  | Starter+                    |
| `chart`         | e.g. `historical-price-eod-full` | Higher plan                 |
| `calendar`      | e.g. `earnings-company`          | Higher plan                 |

**Multi-endpoint tools** — only these `(tool, endpoint)` pairs are blocked; other endpoints on the same tool remain visible:

| Tool         | Blocked endpoint                                                                   | Plan hint   |
| ------------ | ---------------------------------------------------------------------------------- | ----------- |
| `statements` | `financial-scores`, `financial-score`                                              | Higher plan |
| `statements` | `income-statement`, `balance-sheet-statement`, `cashflow-statement`                | Higher plan |
| `statements` | `key-metrics`, `enterprise-values`, `metrics-ratios`                               | Higher plan |
| `statements` | `owner-earnings`, `revenue-geographic-segments`, `revenue-product-segmentation`    | Higher plan |
| `statements` | `income-statements-ttm`, `balance-sheet-statements-ttm`, `cashflow-statements-ttm` | Ultimate+   |
| `company`    | `batch-market-cap`                                                                 | Higher plan |
| `quote`      | `quote-short`                                                                      | Higher plan |

Legacy aliases (`fmp_search`, `fmp_statements`, `fmp_quote`) route to the same underlying tools; the same endpoints are plan-gated.

### FMP MCP — accessible (observed working, not blacklisted)

| Tool                | Endpoint                       | Notes                                                        |
| ------------------- | ------------------------------ | ------------------------------------------------------------ |
| `search`            | `search-company-screener`      | Primary Surveyor screener                                    |
| `search`            | `search-symbol`, `search-name` | Symbol / name lookup                                         |
| `quote`             | `batch-quote`                  | Multi-symbol quotes                                          |
| `company`           | `profile-symbol`               | Single-symbol profile                                        |
| `marketPerformance` | `biggest-losers`               | Market movers                                                |
| `directory`         | `available-exchanges`          | Exchange list                                                |
| `statements`        | `financial-reports-dates`      | Only `statements` endpoint confirmed working on current tier |

Use `quote` → `batch-quote` and `company` → `profile-symbol` instead of the blocked short-quote / batch-market-cap endpoints. Surveyor Step 2 (`financial-scores` for Piotroski / Altman) is **not** available on the current plan — agents should record data gaps or use web search / terminal fallbacks.

### EODHD MCP

No EODHD MCP tool calls appeared in Logfire over the same window (no HTTP to `mcp.eodhd.dev`, no `tools/call` spans). `EODHD_BLACKLIST` is therefore empty. UK/LSE coverage in practice has relied on FMP `search` with `exchange=LSE`, the EODHD REST client (`eodhd_client.py`), or web search. EODHD MCP may still be registered unless `EODHD__DISABLED=true`.

## Key Files

| File                         | Description                                                                                                                                                              |
| ---------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `bounded_web_search.py`      | Bounded DuckDuckGo local search tool with one-at-a-time DDGS calls, retries, fallback result, and Logfire telemetry.                                                     |
| `perplexity.py`              | `create_perplexity_toolset(AgentName)` for web/SEC search.                                                                                                               |
| `financial_data_mcp.py`      | `create_financial_data_mcp_servers()` (EODHD + FMP URLs; EODHD omitted if `EODHD__DISABLED`); wraps each `MCPToolset` with `BlacklistedMcpToolset`.                      |
| `mcp_tool_blacklist.py`      | `McpBlacklistPolicy`, `FMP_BLACKLIST` / `EODHD_BLACKLIST`, policy lookup, endpoint schema narrowing, and call-time block checks for plan-gated FMP endpoints.            |
| `blacklisted_mcp_toolset.py` | `BlacklistedMcpToolset` — hides blocked tools, narrows blocked endpoint values in `get_tools`, and short-circuits blocked endpoint calls before HTTP.                    |
| `fmp_client.py`              | Retry-backed async FMP stable REST client (`profile`, `search_symbol`; listing gate uses profile only).                                                                  |
| `eodhd_client.py`            | Retry-backed async EODHD REST client (`real_time`, `fundamentals_general`) for UK listing fallback when FMP returns 402/403.                                             |
| `terminal.py`                | `Terminal` capability (`terminal_exec`), `TerminalRuntimeConfig`, `TerminalExecPayload`, `ensure_terminal_ready`, `TerminalUnavailableError`, `delete_terminal_session`. |
| `infallible_toolset.py`      | `InfallibleToolset` wrapper that catches tool errors and returns them as messages to the model.                                                                          |
| `text_only_web_fetch.py`     | `create_text_only_web_fetch_tool()` — local `WebFetch` that converts binary documents to markdown via markitdown (DeepSeek).                                             |

## Dependencies

### Internal

- `common.config` for API keys; `discount_analyst.http.retrying_client` for provider REST retries; `discount_analyst.agents.common.tool_descriptions` / `agent_names` for Perplexity.

### External

- **perplexityai**, **pydantic-ai** (`FunctionToolset`, `MCPToolset`, `WrapperToolset`, native-or-local capabilities), **ddgs** / **duckduckgo_search** (local web search fallback), **markitdown** (text-only web fetch for providers that reject binary message parts).

### Terminal fail-fast

When terminal is enabled, `run_streamed_agent` calls `ensure_terminal_ready` before any LLM streaming. The probe `POST`s a throwaway session to the orchestrator and deletes it on success. On failure it raises `TerminalUnavailableError` with the orchestrator HTTP `detail` (e.g. missing sandbox image) so agent runs fail before token spend. Disabled via `--no-terminal` or `DASHBOARD_USE_TERMINAL=false`.
