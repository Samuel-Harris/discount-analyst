<!-- Parent: ../AGENTS.md -->
<!-- Generated: 2026-02-24 | Updated: 2026-04-02 -->

# cost_comparison

## Purpose

Scripts and assets for comparing cost and speed across AI models when running the Appraiser agent. Used to evaluate per-model token usage, cache usage, and dollar cost for a fixed workload (one ticker + the same structured inputs as `run_appraiser`).

## Key Files

| File                       | Description                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             |
| -------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `model_cost_comparison.py` | CLI script that runs the Appraiser agent across one or all configured models, records timing and token usage, prints Rich tables for speed/tokens and cost breakdown, runs DCF valuation on each agent output, and writes a combined `AppraiserRunOutput` JSON under `scripts/cost_comparison/outputs/`.                                                                                                                                                                                                                                                                                                                |
| `view_ticker_results.py`   | CLI script that takes a ticker as a positional argument, loads all matching JSON files from `outputs/`, and pretty-prints a Rich summary table. Use `--detail` for side-by-side Stock Data / Assumptions panels per run; add `--reasoning` to also display the model's full reasoning text. Use `--compare-cache` to compare cost/speed for cache vs no-cache per model; use `--compare-cost` to compare cost, speed, and token usage (input/output/cache write/read) across all models; use `--compare-web-search` to compare built-in web search vs Perplexity with tool cost ($0.005/call) and total estimated cost. |
| `scatter_plot.py`          | Standalone script that writes a static accuracy-vs-cost scatter PNG next to the script (requires **matplotlib**, listed in the project dev dependency group).                                                                                                                                                                                                                                                                                                                                                                                                                                                           |

## Subdirectories

| Directory  | Purpose                                                                                                                                                                                                              |
| ---------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `inputs/`  | Default paths for Appraiser inputs: `*-surveyor-report.json`, `*-deep-research.json`, `*-mispricing-thesis.json`, `*-evaluation-report.json` (or use `--appraiser-input-dir` for the `run_appraiser` folder layout). |
| `outputs/` | Per-model JSON output files written after each successful run (gitignored). Filenames: `{YYYYMMDDTHHMMSS}-{model}-{cache \| no-cache}-{ticker}.json`.                                                                |

## For AI Agents

### Working In This Directory

- **Pricing**: Cost is computed with **genai-prices** when the model is in its snapshot; otherwise the script uses `scripts.common.cost.MODEL_PRICING_FALLBACK`. Update that dict only for models not yet in genai-prices.
- **Rich**: Use the `rich` library for all terminal output (tables, console) per project rules.
- **CLI**: Keep `argparse` for CLI; `--ticker` is required. Load inputs via `--appraiser-input-dir` (four fixed JSON filenames, same as `run_appraiser --dir`) or individual paths defaulting to `inputs/{ticker}-surveyor-report.json`, `inputs/{ticker}-deep-research.json`, `inputs/{ticker}-mispricing-thesis.json`, `inputs/{ticker}-evaluation-report.json`. Files may be raw agent outputs or full `*RunOutput` JSON from `scripts/outputs/` (loader unwraps). Default risk-free rate `0.037276`. `--caching` (`enabled` | `disabled` | `both`, default `both`) controls prompt caching: Anthropic's `anthropic_cache_messages` is toggled; OpenAI and Gemini auto-cache and are skipped when `disabled`. `--dry-run` prints a table of configs that would run (model, cache mode, web search, MCP, output filename) and exits without making API calls. `--no-mcp` omits EODHD/FMP MCP toolsets (use with Google models).
- **Outputs**: After each successful model run the script (1) runs `DCFAnalysis` on the agent output and (2) serialises an `AppraiserRunOutput` (ticker, model_name, risk_free_rate, appraiser output, dcf_result, dcf_error, turn_usage, …) to `outputs/{timestamp}-{model}-{cache|no-cache}-{web-search|perplexity}-{ticker}.json` under this directory. DCF errors are caught and stored in `dcf_error` without failing the whole run. A shared timestamp is generated once before the run loop so all files from one invocation share the same prefix.

### Testing Requirements

- No automated tests; run the script manually with `--model <name>` to verify a single model, or without `--model` to run all (requires API keys and network).

### Common Patterns

- **Run flow**: For each model, build `AIModelsConfig(model_name=...)`, create agent via `create_appraiser_agent()`, run with `agent.run_stream(..., usage_limits=...)` (streaming is required by Anthropic for long requests). Drain `streamed_run.stream_output(debounce_by=None)` silently, then call `await streamed_run.get_output()` and `streamed_run.usage()` after the context manager exits. Cost: try `genai_prices.calc_price(usage, model_ref, provider_id)`; on `LookupError` use `MODEL_PRICING_FALLBACK` and manual $/MTok. Use `RunResult.has_usage()` (mirrors `UsageBase.has_values()`) to show "no usage" when no tokens were recorded.
- **Errors**: Per-model errors are caught, logged, and shown as a row in the result tables instead of failing the whole run.

## Dependencies

### Internal

- `scripts.common.constants`, `scripts.common.cost`, `scripts.common.artifacts`, `scripts.common.run_outputs`, `scripts.common.usage`: run schemas, cost types and calculators, output paths/filenames, usage extraction, `AUTO_CACHE_MODELS` (`model_cost_comparison` passes `output_dir` as `Path(__file__).parent / "outputs"`).
- `discount_analyst.config.ai_models_config`: `ModelName`, `AIModelsConfig` (`view_ticker_results` imports `ModelName` here directly).
- `discount_analyst.agents.appraiser.schema`: `AppraiserOutput` (for typing the `RunResult.output` field).
- `scripts.common.appraiser_input_loader`: builds `AppraiserInput` from paths or directory.
- `discount_analyst.valuation`: `DCFAnalysis`, `DCFAnalysisParameters`, `DCFAnalysisResult`.
- `discount_analyst.agents.appraiser`: `create_appraiser_agent`; `user_prompt.create_user_prompt(appraiser_input=...)` for the prompt string.

### External

- **rich**: Console and table output.
- **pydantic-ai**: Agent run and usage (`RunUsage`).
- **genai-prices**: Actual cost from usage (`calc_price`, `Usage`); fallback to built-in `MODEL_PRICING_FALLBACK` when the model is not in the snapshot.
- **matplotlib** (dev dependency): Used only by `scatter_plot.py` for chart output.
