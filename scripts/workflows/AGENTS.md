<!-- Parent: ../AGENTS.md -->
<!-- Generated: 2026-04-05 | Updated: 2026-04-05 -->

# workflows

## Purpose

Contains orchestration scripts that run multiple agents in sequence: Surveyor once, then Researcher per candidate, then Strategist per successful Researcher run (full pipeline), with JSON artifacts per stage. The Researcher-only variant skips Strategist. `discount_analyst/workflows/run_surveyor_researcher_strategist.py` is a thin compatibility entry point that delegates to `run_surveyor_researcher_strategist` in this package.

## Key Files

| File                                    | Description                                                                                                                    |
| --------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------ |
| `run_surveyor_researcher_strategist.py` | Surveyor discovery, sequential Researcher per candidate, then Strategist per successful Researcher (artifacts for each stage). |
| `run_surveyor_then_researcher.py`       | Surveyor discovery, then sequential Researcher-only flow (no Strategist stage).                                                |
| `__init__.py`                           | Package initialization for workflow scripts.                                                                                   |

## Subdirectories

None.

## For AI Agents

### Working In This Directory

- Keep workflows orchestration-only: core agent logic should stay in `discount_analyst/agents/`.
- Preserve sequential execution semantics for candidate processing unless explicitly changed.
- Continue-on-error is intentional for per-candidate Researcher failures and per-success Strategist failures; retain final failure summary tables.

### Testing Requirements

- Run `uv run ruff check scripts/workflows`.
- Run `uv run pytest`.
- For manual verification: `uv run python scripts/workflows/run_surveyor_researcher_strategist.py` and/or `uv run python discount_analyst/workflows/run_surveyor_researcher_strategist.py --help`.

### Common Patterns

- Use `discount_analyst.shared.ai.streamed_agent_run.run_streamed_agent` for every agent run.
- Persist outputs via `scripts.shared.outputs.write_agent_json` with clear agent-specific suffixes.
- Compatibility wrappers under `discount_analyst/workflows/` should import `main` from `scripts.workflows.*` and call `asyncio.run(main())`.

## Dependencies

### Internal

- `discount_analyst.agents.surveyor`: Surveyor factory and prompt.
- `discount_analyst.agents.researcher`: Researcher factory and prompt builder.
- `discount_analyst.agents.strategist`: Strategist factory and prompt builder.
- `scripts.shared.cli`, `scripts.shared.outputs`, `scripts.shared.schemas.run_outputs`, `scripts.shared.usage`: CLI helpers, JSON writer, run-output models, usage extraction.

### External

- **rich**: Console panels/tables for workflow progress and summaries.

<!-- MANUAL: Any manually added notes below this line are preserved on regeneration -->
