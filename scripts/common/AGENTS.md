<!-- Parent: ../AGENTS.md -->
<!-- Generated: 2026-04-05 -->

# scripts/common

## Purpose

Shared helpers for `scripts/` entry points: CLI defaults, output paths, JSON artifact writers, run-output Pydantic models, usage extraction, and cost-comparison types.

## Key Files

| File             | Description                                                            |
| ---------------- | ---------------------------------------------------------------------- |
| `cli.py`         | `DEFAULT_AGENT_CLI_DEFAULTS`, argparse helpers.                        |
| `constants.py`   | `SCRIPTS_OUTPUTS_DIR`, `AUTO_CACHE_MODELS`.                            |
| `artifacts.py`   | `write_agent_json`, `write_model_output`, `output_filename`.           |
| `run_outputs.py` | `SurveyorRunOutput`, `ResearcherRunOutput`, `AppraiserRunOutput`, etc. |
| `usage.py`       | `extract_turn_usage`.                                                  |
| `cost.py`        | Cost types and `genai-prices` integration.                             |

## Dependencies

### Internal

- `discount_analyst.config`, `discount_analyst.agents.*.schema`, `discount_analyst.valuation.data_types` (for DCF fields in run outputs).
