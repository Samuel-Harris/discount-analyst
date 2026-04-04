<!-- Parent: ../AGENTS.md -->
<!-- Generated: 2026-04-05 | Updated: 2026-04-05 -->

# workflows

## Purpose

Compatibility wrappers that preserve historical `discount_analyst/workflows/*` entry-point paths while the executable workflow scripts live under `scripts/workflows/`.

## Key Files

| File                                    | Description                                                                                          |
| --------------------------------------- | ---------------------------------------------------------------------------------------------------- |
| `run_surveyor_researcher_strategist.py` | Compatibility wrapper that delegates to `scripts.workflows.run_surveyor_researcher_strategist.main`. |
| `__init__.py`                           | Package marker for workflow compatibility paths.                                                     |

## Subdirectories

None.

## For AI Agents

### Working In This Directory

- Keep this directory thin: wrappers only, no orchestration/business logic.
- Put real workflow implementations in `scripts/workflows/`.

### Testing Requirements

- Verify wrapper execution: `uv run python discount_analyst/workflows/run_surveyor_researcher_strategist.py --help`.

### Common Patterns

- Wrapper scripts should import `main` from `scripts.workflows.*` and call `asyncio.run(main())`.

## Dependencies

### Internal

- `scripts.workflows`: Canonical workflow implementations.

### External

- Standard library `asyncio` only.

<!-- MANUAL: Any manually added notes below this line are preserved on regeneration -->
