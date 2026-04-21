<!-- Parent: ../AGENTS.md -->
<!-- Generated: 2026-04-05 -->

# config

## Purpose

Application and AI model configuration: API keys via `pydantic-settings`, LLM model selection and provider-specific parameters, and provider feature flags (`WEB_FETCH`, `MCP`). Unified `Settings` and `settings` are defined in [`common/config.py`](../../common/config.py); import `common.config` in code.

## Key Files

| File                   | Description                                                                                           |
| ---------------------- | ----------------------------------------------------------------------------------------------------- |
| `ai_models_config.py`  | `ModelName`, `AIModelsConfig`, discriminated `AIModelConfig` union and `model_settings` per provider. |
| `provider_features.py` | `Provider`, `ProviderFeature`, `PROVIDERS_BY_FEATURE` mapping.                                        |

## Subdirectories

None.

## For AI Agents

- Add new models to `ModelName` and extend the `AIModelsConfig.model` computed field with a matching branch.
- Use `settings` from `common.config`; do not read `os.environ` directly in application code.

## Dependencies

### Internal

- Consumed by `discount_analyst.agents.common`, `discount_analyst.integrations`, and scripts.

### External

- **pydantic**, **pydantic-settings**, **pydantic-ai** (`UsageLimits`, model settings types).
