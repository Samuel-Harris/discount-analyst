<!-- Parent: ../AGENTS.md -->
<!-- Generated: 2026-04-02 | Updated: 2026-04-02 -->

# agents

## Purpose

Contains AI agent packages used by the project workflows. This directory groups the Appraiser and Surveyor implementations under a shared namespace.

## Key Files

| File | Description |
| ---- | ----------- |
| `__init__.py` | Package initialization file for `discount_analyst.agents`. |

## Subdirectories

| Directory | Purpose |
| --------- | ------- |
| `appraiser/` | Appraiser agent implementation and prompts for DCF workflows (see `appraiser/AGENTS.md`) |
| `surveyor/` | Surveyor agent implementation and prompts for candidate discovery (see `surveyor/AGENTS.md`) |

## For AI Agents

### Working In This Directory

- Keep appraiser and surveyor code in separate subpackages to avoid cross-coupling.
- Use fully qualified imports from `discount_analyst.agents.*` in callers.

### Testing Requirements

- Run `uv run pytest` after moving or changing agent package imports.

### Common Patterns

- Agent factories live in each subpackage's main module (`appraiser.py` and `surveyor.py`).
- Prompt definitions stay inside their owning subpackage.

## Dependencies

### Internal

- `discount_analyst.shared`: Shared models, config, and tool wiring for agent construction.
- `scripts/agents`: CLI entry points that call these factories.

### External

- **pydantic-ai**: Agent framework used by both subpackages.

<!-- MANUAL: Any manually added notes below this line are preserved on regeneration -->
