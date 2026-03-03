<!-- Parent: ../AGENTS.md -->
<!-- Generated: 2026-02-23 | Updated: 2026-02-23 -->

# shared

## Purpose

Common data structures, configuration, and utility modules used across the `discount_analyst` package. It provides the foundational types and infrastructure for AI agents and financial modeling, ensuring consistency in data handling and API interactions.

## Key Files

| File | Description |
| --------- | ---------------------------- |
| `data_types.py` | Central Pydantic models for `StockData`, `StockAssumptions`, and agent outputs. |
| `ai_models_config.py` | Configuration for LLM models, including token budgets and thinking parameters. |
| `settings.py` | Application configuration using `pydantic-settings` for API keys and environment variables (e.g. `anthropic__api_key`, `openai__api_key`, `google__api_key`). |
| `model.py` | Factory for creating rate-limited AI models from config (Anthropic, OpenAI, Google). |
| `rate_limit_client.py` | Asynchronous HTTP client with exponential backoff and retry logic. |
| `__init__.py` | Package initialization file. |

## Subdirectories

None.

## For AI Agents

### Working In This Directory

- **Source of Truth**: Use `data_types.py` as the primary reference for all structured data models.
- **Metric Definitions**: When adding new financial metrics to `StockData`, include detailed `Field` descriptions for AI tool discovery.
- **Configuration**: Always use `settings.py` for accessing environment variables; do not use `os.environ` directly.

### Testing Requirements

- Ensure all Pydantic models are validated against sample financial data.
- Test computed fields in `StockData` for edge cases like zero revenue or zero debt.
- Verify retry logic in `rate_limit_client.py` with mock HTTP failures.

### Common Patterns

- **Pydantic Validation**: All external data should be parsed into Pydantic models.
- **Computed Fields**: Use `@computed_field` for derived financial ratios and metrics.
- **Async Retries**: Standardized API interaction patterns using `tenacity` and `AsyncTenacityTransport`.

## Dependencies

### Internal

- This directory is used by `discount_analyst.dcf_analysis` and `discount_analyst.appraiser`.

### External

- **pydantic**: Data validation and modeling.
- **pydantic-settings**: Environment variable management.
- **pydantic-ai**: AI agent framework integration.
- **httpx**: Asynchronous HTTP client for API interactions.
- **tenacity**: Advanced retry library for robust network calls.

<!-- MANUAL: Any manually added notes below this line are preserved on regeneration -->
