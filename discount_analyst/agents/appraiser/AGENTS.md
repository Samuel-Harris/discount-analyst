<!-- Parent: ../AGENTS.md -->
<!-- Generated: 2026-03-03 | Updated: 2026-05-31 -->

# appraiser

## Purpose

The `appraiser` directory contains the implementation of the "Appraiser" AI agent. This agent is responsible for researching real-world financial and market data, selecting suitable valuation methods, triangulating primary and cross-check evidence, and returning a method-agnostic intrinsic-value distribution. It is valuation-only and does not produce final investment ratings or recommended actions.

## Key Files

| File               | Description                                                                                                                          |
| ------------------ | ------------------------------------------------------------------------------------------------------------------------------------ |
| `appraiser.py`     | Factory for the Appraiser agent (`create_appraiser_agent`).                                                                          |
| `system_prompt.py` | The expert valuation persona and method-selection / distribution instructions for the agent.                                         |
| `schema.py`        | `AppraiserInput` (pipeline inputs) and method-agnostic `AppraiserOutput` (`IntrinsicValueDistribution` + method evidence summaries). |
| `user_prompt.py`   | `create_user_prompt(appraiser_input=...)`: tagged JSON blocks + explicit caller-supplied `risk_free_rate_pct` (percentage points).   |
| `__init__.py`      | Package initialization for the appraiser module.                                                                                     |

## Subdirectories

None.

## For AI Agents

### Working In This Directory

- **Agent Tools**: By default (`use_perplexity=False`), the agent uses pydantic-ai `WebSearch` and `WebFetch` capabilities, which use provider-native tools where supported and Pydantic AI local fallbacks otherwise. With `use_perplexity=True`, Perplexity-backed tools (`web_search`, `sec_filings_search`) are provided by `discount_analyst.integrations.perplexity` via `create_perplexity_toolset(AgentName.APPRAISER)`. When `use_mcp_financial_data=True` (default), EODHD and FMP MCP toolsets are added for Anthropic, OpenAI, and DeepSeek via `add_required_feature_to_builtin_tools` (`ProviderFeature.MCP`). Google does not support MCP—use `use_mcp_financial_data=False` or `scripts/agents/run_appraiser.py --no-mcp`. Add or modify Perplexity-specific descriptions in `agents/common/tool_descriptions.py`.
- **Prompts**: Keep the system persona in `system_prompt.py` and the user-facing instruction logic in `user_prompt.py`. Appraiser prompts must stay valuation-only: no Buy/Hold/Sell ratings, no recommended actions, and no mandatory DCF workflow.

### Testing Requirements

- Verify agent behavior by adding or updating integration tests in `tests/`. Ensure external API calls (Perplexity, LLMs) are mocked to prevent non-deterministic results and cost.
- Run tests using `uv run pytest`.

### Common Patterns

- **Search Tools**: Uses `AsyncPerplexity` with `search_mode="web"` for general research and `search_mode="sec"` for official financial filings.
- **Structured I/O**: Input contract `AppraiserInput` and output `AppraiserOutput` live in `schema.py`. `AppraiserOutput` requires one primary method, at least one cross-check, monotonic p10/p25/p50/p75/p90 intrinsic values, and an expected intrinsic value within the p10-p90 range. `scripts/agents/run_appraiser.py` resolves `AppraiserInput` from a Sentinel run artefact (and embedded paths to Surveyor / Researcher / Strategist JSON); other callers (e.g. workflows) build `AppraiserInput` in code and call `user_prompt.create_user_prompt`.

## Dependencies

### Internal

- `discount_analyst.agents.appraiser.schema`: For `AppraiserInput` and `AppraiserOutput`.
- `discount_analyst.agents.surveyor.schema`, `researcher.schema`, `strategist.schema`, `sentinel.schema`: Structured inputs embedded in the user prompt via `AppraiserInput`.
- `discount_analyst.config.ai_models_config`: For model configuration and selection.
- `common.config`: For API keys and rate limit settings.
- `discount_analyst.agents.common.model`: For creating the LLM model instance.
- `discount_analyst.integrations.perplexity`: For Perplexity-backed search tools via `create_perplexity_toolset(AgentName.APPRAISER)`.
- `discount_analyst.agents.common.tool_support`: MCP toolset wiring via `add_required_feature_to_builtin_tools`.
- `discount_analyst.integrations.financial_data_mcp`: EODHD/FMP `MCPToolset` factories.

### External

- **pydantic-ai**: The agent framework used to build the appraiser.
- **perplexityai**: Used for the `web_search` and `sec_filings_search` tools.
- **aiolimiter**: Manages asynchronous rate limiting for the Perplexity API.
- **pydantic**: Used for internal and shared data models.

<!-- MANUAL: Any manually added notes below this line are preserved on regeneration -->
