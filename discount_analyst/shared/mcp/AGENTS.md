<!-- Parent: ../AGENTS.md -->
<!-- Generated: 2026-03-03 | Updated: 2026-03-03 -->

# mcp

## Purpose

MCP (Model Context Protocol) server factories for financial data providers. Provides EODHD and FMP MCPServerTool instances so the model provider connects to remote MCP servers directly for historical prices, fundamentals, news, screeners, quotes, statements, and DCF data. Supported providers: Anthropic, OpenAI, xAI. Not supported: Google.

## Key Files

| File | Description |
| --------- | ---------------------------- |
| `servers.py` | Factory `create_mcp_financial_data_toolset()` returning EODHD and FMP `MCPServerTool` instances; `create_eodhd_mcp_tool()` and `create_fmp_mcp_tool()` for individual tools. |
| `__init__.py` | Package initialization. |

## Subdirectories

None.

## For AI Agents

### Working In This Directory

- **Provider Support**: MCPServerTool is supported by Anthropic, OpenAI, and xAI. When `use_mcp_financial_data=True` and the provider is Google, `create_appraiser_agent` and `create_surveyor_agent` raise `NotImplementedError`. Use `use_mcp_financial_data=False` when using Google models.
- **API Keys**: When MCP is enabled, `.env` must include `FMP__API_KEY` and `EODHD__API_KEY` (nested delimiter `__` per `config/settings.py`).

### Testing Requirements

- Run MCP tests with `uv run pytest tests/shared/mcp/`.
- Unit tests mock `settings` via `conftest.py` to avoid requiring real API keys.
- Verify `create_appraiser_agent` and `create_surveyor_agent` raise `NotImplementedError` when `use_mcp_financial_data=True` and provider is `"google"`.

### Common Patterns

- **URL Auth**: EODHD and FMP pass the API key via URL query params (`?apikey=...`); no `authorization_token` is needed.
- **Tool IDs**: Use `id="eodhd"` and `id="fmp"` to distinguish servers; tools are namespaced by the provider.

## Dependencies

### Internal

- `discount_analyst.shared.config.settings`: For `settings.eodhd.api_key` and `settings.fmp.api_key`.

### External

- **pydantic-ai**: `MCPServerTool` from `pydantic_ai.builtin_tools`.

<!-- MANUAL: Any manually added notes below this line are preserved on regeneration -->
