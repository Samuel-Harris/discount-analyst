<!-- Parent: ../AGENTS.md -->
<!-- Generated: 2026-03-03 | Updated: 2026-04-02 -->

# appraiser

## Purpose

The `appraiser` directory contains the implementation of the "Appraiser" AI agent. This agent is responsible for researching real-world financial data and determining the necessary assumptions (growth rates, margins, terminal values, etc.) for a Discounted Cash Flow (DCF) analysis. It leverages the Perplexity API to perform targeted web searches and official SEC filing searches.

## Key Files

| File               | Description                                                                                                                                         |
| ------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------- |
| `appraiser.py`     | Factory for the Appraiser agent (`create_appraiser_agent`) and `create_appraiser_user_prompt` (research report + `SurveyorCandidate` for DCF runs). |
| `system_prompt.py` | The expert financial analyst persona and step-by-step analysis instructions for the agent.                                                          |
| `user_prompt.py`   | `create_user_prompt`: requires ticker, research report body, and `SurveyorCandidate` JSON context.                                                  |
| `data_types.py`    | `AppraiserOutput` (agent structured output: `StockData` + `StockAssumptions`).                                                                      |
| `__init__.py`      | Package initialization for the appraiser module.                                                                                                    |

## Subdirectories

None.

## For AI Agents

### Working In This Directory

- **Agent Tools**: By default (`use_perplexity=False`), the agent uses pydantic-ai built-in `WebSearchTool` and, for providers that support it, `WebFetchTool`. With `use_perplexity=True`, Perplexity-backed tools (`web_search`, `sec_filings_search`) are provided by `discount_analyst.shared.tools.perplexity` via `create_perplexity_toolset(AgentName.APPRAISER)`. When `use_mcp_financial_data=True` (default), EODHD and FMP MCP toolsets are added for Anthropic and OpenAI via `add_required_feature_to_builtin_tools` (`ProviderFeature.MCP`). Google does not support MCP—use `use_mcp_financial_data=False` or `scripts/agents/run_appraiser.py --no-mcp` / `scripts/cost_comparison/model_cost_comparison.py --no-mcp`. Add or modify agent-specific descriptions in `shared/tools/descriptions.py`.
- **Prompts**: Keep the system persona in `system_prompt.py` and the user-facing instruction logic in `user_prompt.py`.

### Testing Requirements

- Verify agent behavior by adding or updating integration tests in `tests/`. Ensure external API calls (Perplexity, LLMs) are mocked to prevent non-deterministic results and cost.
- Run tests using `uv run pytest`.

### Common Patterns

- **Search Tools**: Uses `AsyncPerplexity` with `search_mode="web"` for general research and `search_mode="sec"` for official financial filings.
- **Structured Output**: The agent returns `AppraiserOutput` from `appraiser/data_types.py`. Surveyor screening context is passed via `create_appraiser_user_prompt` → `user_prompt.create_user_prompt` using `SurveyorCandidate` from `shared/schemas/surveyor.py`.

## Dependencies

### Internal

- `discount_analyst.agents.appraiser.data_types`: For `AppraiserOutput`.
- `discount_analyst.shared.schemas.surveyor`: For `SurveyorCandidate` in user prompts.
- `discount_analyst.shared.config.ai_models_config`: For model configuration and selection.
- `discount_analyst.shared.config.settings`: For API keys and rate limit settings.
- `discount_analyst.shared.ai.model`: For creating the LLM model instance.
- `discount_analyst.shared.tools.perplexity`: For Perplexity-backed search tools via `create_perplexity_toolset(AgentName.APPRAISER)`.
- `discount_analyst.shared.utils.agent_tools`: MCP toolset wiring via `add_required_feature_to_builtin_tools`.
- `discount_analyst.shared.mcp.financial_data`: EODHD/FMP `MCPServerStreamableHTTP` factories.

### External

- **pydantic-ai**: The agent framework used to build the appraiser.
- **perplexityai**: Used for the `web_search` and `sec_filings_search` tools.
- **aiolimiter**: Manages asynchronous rate limiting for the Perplexity API.
- **pydantic**: Used for internal and shared data models.

<!-- MANUAL: Any manually added notes below this line are preserved on regeneration -->
