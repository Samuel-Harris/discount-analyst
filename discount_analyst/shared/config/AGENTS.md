<!-- Parent: ../AGENTS.md -->
<!-- Generated: 2026-03-03 | Updated: 2026-03-03 -->

# config

## Purpose

Application and AI model configuration. Loads API keys and environment variables via `pydantic-settings` and defines LLM model selection, token budgets, and provider-specific parameters.

## Key Files

| File | Description |
| --------- | ---------------------------- |
| `settings.py` | Application settings for API keys and environment variables (e.g. `anthropic__api_key`, `openai__api_key`, `google__api_key`). |
| `ai_models_config.py` | Configuration for LLM models, including token budgets, thinking parameters, and provider-specific settings (Anthropic, OpenAI, Google). |

## Subdirectories

None.

## For AI Agents

### Working In This Directory

- **Configuration**: Always use `settings.py` for accessing environment variables; do not use `os.environ` directly.
- **Model Selection**: Add new models to `ModelName` enum and extend the `appraiser` computed field in `AIModelsConfig` when supporting additional providers.
- **OpenAI + privacy**: `OpenAIAIModelConfig` uses `openai_store=False` and does **not** set `openai_previous_response_id="auto"`, because unstored responses are not valid targets for `previous_response_id` and the API returns `previous_response_not_found`.

### Testing Requirements

- Validate that settings load correctly from environment and `.env` files.
- Ensure new model configs produce valid `AIModelConfig` instances.

### Common Patterns

- **Nested Settings**: Uses `env_nested_delimiter="__"` for nested config (e.g. `ANTHROPIC__API_KEY`).
- **Discriminated Union**: `AIModelConfig` uses `provider` as discriminator for provider-specific configs.

## Dependencies

### Internal

- This directory is used by `discount_analyst.shared.ai`, `discount_analyst.appraiser`, and scripts.

### External

- **pydantic**: Data validation and modeling.
- **pydantic-settings**: Environment variable management.
- **pydantic-ai**: `UsageLimits` and model settings types.

<!-- MANUAL: Any manually added notes below this line are preserved on regeneration -->
