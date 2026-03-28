<!-- Parent: ../AGENTS.md -->
<!-- Generated: 2026-03-28 | Updated: 2026-03-28 -->

# mcp

## Purpose

MCP (Model Context Protocol) **Streamable HTTP** server factories for financial data (EODHD, FMP). pydantic-ai registers each remote server as native toolsets on the agent. Supported model providers: Anthropic and OpenAI. Google is not supported for MCP; use `--no-mcp` on agent scripts when using Gemini.

## Key Files

| File | Description |
| --------- | ---------------------------- |
| `financial_data.py` | `create_financial_data_mcp_servers()` returning EODHD and FMP `MCPServerStreamableHTTP` instances (`tool_prefix` `eodhd` / `fmp`). |
| `__init__.py` | Package marker. |

## Subdirectories

None.

## For AI Agents

### Working In This Directory

- **Provider support**: When `use_mcp_financial_data=True`, Surveyor and Appraiser call `add_required_feature_to_builtin_tools` with `ProviderFeature.MCP`. Unsupported providers raise `NotImplementedError` (e.g. Google). Pass `use_mcp_financial_data=False` or CLI `--no-mcp` for those runs.
- **API keys**: `.env` must include `EODHD__API_KEY` and `FMP__API_KEY` (nested delimiter `__` per `config/settings.py`) whenever MCP is enabled.

### Testing Requirements

- No dedicated MCP test package in-repo; agent integration is exercised via scripts with mocks where applicable.

### Common Patterns

- **URL auth**: Keys are passed as `?apikey=...` on the MCP base URLs; no separate bearer token.

## Dependencies

### Internal

- `discount_analyst.shared.config.settings`: `settings.eodhd.api_key`, `settings.fmp.api_key`.

### External

- **pydantic-ai**: `MCPServerStreamableHTTP` from `pydantic_ai.mcp`.

<!-- MANUAL: Any manually added notes below this line are preserved on regeneration -->
