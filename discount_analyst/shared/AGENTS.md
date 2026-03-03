<!-- Parent: ../AGENTS.md -->
<!-- Generated: 2026-03-03 | Updated: 2026-03-03 -->

# shared

## Purpose

Common data structures, configuration, and utility modules used across the `discount_analyst` package. It provides the foundational types and infrastructure for AI agents and financial modeling, ensuring consistency in data handling and API interactions.

## Key Files

| File | Description |
| --------- | ---------------------------- |
| `__init__.py` | Package initialization file. |

## Subdirectories

| Directory | Purpose |
| --------- | ----------------------------------------- |
| `config/` | Application and AI model configuration (see `config/AGENTS.md`) |
| `models/` | Central Pydantic models for stock data and agent outputs (see `models/AGENTS.md`) |
| `ai/` | Factory for creating rate-limited AI models from config (see `ai/AGENTS.md`) |
| `http/` | Asynchronous HTTP client with retry logic (see `http/AGENTS.md`) |

## For AI Agents

### Working In This Directory

- **Source of Truth**: Use `models/data_types.py` as the primary reference for all structured data models.
- **Metric Definitions**: When adding new financial metrics to `StockData`, include detailed `Field` descriptions for AI tool discovery.
- **Configuration**: Always use `config/settings.py` for accessing environment variables; do not use `os.environ` directly.

### Testing Requirements

- Ensure all Pydantic models are validated against sample financial data.
- Test computed fields in `StockData` for edge cases like zero revenue or zero debt.
- Verify retry logic in `http/rate_limit_client.py` with mock HTTP failures.

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
