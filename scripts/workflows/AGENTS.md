<!-- Parent: ../AGENTS.md -->
<!-- Generated: 2026-04-05 | Updated: 2026-04-05 -->

# workflows

## Purpose

Contains orchestration scripts that run multiple agents in sequence with JSON artefacts per stage. Canonical implementations live in this package under `scripts/workflows/`.

## Key Files

| File                                    | Description                                                                                                                                                                                                           |
| --------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `run_surveyor_then_researcher.py`       | Surveyor discovery, then sequential Researcher per candidate (no Strategist).                                                                                                                                         |
| `run_surveyor_researcher_strategist.py` | Surveyor discovery, sequential Researcher per candidate, then Strategist per successful Researcher.                                                                                                                   |
| `run_surveyor_to_sentinel.py`           | Surveyor discovery, sequential Researcher per candidate, then Strategist and Sentinel per successful prior stage.                                                                                                     |
| `run_full_workflow.py`                  | Surveyor discovery, sequential Researcher per candidate, Strategist and Sentinel per successful prior stage; Appraiser + DCF and Arbiter when the Sentinel valuation gate passes; verdicts table + `*-VERDICTS.json`. |
| `__init__.py`                           | Package initialization for workflow scripts.                                                                                                                                                                          |

## Subdirectories

None.

## For AI Agents

### Working In This Directory

- Keep workflows orchestration-only: core agent logic should stay in `discount_analyst/agents/`.
- Preserve sequential execution semantics for candidate processing unless explicitly changed.
- Continue-on-error is intentional for per-candidate Researcher failures and per-success Strategist/Sentinel failures; retain final failure summary tables.

### Testing Requirements

- Run `uv run ruff check scripts/workflows`.
- Run `uv run pytest`.
- For manual verification: `uv run python scripts/workflows/run_surveyor_then_researcher.py --help`, `uv run python scripts/workflows/run_surveyor_researcher_strategist.py --help`, `uv run python scripts/workflows/run_surveyor_to_sentinel.py --help`, and/or `uv run python scripts/workflows/run_full_workflow.py --help`.

### Common Patterns

- Use `discount_analyst.agents.common.streamed_agent_run.run_streamed_agent` for every agent run.
- Persist outputs via `scripts.common.artefacts.write_agent_json` with clear agent-specific suffixes.

## Dependencies

### Internal

- `discount_analyst.agents.surveyor`: Surveyor factory and prompt.
- `discount_analyst.agents.researcher`: Researcher factory and prompt builder.
- `discount_analyst.agents.strategist`: Strategist factory and prompt builder.
- `discount_analyst.agents.sentinel`: Sentinel factory and prompt builder.
- `scripts.common.cli`, `scripts.common.artefacts`, `scripts.common.run_outputs`, `scripts.common.usage`: CLI helpers, JSON writer, run-output models, usage extraction.

### External

- **rich**: Console panels/tables for workflow progress and summaries.

<!-- MANUAL: Any manually added notes below this line are preserved on regeneration -->
