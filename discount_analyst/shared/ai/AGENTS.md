<!-- Parent: ../AGENTS.md -->
<!-- Generated: 2026-03-03 | Updated: 2026-03-03 -->

# ai

## Purpose

Factory for creating AI model instances from configuration. Instantiates pydantic-ai models (Anthropic, OpenAI, Google) with rate-limited HTTP clients and provider-specific settings.

## Key Files

| File | Description |
| --------- | ---------------------------- |
| `model.py` | Factory function `create_model_from_config` that creates rate-limited AI models from `AIModelConfig`. |
| `history_processors.py` | `get_history_processors_for_model`: returns pydantic-ai `history_processors` hooks per model (currently none; OpenAI uses server-side compaction). |

## Subdirectories

None.

## For AI Agents

### Working In This Directory

- **Extending Providers**: When adding a new provider, add a config class in `config/ai_models_config.py`, add a case to `create_model_from_config`, and wire the provider's API key from `config/settings.py`.

### Testing Requirements

- Verify model creation for each supported provider (with mocked settings).
- Ensure unsupported config types raise clear errors.

### Common Patterns

- **Match on Config**: Uses `match config` with discriminated union for provider-specific instantiation.
- **Rate-Limited Client**: All providers use `create_rate_limit_client()` from `http/rate_limit_client.py` for retries.

## Dependencies

### Internal

- `discount_analyst.shared.config.settings`: API keys and rate limit settings.
- `discount_analyst.shared.config.ai_models_config`: Model config types.
- `discount_analyst.shared.http.rate_limit_client`: HTTP client with retries.

### External

- **pydantic-ai**: Model and provider classes for Anthropic, OpenAI, Google.

<!-- MANUAL: Any manually added notes below this line are preserved on regeneration -->
