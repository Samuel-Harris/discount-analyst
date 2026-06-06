<!-- Parent: ../AGENTS.md -->
<!-- Generated: 2026-04-05 -->

# agents/common

## Purpose

Shared **agent runtime** only: model construction from config, streaming runs with retries, declarative `AgentSpec` / `create_agent`, Perplexity + MCP tool wiring helpers, investing creed, and `AgentName` / tool description maps. Does not own stage output schemas (those live beside each agent).

## Key Files

| File                    | Description                                                                                 |
| ----------------------- | ------------------------------------------------------------------------------------------- |
| `agent_factory.py`      | `AgentSpec`, `create_agent` (optional `terminal: TerminalRunOptions`).                      |
| `terminal_run.py`       | `TerminalRunOptions`, `terminal_run_options`, `bind_session_id`, `run_agent_with_terminal`. |
| `model.py`              | `create_model_from_config`.                                                                 |
| `ai_logging.py`         | Shared AI-tagged Logfire instance (`AI_LOGFIRE`).                                           |
| `logging_constants.py`  | Shared observability constants (e.g. `AI_LOG_TAG`).                                         |
| `streamed_agent_run.py` | `run_streamed_agent` (terminal session delete + HTTP client cleanup).                       |
| `streaming_retries.py`  | `stream_with_retries`, streaming error classification.                                      |
| `tool_support.py`       | `add_required_feature_to_builtin_tools` (MCP, etc.).                                        |
| `tool_descriptions.py`  | Perplexity tool docstrings per `AgentName`.                                                 |
| `agent_names.py`        | `AgentName` enum.                                                                           |
| `creed.py`              | `INVESTING_CREED` for system prompts.                                                       |

## For AI Agents

- Do **not** import `discount_analyst.agents.surveyor`, `researcher`, etc. from this package (avoid cycles; keep stage boundaries).

## Dependencies

### Internal

- `discount_analyst.config`, `discount_analyst.http.retrying_client`, `discount_analyst.integrations`.
