<!-- Parent: ../AGENTS.md -->
<!-- Generated: 2026-04-05 | Updated: 2026-05-31 -->

# scripts/common

## Purpose

Shared helpers for `scripts/` entry points: CLI defaults, output paths, JSON artefact writers, run-output Pydantic models, and usage extraction.

## Key Files

| File                       | Description                                                                                      |
| -------------------------- | ------------------------------------------------------------------------------------------------ |
| `appraiser_run_context.py` | `AppraiserRunContext`: CLI/workflow metadata for a single Appraiser run (candidate, RFR, model). |
| `cli.py`                   | `DEFAULT_AGENT_CLI_DEFAULTS`, `add_agent_terminal_argument`, `terminal_run_options_for_cli`.     |
| `constants.py`             | `SCRIPTS_OUTPUTS_DIR`.                                                                           |
| `artefacts.py`             | `write_agent_json`, `write_verdicts_json` (`list[Verdict]` → `*-VERDICTS.json`).                 |
| `run_outputs.py`           | `SurveyorRunOutput`, `ResearcherRunOutput`, method-agnostic `AppraiserRunOutput`, etc.           |
| `usage.py`                 | `extract_turn_usage`.                                                                            |

## Dependencies

### Internal

- `discount_analyst.config`, `discount_analyst.agents.*.schema`, and pipeline verdict schemas.
