<!-- Parent: ../AGENTS.md -->
<!-- Generated: 2026-04-05 -->

# arbiter

## Purpose

The `arbiter` directory contains the Arbiter AI agent. It consumes a `SurveyorCandidate`, `DeepResearchReport`, and `MispricingThesis` and produces an `EvaluationReport` (question assessments, red-flag screen, verdict, recommendation).

## Key Files

| File             | Description                                                                                         |
| ---------------- | --------------------------------------------------------------------------------------------------- |
| `arbiter.py`     | Factory for the Arbiter agent (`create_arbiter_agent`).                                            |
| `system_prompt.py` | System prompt (placeholder until filled in).                                                     |
| `user_prompt.py` | `create_user_prompt`: injects candidate, deep research, and thesis as tagged JSON.                 |
| `__init__.py`    | Package initialization for the arbiter module.                                                     |

## Subdirectories

None.

## For AI Agents

### Working In This Directory

- **No tools**: The Arbiter agent is evaluation-only; do not add web search, fetch, Perplexity, or MCP without an explicit product decision.
- **Output contract**: Keep output constrained to `EvaluationReport` in `shared/schemas/arbiter.py`.

### Testing Requirements

- Run `uv run ruff check discount_analyst/agents/arbiter`.
- Run `uv run pytest` for full-suite validation.

### Common Patterns

- **Structured output**: Always return `EvaluationReport` and pass context via `user_prompt.create_user_prompt`.

## Dependencies

### Internal

- `discount_analyst.shared.schemas.arbiter`: Output contract (`EvaluationReport`).
- `discount_analyst.shared.schemas.researcher`: `DeepResearchReport` input.
- `discount_analyst.shared.schemas.strategist`: `MispricingThesis` input.
- `discount_analyst.shared.schemas.surveyor`: `SurveyorCandidate` input.

### External

- **pydantic-ai**: Agent construction and structured output.
- **pydantic**: Data model validation via shared schemas.

<!-- MANUAL: Any manually added notes below this line are preserved on regeneration -->
