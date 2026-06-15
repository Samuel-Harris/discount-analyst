<!-- Parent: ../AGENTS.md -->
<!-- Generated: 2026-04-05 -->

# integrations

## Purpose

Named external service adapters: Perplexity search tools, EODHD/FMP MCP `MCPToolset` factories, and the Docker-backed **terminal** sandbox (`terminal_exec`). Default web search/fetch is wired directly through Pydantic AI capabilities in `agents/common/agent_factory.py`.

## Key Files

| File                     | Description                                                                                                                                                              |
| ------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `perplexity.py`          | `create_perplexity_toolset(AgentName)` for web/SEC search.                                                                                                               |
| `financial_data_mcp.py`  | `create_financial_data_mcp_servers()` (EODHD + FMP URLs; EODHD omitted if `EODHD__DISABLED`).                                                                            |
| `terminal.py`            | `Terminal` capability (`terminal_exec`), `TerminalRuntimeConfig`, `TerminalExecPayload`, `ensure_terminal_ready`, `TerminalUnavailableError`, `delete_terminal_session`. |
| `infallible_toolset.py`  | `InfallibleToolset` wrapper that catches tool errors and returns them as messages to the model.                                                                          |
| `text_only_web_fetch.py` | `create_text_only_web_fetch_tool()` — local `WebFetch` that converts binary documents to markdown via markitdown (DeepSeek).                                             |

## Dependencies

### Internal

- `common.config` for API keys; `discount_analyst.agents.common.tool_descriptions` / `agent_names` for Perplexity.

### External

- **perplexityai**, **pydantic-ai** (`FunctionToolset`, `MCPToolset`, `WrapperToolset`), **markitdown** (text-only web fetch for providers that reject binary message parts).

### Terminal fail-fast

When terminal is enabled, `run_streamed_agent` calls `ensure_terminal_ready` before any LLM streaming. The probe `POST`s a throwaway session to the orchestrator and deletes it on success. On failure it raises `TerminalUnavailableError` with the orchestrator HTTP `detail` (e.g. missing sandbox image) so agent runs fail before token spend. Disabled via `--no-terminal` or `DASHBOARD_USE_TERMINAL=false`.
