<!-- Parent: ../AGENTS.md -->
<!-- Generated: 2026-04-03 | Updated: 2026-04-03 -->

# workflows

## Purpose

Contains orchestration scripts that run multiple agents in sequence. The initial workflow runs Surveyor once, then executes Researcher sequentially for each returned candidate and writes one artifact per stage.

## Key Files

| File                              | Description                                                                                                        |
| --------------------------------- | ------------------------------------------------------------------------------------------------------------------ |
| `run_surveyor_then_researcher.py` | End-to-end workflow: Surveyor batch discovery followed by sequential Researcher runs for each `SurveyorCandidate`. |
| `__init__.py`                     | Package initialization for workflow scripts.                                                                       |

## Subdirectories

None.

## For AI Agents

### Working In This Directory

- Keep workflows orchestration-only: core agent logic should stay in `discount_analyst/agents/`.
- Preserve sequential execution semantics for candidate processing unless explicitly changed.
- Continue-on-error is intentional for per-candidate Researcher failures; retain final failure summary behavior.

### Testing Requirements

- Run `uv run ruff check discount_analyst/workflows`.
- Run `uv run pytest`.
- For manual verification, run `uv run python discount_analyst/workflows/run_surveyor_then_researcher.py`.

### Common Patterns

- Use `stream_with_retries` for every agent run.
- Persist outputs via `scripts.shared.outputs.write_agent_json` with clear agent-specific suffixes.

## Dependencies

### Internal

- `discount_analyst.agents.surveyor`: Surveyor factory and prompt.
- `discount_analyst.agents.researcher`: Researcher factory and prompt builder.
- `scripts.shared.cli`, `scripts.shared.outputs`, `scripts.shared.schemas.run_outputs`, `scripts.shared.usage`: CLI helpers, JSON writer, run-output models, usage extraction.

### External

- **rich**: Console panels/tables for workflow progress and summaries.

<!-- MANUAL: Any manually added notes below this line are preserved on regeneration -->
