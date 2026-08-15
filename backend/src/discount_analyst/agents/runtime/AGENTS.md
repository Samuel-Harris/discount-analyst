<!-- Parent: ../AGENTS.md -->
<!-- Generated: 2026-04-05 | Updated: 2026-08-15 -->

# agents/common

## Purpose

Shared **agent runtime** only: model construction from config, streaming runs with retries, declarative `AgentSpec` / `create_agent`, Perplexity + MCP tool wiring helpers, investing creed, structured-output prompt helpers, and `AgentName` / tool description maps. Does not own stage output schemas (those live beside each agent).

All pipeline agents register structured output via **tool mode** (`ToolOutput` → pydantic-ai `final_result`) for cross-provider uniformity.

## Key Files

| File                    | Description                                                                                                                                                                                                                                                                                                                                      |
| ----------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `agent_factory.py`      | `AgentSpec`, `create_agent`, `create_web_research_tooling` (bounded DuckDuckGo local web-search fallback; DeepSeek uses text-only `WebFetch` local tool). Always attaches Frankfurter `convert_currency` from `agents/tools/market_data/frankfurter.py`. Always attaches pydantic-ai-harness `ToolOutputLimits` (truncate at 10,000 characters). |
| `terminal_run.py`       | `TerminalRunOptions`, `terminal_run_options`, `bind_session_id`, `run_agent_with_terminal`.                                                                                                                                                                                                                                                      |
| `model.py`              | `create_model_from_config`.                                                                                                                                                                                                                                                                                                                      |
| `ai_logging.py`         | Shared AI-tagged Logfire instance (`AI_LOGFIRE`).                                                                                                                                                                                                                                                                                                |
| `logging_constants.py`  | Shared observability constants (e.g. `AI_LOG_TAG`).                                                                                                                                                                                                                                                                                              |
| `streamed_agent_run.py` | `run_streamed_agent` (terminal session delete + HTTP client cleanup).                                                                                                                                                                                                                                                                            |
| `streaming_retries.py`  | `stream_with_retries`, streaming error classification.                                                                                                                                                                                                                                                                                           |
| `tool_support.py`       | `add_required_feature_to_builtin_tools` (MCP, etc.).                                                                                                                                                                                                                                                                                             |
| `tool_descriptions.py`  | Perplexity tool docstrings per `AgentName`.                                                                                                                                                                                                                                                                                                      |
| `agent_names.py`        | `AgentName` enum.                                                                                                                                                                                                                                                                                                                                |
| `creed.py`              | `INVESTING_CREED` for system prompts.                                                                                                                                                                                                                                                                                                            |

## For AI Agents

- Do **not** import `discount_analyst.agents.surveyor`, `researcher`, etc. from this package (avoid cycles; keep stage boundaries).
- FX is always-on via `create_frankfurter_toolset()` in `create_agent`. Do not add an FX settings flag. `enable_web_research_tools=False` is test isolation only — production factories must not pass it.
- Tool-return truncation is always-on via pydantic-ai-harness `ToolOutputLimits` with `Truncate` at 10,000 characters (not the harness Spill default). Do not add a flag. pydantic-ai excludes output tools (`final_result`).
- Perplexity descriptions in `tool_descriptions.py` must include every `AgentName` (`create_perplexity_toolset` indexes the dict).

## Dependencies

### Internal

- `discount_analyst.config`, `discount_analyst.http.retrying_client`, `discount_analyst.integrations`.

### External

- **pydantic-ai**, **pydantic-ai-harness** (`ToolOutputLimits`).
