<!-- Parent: ../AGENTS.md -->
<!-- Generated: 2026-04-05 -->

# workflows

## Purpose

Thin compatibility entry points that delegate to canonical orchestration under `scripts/workflows/`.

## Key Files

| File                                    | Description                                                                                        |
| --------------------------------------- | -------------------------------------------------------------------------------------------------- |
| `run_surveyor_researcher_strategist.py` | `asyncio.run(main)` wrapper importing `scripts.workflows.run_surveyor_researcher_strategist.main`. |

## Dependencies

- `scripts/workflows/run_surveyor_researcher_strategist.py` for the full Surveyor → Researcher → Strategist pipeline.
