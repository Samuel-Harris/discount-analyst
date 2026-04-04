<!-- Parent: ../AGENTS.md -->
<!-- Generated: 2026-03-03 | Updated: 2026-04-04 -->

# ai

## Purpose

Factory for creating AI model instances from configuration and shared research-style agents. Instantiates pydantic-ai models (Anthropic, OpenAI, Google) with rate-limited HTTP clients and provider-specific settings; researcher, appraiser, and surveyor agents share web / Perplexity / financial MCP tooling via `agent_factory.create_pipeline_agent`. Use `streamed_agent_run.run_streamed_agent` for the standard streaming + retry loop used by scripts.

## Key Files

| File                    | Description                                                                                                                                                            |
| ----------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `model.py`              | Factory function `create_model_from_config` that creates rate-limited AI models from `AIModelConfig`.                                                                  |
| `agent_factory.py`      | `PipelineAgentSpec` and `create_pipeline_agent`: build pipeline agents with web search/fetch, optional Perplexity, and optional financial MCP toolsets.                |
| `streamed_agent_run.py` | `run_streamed_agent` and `StreamedAgentRunOutcome`: drain `stream_with_retries`, optional stream callback and debounce, return output/usage/messages and elapsed time. |

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
