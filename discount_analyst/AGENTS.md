<!-- Parent: ../AGENTS.md -->
<!-- Generated: 2026-02-23 | Updated: 2026-02-23 -->

# discount_analyst

## Purpose

The core source code for the "Discount Analyst" stock analysis engine. This directory contains the implementation of the financial modeling logic (DCF), the AI agents for automated research, and the shared utilities required to perform comprehensive, low-cost stock valuations.

## Key Files

| File | Description |
| --------- | ---------------------------- |
| `dcf_analysis/dcf_analysis.py` | Implementation of the Discounted Cash Flow calculation engine. |
| `market_analyst/market_analyst.py` | Factory for the Market Analyst agent, including Perplexity-powered search tools. |
| `shared/data_types.py` | Central Pydantic models defining `StockData`, `StockAssumptions`, and analysis outputs. |
| `shared/settings.py` | Application configuration using `pydantic-settings` for API keys and environment variables. |
| `shared/ai_models_config.py` | Configuration for LLM models, including token budgets and thinking parameters. |

## Subdirectories

| Directory | Purpose |
| --------- | ----------------------------------------- |
| `dcf_analysis/` | Core logic for financial calculations and DCF modeling. (see `dcf_analysis/AGENTS.md`) |
| `market_analyst/` | AI agent implementation using `pydantic-ai` for market research and assumption making. (see `market_analyst/AGENTS.md`) |
| `shared/` | Common data structures, configuration, and utility modules used across the package. (see `shared/AGENTS.md`) |

## For AI Agents

### Working In This Directory

- **Structured Output**: Always use the Pydantic models defined in `shared/data_types.py` for any agent outputs or internal data passing.
- **Async Execution**: Ensure all network calls (AI agents, search tools) are asynchronous.
- **Type Safety**: Maintain strict typing for all financial metrics (typically `float`).

### Testing Requirements

- Run the full test suite with `uv run pytest`.
- Add unit tests for any new financial calculation logic in `tests/dcf_analysis/`.
- Ensure agent tool changes are verified with integration tests (mocking external API calls).

### Common Patterns

- **Agent-Tool Binding**: AI agents use the `@agent.tool_plain` decorator with detailed Google-style docstrings for tool discovery.
- **Financial Modeling**: Follow the "Bottom-Up/Line-Item" approach for Free Cash Flow (FCF) projections as seen in `DCFAnalysis`.
- **Rate Limiting**: Use the `aiolimiter` in `market_analyst.py` when making calls to external search or LLM APIs.

## Dependencies

### Internal

- This is the root source directory; submodules depend on `discount_analyst.shared`.

### External

- **pydantic-ai**: The primary framework for building and running analysis agents.
- **pydantic**: Used for data validation and structured data modeling.
- **perplexityai**: Powers the `web_search` and `sec_filings_search` capabilities of the agent.
- **aiolimiter**: Manages API rate limits for external services.
- **marimo**: The interactive notebook environment for analysis.

<!-- MANUAL: Any manually added notes below this line are preserved on regeneration -->
