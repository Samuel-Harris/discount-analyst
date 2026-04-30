<!-- Parent: ../AGENTS.md -->
<!-- Generated: 2026-04-05 -->

# scripts/common

## Purpose

Shared helpers for `scripts/` entry points: CLI defaults, output paths, JSON artefact writers, run-output Pydantic models, and usage extraction.

## Key Files

| File             | Description                                                                                |
| ---------------- | ------------------------------------------------------------------------------------------ |
| `cli.py`         | `DEFAULT_AGENT_CLI_DEFAULTS`, argparse helpers.                                            |
| `constants.py`   | `SCRIPTS_OUTPUTS_DIR`.                                                                     |
| `artefacts.py`   | `write_agent_json`, `write_verdicts_json` (`list[Verdict]` → `*-VERDICTS.json`).           |
| `run_outputs.py` | `SurveyorRunOutput`, `ResearcherRunOutput`, `AppraiserRunOutput`, `ArbiterRunOutput`, etc. |
| `usage.py`       | `extract_turn_usage`.                                                                      |

## Dependencies

### Internal

- `discount_analyst.config`, `discount_analyst.agents.*.schema`, `discount_analyst.valuation.data_types` (for DCF fields in run outputs).
