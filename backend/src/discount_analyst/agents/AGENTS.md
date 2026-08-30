<!-- Parent: ../AGENTS.md -->
<!-- Generated: 2026-04-02 | Updated: 2026-05-31 -->

# agents

## Purpose

Contains AI agent packages used by the project workflows. This directory groups the Surveyor, Researcher, Strategist, Sentinel, and Appraiser implementations under a shared namespace.

## Key Files

| File          | Description                                                |
| ------------- | ---------------------------------------------------------- |
| `__init__.py` | Package initialization file for `discount_analyst.agents`. |

## Subdirectories

| Directory     | Purpose                                                                                                               |
| ------------- | --------------------------------------------------------------------------------------------------------------------- |
| `tools/`          | Agent tool clients: web research, Frankfurter FX, MCP, terminal, official regulatory data (see `tools/AGENTS.md`) |
| `runtime/`        | Shared agent factory, model construction, streaming (see `runtime/AGENTS.md`)                                     |
| `common_prompts/` | Shared creed, MCP rules, and official filing/universe prompt snippets                                             |
| `surveyor/`       | Surveyor agent implementation and prompts for candidate discovery (see `surveyor/AGENTS.md`)                      |
| `researcher/` | Researcher agent implementation and prompts for structured deep-research evidence output (see `researcher/AGENTS.md`) |
| `strategist/` | Strategist agent implementation and prompts for `MispricingThesis` output (see `strategist/AGENTS.md`)                |
| `sentinel/`   | Sentinel agent implementation and prompts for `EvaluationReport` output (see `sentinel/AGENTS.md`)                    |
| `appraiser/`  | Appraiser agent implementation and prompts for method-agnostic valuation distributions (see `appraiser/AGENTS.md`)    |

## For AI Agents

### Working In This Directory

- Keep surveyor, researcher, strategist, sentinel, and appraiser code in separate subpackages to avoid cross-coupling.
- Use fully qualified imports from `discount_analyst.agents.*` in callers.

### Testing Requirements

- Run `uv run pytest` after moving or changing agent package imports.

### Common Patterns

- Agent factories live in each subpackage's main module (`surveyor.py`, `researcher.py`, `sentinel.py`, `appraiser.py`).
- Prompt definitions stay inside their owning subpackage.

## Dependencies

### Internal

- `discount_analyst.agents.common`, `discount_analyst.config`, `discount_analyst.integrations`, `discount_analyst.valuation` (schemas only where needed): runtime and contracts for agent construction.
- `scripts/agents`: CLI entry points that call these factories.

### External

- **pydantic-ai**: Agent framework used by both subpackages.
- **pydantic-ai-harness**: `ToolOutputLimits` truncation of oversized tool returns.

<!-- MANUAL: Any manually added notes below this line are preserved on regeneration -->
