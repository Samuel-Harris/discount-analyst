<!-- Parent: ../AGENTS.md -->
<!-- Generated: 2026-04-05 | Updated: 2026-08-15 -->

# sentinel

## Purpose

The `sentinel` directory contains the Sentinel AI agent. It consumes a `SurveyorCandidate`, `DeepResearchReport`, and `MispricingThesis` and produces an `EvaluationReport` (question assessments, red-flag screen, `thesis_verdict`). Whether to run valuation is **derived** via `sentinel_proceeds_to_valuation(evaluation)` in `schema.py` (thesis proceed set **and** red-flag screen — blocks on ``Serious concern``) — there is no stored `recommendation` field.

## Key Files

| File               | Description                                                                                                                   |
| ------------------ | ----------------------------------------------------------------------------------------------------------------------------- |
| `sentinel.py`      | Factory for the Sentinel agent (`create_sentinel_agent`).                                                                     |
| `schema.py`        | Output contract: `EvaluationReport`, `ThesisVerdict` / `OverallRedFlagVerdict` (`StrEnum`), `sentinel_proceeds_to_valuation`. |
| `system_prompt.py` | System prompt and Sentinel role instructions.                                                                                 |
| `user_prompt.py`   | `create_user_prompt`: injects candidate, deep research, and thesis as tagged context.                                         |
| `__init__.py`      | Package initialization for the sentinel module.                                                                               |

## Subdirectories

None.

## For AI Agents

### Working In This Directory

- **Agent tools**: Same flag contract as Surveyor. Default (`use_perplexity=False`) uses pydantic-ai `WebSearch` and `WebFetch`. With `use_perplexity=True`, Perplexity tools come from `create_perplexity_toolset(AgentName.SENTINEL)` — descriptions are optional checks to verify a red flag or filing fact, not a licence to re-run research. MCP follows `use_mcp_financial_data` (False for Google / `--no-mcp`). Frankfurter `convert_currency` is always attached. Terminal follows `settings.use_terminal` / `--no-terminal`.
- **Output contract**: Keep output constrained to `EvaluationReport` in `schema.py`. Use `sentinel_proceeds_to_valuation(evaluation)` for the valuation gate; do not add a duplicate persisted recommendation field.

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
