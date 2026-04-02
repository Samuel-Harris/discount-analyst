<!-- Parent: ../AGENTS.md -->
<!-- Generated: 2026-03-03 | Updated: 2026-04-03 -->

# tools

## Purpose

Shared tool definitions and agent-specific descriptions for AI agents. Provides reusable Perplexity-backed search tools (web_search, sec_filings_search) that can be registered with different agents via `create_perplexity_toolset(AgentName.X)` for Surveyor, Researcher, and Appraiser.

## Key Files

| File              | Description                                                                                                       |
| ----------------- | ----------------------------------------------------------------------------------------------------------------- |
| `descriptions.py` | `PerplexityToolDescriptions` dataclass and `AGENT_TOOL_DESCRIPTIONS` mapping agent names to tool docstrings.      |
| `perplexity.py`   | Shared implementation (`_web_search_impl`, `_sec_filings_search_impl`) and `create_perplexity_toolset()` factory. |

## Subdirectories

None.

## For AI Agents

### Working In This Directory

- **Add agent descriptions**: When implementing a new agent, add a `PerplexityToolDescriptions` instance to `AGENT_TOOL_DESCRIPTIONS` keyed by `AgentName.X` (currently includes APPRAISER, SURVEYOR, and RESEARCHER).
- **Use the factory**: When building agents, call `create_perplexity_toolset(AgentName.X)` and pass the result to the Agent's `toolsets` parameter.
- **Rate limiting**: The `perplexity_rate_limiter` lives in `perplexity.py`; all Perplexity API calls use it.

### Testing Requirements

- Ensure new agent descriptions are added to `AGENT_TOOL_DESCRIPTIONS` before calling `create_perplexity_toolset` for that agent (KeyError otherwise).
- Integration tests should mock Perplexity API calls when verifying agent behavior.

### Common Patterns

- **Agent-specific docstrings**: Each agent can have different tool descriptions via `AGENT_TOOL_DESCRIPTIONS`; the implementation logic is shared.
- **FunctionToolset**: Uses pydantic-ai's `FunctionToolset` and `add_function()` with `docstring_format="google"` and `require_parameter_descriptions=True`.

## Dependencies

### Internal

- `discount_analyst.shared.config.settings`: API keys and rate limit configuration.
- `discount_analyst.shared.constants.agents`: `AgentName` enum.

### External

- **pydantic-ai**: `FunctionToolset` for tool registration.
- **perplexityai**: `AsyncPerplexity` for web and SEC filing searches.
- **aiolimiter**: Rate limiting for Perplexity API calls.

<!-- MANUAL: Any manually added notes below this line are preserved on regeneration -->
