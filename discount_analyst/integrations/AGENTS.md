<!-- Parent: ../AGENTS.md -->
<!-- Generated: 2026-04-05 -->

# integrations

## Purpose

Named external service adapters: Perplexity search tools and EODHD/FMP MCP `MCPServerStreamableHTTP` factories.

## Key Files

| File                    | Description                                                |
| ----------------------- | ---------------------------------------------------------- |
| `perplexity.py`         | `create_perplexity_toolset(AgentName)` for web/SEC search. |
| `financial_data_mcp.py` | `create_financial_data_mcp_servers()` (EODHD + FMP URLs).  |

## Dependencies

### Internal

- `discount_analyst.config.settings` for API keys; `discount_analyst.agents.common.tool_descriptions` / `agent_names` for Perplexity.

### External

- **perplexityai**, **pydantic-ai** (`FunctionToolset`, `MCPServerStreamableHTTP`).
