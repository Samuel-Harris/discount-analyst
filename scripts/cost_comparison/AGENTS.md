<!-- Parent: ../AGENTS.md -->
<!-- Generated: 2026-02-24 | Updated: 2026-02-24 -->

# cost_comparison

## Purpose

Scripts and assets for comparing cost and speed across AI models when running the Market Analyst agent. Used to evaluate per-model token usage, cache usage, and dollar cost for a fixed workload (e.g. one ticker + research report).

## Key Files

| File                       | Description                                                                                                                                                                                                                                                                    |
| -------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `model_cost_comparison.py` | CLI script that runs the Market Analyst agent across one or all configured models, records timing and token usage, prints Rich tables for speed/tokens and cost breakdown, runs DCF valuation on each agent output, and writes a combined `ModelRunOutput` JSON to `outputs/`. |

## Subdirectories

| Directory  | Purpose                                                                                                                  |
| ---------- | ------------------------------------------------------------------------------------------------------------------------ |
| `inputs/`  | Input research reports (e.g. `amzn.md`). Default report resolved from here.                                              |
| `outputs/` | Per-model JSON output files written after each successful run (gitignored). Filenames: `{YYYYMMDDTHHMMSS}-{model}-{cache \| no-cache}-{ticker}.json`. |

## For AI Agents

### Working In This Directory

- **Pricing**: Cost is computed with **genai-prices** when the model is in its snapshot; otherwise the script uses the `MODEL_PRICING_FALLBACK` dict. Update `MODEL_PRICING_FALLBACK` only for models not yet in genai-prices.
- **Rich**: Use the `rich` library for all terminal output (tables, console) per project rules.
- **CLI**: Keep `argparse` for CLI; default ticker `AMZN`, default risk-free rate `0.045`, default report `scripts/cost_comparison/inputs/amzn.md` (resolved relative to the script file). `--caching` (`enabled` | `disabled` | `both`, default `both`) controls prompt caching: Anthropic's `anthropic_cache_messages` is toggled; OpenAI and Gemini auto-cache and are skipped when `disabled`. `--dry-run` prints a table of configs that would run (model, cache mode, output filename) and exits without making API calls.
- **Outputs**: After each successful model run the script (1) runs `DCFAnalysis` on the agent output and (2) serialises a `ModelRunOutput` (ticker, model_name, risk_free_rate, market_analyst output, dcf_result, dcf_error) to `outputs/{timestamp}-{model}-{cache|no-cache}-{ticker}.json`. DCF errors are caught and stored in `dcf_error` without failing the whole run. A shared timestamp is generated once before the run loop so all files from one invocation share the same prefix.

### Testing Requirements

- No automated tests; run the script manually with `--model <name>` to verify a single model, or without `--model` to run all (requires API keys and network).

### Common Patterns

- **Run flow**: For each model, build `AIModelsConfig(model_name=...)`, create agent via `create_market_analyst_agent()`, run with `agent.run_stream(..., usage_limits=...)` (streaming is required by Anthropic for long requests). Drain `streamed_run.stream_output(debounce_by=None)` silently, then call `await streamed_run.get_output()` and `streamed_run.usage()` after the context manager exits. Cost: try `genai_prices.calc_price(usage, model_ref, provider_id)`; on `LookupError` use `MODEL_PRICING_FALLBACK` and manual $/MTok. Use `RunResult.has_usage()` (mirrors `UsageBase.has_values()`) to show "no usage" when no tokens were recorded.
- **Errors**: Per-model errors are caught, logged, and shown as a row in the result tables instead of failing the whole run.

## Dependencies

### Internal

- `discount_analyst.shared.ai_models_config`: `ModelName`, `AIModelsConfig`.
- `discount_analyst.shared.data_types`: `MarketAnalystOutput` (for typing the `RunResult.output` field).
- `discount_analyst.dcf_analysis`: `DCFAnalysis`, `DCFAnalysisParameters`, `DCFAnalysisResult`.
- `discount_analyst.market_analyst`: `create_market_analyst_agent`, `create_user_prompt`.

### External

- **rich**: Console and table output.
- **pydantic-ai**: Agent run and usage (`RunUsage`).
- **genai-prices**: Actual cost from usage (`calc_price`, `Usage`); fallback to built-in `MODEL_PRICING_FALLBACK` when the model is not in the snapshot.
