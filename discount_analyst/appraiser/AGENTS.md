<!-- Parent: ../AGENTS.md -->
<!-- Generated: 2026-03-03 | Updated: 2026-03-03 -->

# appraiser

## Purpose

The `appraiser` directory contains the implementation of the "Appraiser" AI agent. This agent is responsible for researching real-world financial data and determining the necessary assumptions (growth rates, margins, terminal values, etc.) for a Discounted Cash Flow (DCF) analysis. It leverages the Perplexity API to perform targeted web searches and official SEC filing searches.

## Key Files

| File               | Description                                                                                |
| ------------------ | ------------------------------------------------------------------------------------------ |
| `appraiser.py`     | Factory function for creating the Appraiser agent, including its search tools.             |
| `system_prompt.py` | The expert financial analyst persona and step-by-step analysis instructions for the agent. |
| `user_prompt.py`   | Helper for generating dynamic user prompts that can include research report context.       |
| `data_types.py`    | Internal Pydantic models for the appraiser module (e.g., `SearchResult`).                  |
| `__init__.py`      | Package initialization for the appraiser module.                                           |

## Subdirectories

None.

## For AI Agents

### Working In This Directory

- **Agent Tools**: Perplexity-backed tools (`web_search`, `sec_filings_search`) are provided by `discount_analyst.shared.tools.perplexity` via `create_perplexity_toolset(AgentName.APPRAISER)`. EODHD and FMP MCPServerTool instances are added via `create_eodhd_mcp_tool()` and `create_fmp_mcp_tool()` when `use_mcp_financial_data=True` (default). Add or modify agent-specific descriptions in `shared/tools/descriptions.py`.
- **MCP Financial Data**: Set `use_mcp_financial_data=False` when using Google models; MCPServerTool is not supported by Google. Supported providers: anthropic, openai, xai.
- **Prompts**: Keep the system persona in `system_prompt.py` and the user-facing instruction logic in `user_prompt.py`.

### Testing Requirements

- Verify agent behavior by adding or updating integration tests in `tests/`. Ensure external API calls (Perplexity, LLMs) are mocked to prevent non-deterministic results and cost.
- Run tests using `uv run pytest`.

### Common Patterns

- **Search Tools**: Uses `AsyncPerplexity` with `search_mode="web"` for general research and `search_mode="sec"` for official financial filings.
- **Structured Output**: The agent is configured to return an `AppraiserOutput` (defined in `shared/models/data_types.py`) for strict data validation.

## Dependencies

### Internal

- `discount_analyst.shared.models.data_types`: For the `AppraiserOutput` schema.
- `discount_analyst.shared.config.ai_models_config`: For model configuration and selection.
- `discount_analyst.shared.config.settings`: For API keys and rate limit settings.
- `discount_analyst.shared.ai.model`: For creating the LLM model instance.
- `discount_analyst.shared.tools.perplexity`: For Perplexity-backed search tools via `create_perplexity_toolset(AgentName.APPRAISER)`.
- `discount_analyst.shared.mcp.servers`: For EODHD and FMP MCPServerTool when `use_mcp_financial_data=True`.

### External

- **pydantic-ai**: The agent framework used to build the appraiser.
- **perplexityai**: Used for the `web_search` and `sec_filings_search` tools.
- **aiolimiter**: Manages asynchronous rate limiting for the Perplexity API.
- **pydantic**: Used for internal and shared data models.

<!-- MANUAL: Any manually added notes below this line are preserved on regeneration -->
