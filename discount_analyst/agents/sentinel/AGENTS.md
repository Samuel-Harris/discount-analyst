<!-- Parent: ../AGENTS.md -->
<!-- Generated: 2026-04-05 -->

# sentinel

## Purpose

The `sentinel` directory contains the Sentinel AI agent. It consumes a `SurveyorCandidate`, `DeepResearchReport`, and `MispricingThesis` and produces an `EvaluationReport` (question assessments, red-flag screen, verdict, recommendation).

## Key Files

| File               | Description                                                                           |
| ------------------ | ------------------------------------------------------------------------------------- |
| `sentinel.py`      | Factory for the Sentinel agent (`create_sentinel_agent`).                             |
| `schema.py`        | Output contract: `EvaluationReport`, `QuestionAssessment`, `RedFlagScreen`.           |
| `system_prompt.py` | System prompt and Sentinel role instructions.                                         |
| `user_prompt.py`   | `create_user_prompt`: injects candidate, deep research, and thesis as tagged context. |
| `__init__.py`      | Package initialization for the sentinel module.                                       |

## Subdirectories

None.

## For AI Agents

### Working In This Directory

- **No tools**: The Sentinel agent is evaluation-only; do not add web search, fetch, Perplexity, or MCP without an explicit product decision.
- **Output contract**: Keep output constrained to `EvaluationReport` in `schema.py`.

### Testing Requirements

- Run `uv run ruff check discount_analyst/agents/sentinel`.
- Run `uv run pytest` for full-suite validation.

### Common Patterns

- **Structured output**: Always return `EvaluationReport` and pass context via `user_prompt.create_user_prompt`.

## Dependencies

### Internal

- `discount_analyst.agents.sentinel.schema`: Output contract (`EvaluationReport`).
- `discount_analyst.agents.researcher.schema`: `DeepResearchReport` input.
- `discount_analyst.agents.strategist.schema`: `MispricingThesis` input.
- `discount_analyst.agents.surveyor.schema`: `SurveyorCandidate` input.

### External

- **pydantic-ai**: Agent construction and structured output.
- **pydantic**: Data model validation via shared schemas.

<!-- MANUAL: Any manually added notes below this line are preserved on regeneration -->
