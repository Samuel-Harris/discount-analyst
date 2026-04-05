<!-- Parent: ../AGENTS.md -->
<!-- Generated: 2026-04-02 | Updated: 2026-04-03 -->

# agents

## Purpose

Contains AI agent packages used by the project workflows. This directory groups the Surveyor, Researcher, Strategist, and Appraiser implementations under a shared namespace.

## Key Files

| File          | Description                                                |
| ------------- | ---------------------------------------------------------- |
| `__init__.py` | Package initialization file for `discount_analyst.agents`. |

## Subdirectories

| Directory     | Purpose                                                                                                               |
| ------------- | --------------------------------------------------------------------------------------------------------------------- |
| `common/`     | Agent runtime: model factory, streaming, tools, creed (see `common/AGENTS.md`).                                       |
| `surveyor/`   | Surveyor agent implementation and prompts for candidate discovery (see `surveyor/AGENTS.md`)                          |
| `researcher/` | Researcher agent implementation and prompts for structured deep-research evidence output (see `researcher/AGENTS.md`) |
| `strategist/` | Strategist agent implementation and prompts for `MispricingThesis` output (see `strategist/AGENTS.md`)                |
| `appraiser/`  | Appraiser agent implementation and prompts for DCF workflows (see `appraiser/AGENTS.md`)                              |

## For AI Agents

### Working In This Directory

- Keep surveyor, researcher, strategist, and appraiser code in separate subpackages to avoid cross-coupling.
- Use fully qualified imports from `discount_analyst.agents.*` in callers.

### Testing Requirements

- Run `uv run pytest` after moving or changing agent package imports.

### Common Patterns

- Agent factories live in each subpackage's main module (`surveyor.py`, `researcher.py`, `appraiser.py`).
- Prompt definitions stay inside their owning subpackage.

## Dependencies

### Internal

- `discount_analyst.agents.common`, `discount_analyst.config`, `discount_analyst.integrations`, `discount_analyst.valuation` (schemas only where needed): runtime and contracts for agent construction.
- `scripts/agents`: CLI entry points that call these factories.

### External

- **pydantic-ai**: Agent framework used by both subpackages.

<!-- MANUAL: Any manually added notes below this line are preserved on regeneration -->
