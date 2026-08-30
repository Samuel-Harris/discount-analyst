<!-- Parent: ../AGENTS.md -->
<!-- Generated: 2026-04-02 | Updated: 2026-08-30 -->

# agents

## Purpose

Contains AI agent packages used by the project workflows. This directory groups the Surveyor, Profiler, Researcher, Strategist, Sentinel, and Appraiser implementations under a shared namespace.

## Key Files

| File          | Description                                                |
| ------------- | ---------------------------------------------------------- |
| `__init__.py` | Package initialization file for `discount_analyst.agents`. |

## Subdirectories

| Directory     | Purpose                                                                                                               |
| ------------- | --------------------------------------------------------------------------------------------------------------------- |
| `tools/`          | Agent tool clients: web research, Frankfurter FX, MCP, terminal, official regulatory data (see `tools/AGENTS.md`) |
| `runtime/`        | Shared agent factory, model construction, streaming (see `runtime/AGENTS.md`)                                     |
| `common_prompts/` | Shared creed, market-data source rules, and official filing/universe prompt snippets                            |
| `surveyor/`       | Surveyor agent implementation and prompts for candidate discovery (see `surveyor/AGENTS.md`)                      |
| `profiler/`       | Profiler implementation and prompts for named-ticker screening                                                   |
| `researcher/` | Researcher agent implementation and prompts for structured deep-research evidence output (see `researcher/AGENTS.md`) |
| `strategist/` | Strategist agent implementation and prompts for `MispricingThesis` output (see `strategist/AGENTS.md`)                |
| `sentinel/`   | Sentinel agent implementation and prompts for `EvaluationReport` output (see `sentinel/AGENTS.md`)                    |
| `appraiser/`  | Appraiser agent implementation and prompts for method-agnostic valuation distributions (see `appraiser/AGENTS.md`)    |

## For AI Agents

### Working In This Directory

- Keep each stage's code in its own subpackage to avoid cross-coupling.
- Use fully qualified imports from `discount_analyst.agents.*` in callers.

### Testing Requirements

- Run `uv run pytest` after moving or changing agent package imports.

### Common Patterns

- Agent factories live in each stage subpackage's matching module.
- Prompt definitions stay inside their owning subpackage.

## Dependencies

### Internal

- `discount_analyst.agents.runtime`, `discount_analyst.agents.tools`, `discount_analyst.config`, and `discount_analyst.domain`: runtime, capabilities, configuration, and shared domain contracts.
- `discount_analyst.entrypoints.cli.agents`: one-shot CLI entry points that call the stage factories.

### External

- **pydantic-ai**: Agent framework used by the stage packages.
- **pydantic-ai-harness**: `ToolOutputLimits` truncation of oversized tool returns.

<!-- MANUAL: Any manually added notes below this line are preserved on regeneration -->
