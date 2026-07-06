<!-- Parent: ../AGENTS.md -->
<!-- Generated: 2026-04-05 | Updated: 2026-07-06 -->

# integrations

## Purpose

Named external service adapters: bounded DuckDuckGo local web search fallback, Perplexity search tools, EODHD/FMP MCP `MCPToolset` factories (each wrapped with a plan-gated tool blacklist), async FMP/EODHD REST clients for pipeline data-quality gates, and the Docker-backed **terminal** sandbox (`terminal_exec`). Default web search/fetch capabilities are wired in `agents/common/agent_factory.py`.

FMP MCP blacklist is enabled by default via `BlacklistedMcpToolset` — whole tools are hidden from the model; multi-endpoint tools (e.g. `statements`, `company`) have blocked endpoint enum values removed from the visible schema and are still guarded at call time. Add entries in `mcp_tool_blacklist.py` when telemetry shows consistent plan-gating.

## Key Files

| File                         | Description                                                                                                                                                              |
| ---------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `bounded_web_search.py`      | Bounded DuckDuckGo local search tool with one-at-a-time DDGS calls, retries, fallback result, and Logfire telemetry.                                                     |
| `perplexity.py`              | `create_perplexity_toolset(AgentName)` for web/SEC search.                                                                                                               |
| `financial_data_mcp.py`      | `create_financial_data_mcp_servers()` (EODHD + FMP URLs; EODHD omitted if `EODHD__DISABLED`); wraps each `MCPToolset` with `BlacklistedMcpToolset`.                      |
| `mcp_tool_blacklist.py`      | `McpBlacklistPolicy`, `FMP_BLACKLIST` / `EODHD_BLACKLIST`, policy lookup, endpoint schema narrowing, and call-time block checks for plan-gated FMP endpoints.            |
| `blacklisted_mcp_toolset.py` | `BlacklistedMcpToolset` — hides blocked tools, narrows blocked endpoint values in `get_tools`, and short-circuits blocked endpoint calls before HTTP.                    |
| `fmp_client.py`              | Retry-backed async FMP stable REST client (`profile`, `search_symbol`, `quote_short`) for pipeline candidate gates.                                                      |
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
