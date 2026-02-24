<!-- Parent: ../AGENTS.md -->
<!-- Generated: 2026-02-24 | Updated: 2026-02-24 -->

# cost_comparison

## Purpose

Scripts and assets for comparing cost and speed across AI models when running the Market Analyst agent. Used to evaluate per-model token usage, cache usage, and dollar cost for a fixed workload (e.g. one ticker + research report).

## Key Files

| File | Description |
| --------- | ---------------------------- |
| `model_cost_comparison.py` | CLI script that runs the Market Analyst agent across one or all configured models, records timing and token usage, and prints Rich tables for speed/tokens and cost breakdown. |
| `amzn.md` | Default research report (AMZN) used when `--research-report-path` is not set. |

## Subdirectories

None.

## For AI Agents

### Working In This Directory

- **Pricing**: Cost is computed with **genai-prices** when the model is in its snapshot; otherwise the script uses the `MODEL_PRICING_FALLBACK` dict. Update `MODEL_PRICING_FALLBACK` only for models not yet in genai-prices.
- **Rich**: Use the `rich` library for all terminal output (tables, console) per project rules.
- **CLI**: Keep `argparse` for CLI; default ticker `AMZN`, default report `scripts/cost_comparison/amzn.md` (resolved from repo root).

### Testing Requirements

- No automated tests; run the script manually with `--model <name>` to verify a single model, or without `--model` to run all (requires API keys and network).

### Common Patterns

- **Run flow**: For each model, build `AIModelsConfig(model_name=...)`, create agent via `create_market_analyst_agent()`, run with `agent.iter(..., usage_limits=...)`, consume iteration, then read `agent_run.usage()`. Cost: try `genai_prices.calc_price(usage, model_ref, provider_id)`; on `LookupError` use `MODEL_PRICING_FALLBACK` and manual $/MTok. Use `RunResult.has_usage()` (mirrors `UsageBase.has_values()`) to show "no usage" when no tokens were recorded.
- **Errors**: Per-model errors are caught, logged, and shown as a row in the result tables instead of failing the whole run.

## Dependencies

### Internal

- `discount_analyst.shared.ai_models_config`: `ModelName`, `AIModelsConfig`.
- `discount_analyst.market_analyst`: `create_market_analyst_agent`, `create_user_prompt`.

### External

- **rich**: Console and table output.
- **pydantic-ai**: Agent run and usage (`RunUsage`).
- **genai-prices**: Actual cost from usage (`calc_price`, `Usage`); fallback to built-in `MODEL_PRICING_FALLBACK` when the model is not in the snapshot.
