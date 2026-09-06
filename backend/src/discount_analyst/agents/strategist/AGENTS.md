<!-- Parent: ../AGENTS.md -->
<!-- Generated: 2026-04-04 | Updated: 2026-09-05 -->

# strategist

## Purpose

The `strategist` directory contains the implementation of the "Strategist" AI agent. This agent consumes a `SurveyorCandidate` plus a `DeepResearchReport` and an optional prior `MispricingThesis`, then produces a `StrategistDecision`: `keep_prior` (discriminator only) or `replace` with a nested `MispricingThesis`. Application code (`resolve_live_thesis`) is the only place keep is resolved into a live thesis. It shares the same web/MCP/terminal flags as the other pipeline agents, plus always-on Frankfurter FX.

## Key Files

| File               | Description                                                                                          |
| ------------------ | ---------------------------------------------------------------------------------------------------- |
| `strategist.py`    | Factory for the Strategist agent (`create_strategist_agent`, `output_type=StrategistDecision`).      |
| `schema.py`        | `MispricingThesis` and `StrategistDecision` (single object: `keep_prior` omits `thesis`; `replace` requires nested `MispricingThesis`). |
| `system_prompt.py` | System prompt (investing creed + Strategist role + keep-versus-replace).                             |
| `user_prompt.py`   | `create_user_prompt`: injects candidate, research, and optional `<prior_mispricing_thesis>`.         |
| `__init__.py`      | Package initialization for the strategist module.                                                    |

## Subdirectories

None.

## For AI Agents

### Working In This Directory

- **Agent tools**: Same flag contract as Surveyor. Default (`use_perplexity=False`) uses pydantic-ai `WebSearch` and `WebFetch`. With `use_perplexity=True`, Perplexity tools come from `create_perplexity_toolset(AgentName.STRATEGIST)` — descriptions are optional checks to falsify a packed-context claim, not a licence to re-run research. MCP follows `use_mcp_financial_data` (False for Google / `--no-mcp`). Frankfurter `convert_currency` and official filing tools are always attached. Terminal follows `settings.use_terminal` / `--no-terminal`.
- **Output contract**: Keep output constrained to `StrategistDecision` in `schema.py`. `keep_prior` must not echo thesis fields. `evaluation_questions` on replace must be answerable from the last reported period plus the last trading update; do not make a future print load-bearing. Without a prior thesis, `keep_prior` is forbidden.

### Testing Requirements

- Run `uv run ruff check discount_analyst/agents/strategist`.
- Run `uv run pytest` for full-suite validation.

### Common Patterns

- **Structured output**: Always return `StrategistDecision` and pass context via `user_prompt.create_user_prompt`. One-shot CLI is `uv run discount-analyst agent strategist --prior-thesis PATH`.

## Dependencies

### Internal

- `discount_analyst.agents.strategist.schema`: Output contract (`StrategistDecision` / `MispricingThesis`).
- `discount_analyst.agents.researcher.schema`: `DeepResearchReport` input.
- `discount_analyst.agents.surveyor.schema`: `SurveyorCandidate` input.

### External

- **pydantic-ai**: Agent construction and structured output.
- **pydantic**: Data model validation via stage-local schemas.

<!-- MANUAL: Any manually added notes below this line are preserved on regeneration -->
