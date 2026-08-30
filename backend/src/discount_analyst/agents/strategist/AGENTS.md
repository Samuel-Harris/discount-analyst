<!-- Parent: ../AGENTS.md -->
<!-- Generated: 2026-04-04 | Updated: 2026-08-28 -->

# strategist

## Purpose

The `strategist` directory contains the implementation of the "Strategist" AI agent. This agent consumes a `SurveyorCandidate` plus a `DeepResearchReport` and produces a structured `MispricingThesis` focused on falsifiable interpretation. It shares the same web/MCP/terminal flags as the other pipeline agents, plus always-on Frankfurter FX.

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

- **Agent tools**: Same flag contract as Surveyor. Default (`use_perplexity=False`) uses pydantic-ai `WebSearch` and `WebFetch`. With `use_perplexity=True`, Perplexity tools come from `create_perplexity_toolset(AgentName.STRATEGIST)` — descriptions are optional checks to falsify a packed-context claim, not a licence to re-run research. MCP follows `use_mcp_financial_data` (False for Google / `--no-mcp`). Frankfurter `convert_currency` and official filing tools are always attached. Terminal follows `settings.use_terminal` / `--no-terminal`.
- **Output contract**: Keep output constrained to `MispricingThesis` in `schema.py`. `evaluation_questions` must be answerable from the last reported period plus the last trading update; do not make a future print load-bearing.

### Testing Requirements

- Run `uv run ruff check discount_analyst/agents/strategist`.
- Run `uv run pytest` for full-suite validation.

### Common Patterns

- **Structured output**: Always return `MispricingThesis` and pass context via `user_prompt.create_user_prompt`.

## Dependencies

### Internal

- `discount_analyst.agents.strategist.schema`: Output contract (`MispricingThesis`).
- `discount_analyst.agents.researcher.schema`: `DeepResearchReport` input.
- `discount_analyst.agents.surveyor.schema`: `SurveyorCandidate` input.

### External

- **pydantic-ai**: Agent construction and structured output.
- **pydantic**: Data model validation via stage-local schemas.

<!-- MANUAL: Any manually added notes below this line are preserved on regeneration -->
