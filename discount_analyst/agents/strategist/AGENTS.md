<!-- Parent: ../AGENTS.md -->
<!-- Generated: 2026-04-04 -->

# strategist

## Purpose

The `strategist` directory contains the implementation of the "Strategist" AI agent. This agent consumes a `SurveyorCandidate` plus a `DeepResearchReport` and produces a structured `MispricingThesis` focused on falsifiable interpretation (no further research tools).

## Key Files

| File               | Description                                                                                    |
| ------------------ | ---------------------------------------------------------------------------------------------- |
| `strategist.py`    | Factory for the Strategist agent (`create_strategist_agent`).                                  |
| `system_prompt.py` | System prompt (investing creed + Strategist role).                                             |
| `user_prompt.py`   | `create_user_prompt`: injects candidate + deep research context for `MispricingThesis` output. |
| `__init__.py`      | Package initialization for the strategist module.                                              |

## Subdirectories

None.

## For AI Agents

### Working In This Directory

- **No tools**: The Strategist agent is interpretation-only; do not add `WebSearchTool`, `WebFetchTool`, Perplexity, or MCP toolsets without an explicit product decision.
- **Output contract**: Keep output constrained to `MispricingThesis` in `shared/schemas/strategist.py`.

### Testing Requirements

- Run `uv run ruff check discount_analyst/agents/strategist`.
- Run `uv run pytest` for full-suite validation.

### Common Patterns

- **Structured output**: Always return `MispricingThesis` and pass context via `user_prompt.create_user_prompt`.

## Dependencies

### Internal

- `discount_analyst.shared.schemas.strategist`: Output contract (`MispricingThesis`).
- `discount_analyst.shared.schemas.researcher`: `DeepResearchReport` input.
- `discount_analyst.shared.schemas.surveyor`: `SurveyorCandidate` input.

### External

- **pydantic-ai**: Agent construction and structured output.
- **pydantic**: Data model validation via shared schemas.

<!-- MANUAL: Any manually added notes below this line are preserved on regeneration -->
