<!-- Parent: ../AGENTS.md -->
<!-- Generated: 2026-03-03 | Updated: 2026-03-03 -->

# appraiser

## Purpose

The `appraiser` directory contains the implementation of the "Appraiser" AI agent. This agent is responsible for researching real-world financial data and determining the necessary assumptions (growth rates, margins, terminal values, etc.) for a Discounted Cash Flow (DCF) analysis. It leverages the Perplexity API to perform targeted web searches and official SEC filing searches.

## Key Files

| File | Description |
| --------- | ---------------------------- |
| `appraiser.py` | Factory function for creating the Appraiser agent, including its search tools. |
| `system_prompt.py` | The expert financial analyst persona and step-by-step analysis instructions for the agent. |
| `user_prompt.py` | Helper for generating dynamic user prompts that can include research report context. |
| `data_types.py` | Internal Pydantic models for the appraiser module (e.g., `SearchResult`). |
| `__init__.py` | Package initialization for the appraiser module. |

## Subdirectories

None.

## For AI Agents

### Working In This Directory

- **Agent Tools**: When adding or modifying tools in `appraiser.py`, ensure they have detailed Google-style docstrings, as these are used by the agent for discovery.
- **Prompts**: Keep the system persona in `system_prompt.py` and the user-facing instruction logic in `user_prompt.py`.
- **Rate Limiting**: Always use the `perplexity_rate_limiter` (defined in `appraiser.py`) for any new tools that call the Perplexity API.

### Testing Requirements

- Verify agent behavior by adding or updating integration tests in `tests/`. Ensure external API calls (Perplexity, LLMs) are mocked to prevent non-deterministic results and cost.
- Run tests using `uv run pytest`.

### Common Patterns

- **Search Tools**: Uses `AsyncPerplexity` with `search_mode="web"` for general research and `search_mode="sec"` for official financial filings.
- **Structured Output**: The agent is configured to return an `AppraiserOutput` (defined in `shared/data_types.py`) for strict data validation.

## Dependencies

### Internal

- `discount_analyst.shared.data_types`: For the `AppraiserOutput` schema.
- `discount_analyst.shared.ai_models_config`: For model configuration and selection.
- `discount_analyst.shared.settings`: For API keys and rate limit settings.
- `discount_analyst.shared.model`: For creating the LLM model instance.

### External

- **pydantic-ai**: The agent framework used to build the appraiser.
- **perplexityai**: Used for the `web_search` and `sec_filings_search` tools.
- **aiolimiter**: Manages asynchronous rate limiting for the Perplexity API.
- **pydantic**: Used for internal and shared data models.

<!-- MANUAL: Any manually added notes below this line are preserved on regeneration -->
