<!-- Parent: ../AGENTS.md -->
<!-- Generated: 2026-04-03 | Updated: 2026-04-03 -->

# researcher

## Purpose

The `researcher` directory contains the implementation of the "Researcher" AI agent. This agent consumes a `SurveyorCandidate` and produces a structured, neutral `DeepResearchReport` JSON payload focused on evidence synthesis, market narrative, and explicit data-gaps progression.

## Key Files

| File               | Description                                                                                                               |
| ------------------ | ------------------------------------------------------------------------------------------------------------------------- |
| `researcher.py`    | Factory for the Researcher agent (`create_researcher_agent`).                                                             |
| `system_prompt.py` | System prompt defining neutral-evidence behavior (no recommendation/valuation calls) and schema-only output requirements. |
| `user_prompt.py`   | `create_user_prompt`: injects one `SurveyorCandidate` JSON block and requires `DeepResearchReport` output.                |
| `__init__.py`      | Package initialization for the researcher module.                                                                         |

## Subdirectories

None.

## For AI Agents

### Working In This Directory

- **Agent tools**: By default (`use_perplexity=False`), the agent uses pydantic-ai built-in `WebSearchTool` and, for providers that support it, `WebFetchTool`. With `use_perplexity=True`, Perplexity-backed tools (`web_search`, `sec_filings_search`) are provided by `discount_analyst.shared.tools.perplexity` via `create_perplexity_toolset(AgentName.RESEARCHER)`.
- **MCP support**: When `use_mcp_financial_data=True` (default), EODHD and FMP MCP toolsets are added for Anthropic and OpenAI via `add_required_feature_to_builtin_tools` (`ProviderFeature.MCP`). Google does not support MCP - use `use_mcp_financial_data=False` or pass `--no-mcp` in scripts.
- **Output contract**: Keep output constrained to `DeepResearchReport` in `shared/schemas/researcher.py`; do not add recommendation or valuation semantics to this agent.

### Testing Requirements

- Run `uv run ruff check discount_analyst/agents/researcher`.
- Run `uv run pytest` for full-suite validation.

### Common Patterns

- **Structured output**: Always return `DeepResearchReport` and pass `SurveyorCandidate` via `user_prompt.create_user_prompt`.
- **Tool wiring parity**: Mirror Surveyor/Appraiser toolset wiring to keep provider behavior consistent across agents.

## Dependencies

### Internal

- `discount_analyst.shared.schemas.researcher`: Structured output contract (`DeepResearchReport` and nested models).
- `discount_analyst.shared.schemas.surveyor`: Input contract (`SurveyorCandidate`).
- `discount_analyst.shared.tools.perplexity`: Perplexity toolset factory keyed by `AgentName.RESEARCHER`.
- `discount_analyst.shared.utils.agent_tools`: MCP toolset wiring utility.

### External

- **pydantic-ai**: Agent construction, built-in tools, and structured output.
- **pydantic**: Data model validation via shared schemas.

<!-- MANUAL: Any manually added notes below this line are preserved on regeneration -->
