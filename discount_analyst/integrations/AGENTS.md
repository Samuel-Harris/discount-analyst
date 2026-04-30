<!-- Parent: ../AGENTS.md -->
<!-- Generated: 2026-04-05 -->

# integrations

## Purpose

Named external service adapters: Perplexity search tools and EODHD/FMP MCP `MCPServerStreamableHTTP` factories.

## Key Files

| File                    | Description                                                                                     |
| ----------------------- | ----------------------------------------------------------------------------------------------- |
| `perplexity.py`         | `create_perplexity_toolset(AgentName)` for web/SEC search.                                      |
| `financial_data_mcp.py` | `create_financial_data_mcp_servers()` (EODHD + FMP URLs; EODHD omitted if `EODHD__DISABLED`).   |
| `infallible_toolset.py` | `InfallibleToolset` wrapper that catches tool errors and returns them as messages to the model. |

## Dependencies

### Internal

- `common.config` for API keys; `discount_analyst.agents.common.tool_descriptions` / `agent_names` for Perplexity.

### External

- **perplexityai**, **pydantic-ai** (`FunctionToolset`, `MCPServerStreamableHTTP`, `WrapperToolset`).
