<!-- Parent: ../AGENTS.md -->
<!-- Generated: 2026-03-03 | Updated: 2026-03-03 -->

# surveyor

## Purpose

The `surveyor` directory contains the implementation of the "Surveyor" AI agent. This agent discovers cheap small-cap stock candidates in UK and US markets using Perplexity-backed web search. It mirrors the appraiser structure but with a different output schema (`SurveyorOutput`) tailored to stock screening and discovery.

## Key Files

| File               | Description                                                                   |
| ------------------ | ----------------------------------------------------------------------------- |
| `surveyor.py`      | Factory function for creating the Surveyor agent, including its search tools. |
| `system_prompt.py` | System prompt for the Surveyor agent persona and instructions.                |
| `__init__.py`      | Package initialization for the surveyor module.                               |

## Subdirectories

None.

## For AI Agents

### Working In This Directory

- **Agent Tools**: By default (`use_perplexity=False`), the agent uses pydantic-ai built-in `WebSearchTool` and, for providers that support it, `WebFetchTool`. With `use_perplexity=True`, Perplexity-backed tools (`web_search`, `sec_filings_search`) are provided by `discount_analyst.shared.tools.perplexity` via `create_perplexity_toolset(AgentName.SURVEYOR)`. Add or modify agent-specific descriptions in `shared/tools/descriptions.py`.
- **Prompts**: Keep the system persona in `system_prompt.py`.

### Testing Requirements

- Verify agent behavior by adding or updating integration tests in `tests/`. Ensure external API calls (Perplexity, LLMs) are mocked to prevent non-deterministic results and cost.
- Run tests using `uv run pytest`.

### Common Patterns

- **Search Tools**: Uses `AsyncPerplexity` with `search_mode="web"` for general research and `search_mode="sec"` for official financial filings.
- **Structured Output**: The agent is configured to return a `SurveyorOutput` (defined in `shared/models/data_types.py`) for strict data validation.

## Dependencies

### Internal

- `discount_analyst.shared.models.data_types`: For the `SurveyorOutput` schema.
- `discount_analyst.shared.config.ai_models_config`: For model configuration and selection.
- `discount_analyst.shared.config.settings`: For API keys and rate limit settings.
- `discount_analyst.shared.ai.model`: For creating the LLM model instance.
- `discount_analyst.shared.tools.perplexity`: For Perplexity-backed search tools via `create_perplexity_toolset(AgentName.SURVEYOR)`.

### External

- **pydantic-ai**: The agent framework used to build the surveyor.
- **perplexityai**: Used for the `web_search` and `sec_filings_search` tools.
- **aiolimiter**: Manages asynchronous rate limiting for the Perplexity API.
- **pydantic**: Used for internal and shared data models.
