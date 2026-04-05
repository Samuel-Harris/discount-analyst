<!-- Parent: ../AGENTS.md -->
<!-- Generated: 2026-02-23 | Updated: 2026-04-05 -->

# discount_analyst

## Purpose

The core source code for the "Discount Analyst" stock analysis engine. This directory contains the implementation of the financial modeling logic (DCF), the AI agents for automated research, and explicit packages for configuration, HTTP transport, integrations, valuation types, and shared agent runtime.

## Key Files

| File                                  | Description                                                                                                        |
| ------------------------------------- | ------------------------------------------------------------------------------------------------------------------ |
| `valuation/dcf_analysis.py`           | Implementation of the Discounted Cash Flow calculation engine.                                                     |
| `agents/appraiser/appraiser.py`       | Factory for the Appraiser agent with model-native or optional Perplexity-backed search tools.                      |
| `agents/surveyor/surveyor.py`         | Factory for the Surveyor agent for discovering cheap small-cap stock candidates.                                   |
| `agents/researcher/researcher.py`     | Factory for the Researcher agent that produces structured `DeepResearchReport` output from `SurveyorCandidate`.    |
| `agents/strategist/strategist.py`     | Factory for the Strategist agent that produces `MispricingThesis` from `SurveyorCandidate` + `DeepResearchReport`. |
| `agents/sentinel/sentinel.py`         | Factory for the Sentinel agent that produces `EvaluationReport` from candidate + deep research + thesis.           |
| `agents/common/agent_factory.py`      | Shared `AgentSpec` + `create_agent` factory used by pipeline agents (Strategist and Sentinel use no-tools mode).   |
| `agents/common/streamed_agent_run.py` | Streaming helper wrapping `stream_with_retries` and returning output, usage, and elapsed time.                     |
| `agents/common/streaming_retries.py`  | Retry/resume logic for `AbstractAgent.run_stream()` / `stream_output()`.                                           |
| `valuation/schema.py`                 | Core financial schemas: `StockData` and `StockAssumptions` used by DCF and Appraiser output typing.                |
| `agents/surveyor/schema.py`           | Surveyor enums and schemas: `SurveyorCandidate`, `SurveyorOutput`, and `KeyMetrics`.                               |
| `agents/researcher/schema.py`         | Researcher report schemas: `DeepResearchReport` plus nested neutral-evidence sections and data-gap progression.    |
| `agents/strategist/schema.py`         | Strategist output schema: `MispricingThesis`.                                                                      |
| `agents/sentinel/schema.py`           | Sentinel output schema: `EvaluationReport` and nested assessment models.                                           |
| `agents/appraiser/schema.py`          | Appraiser output schema: `AppraiserOutput` (`StockData` + `StockAssumptions`).                                     |
| `config/settings.py`                  | Application configuration using `pydantic-settings` for API keys and environment variables.                        |
| `config/ai_models_config.py`          | Configuration for LLM models, including token budgets and thinking parameters.                                     |
| `http/retrying_client.py`             | Tenacity-backed async HTTP client for provider APIs.                                                               |
| `integrations/perplexity.py`          | Perplexity-backed toolset factory for agents.                                                                      |

## Subdirectories

| Directory        | Purpose                                                                                                    |
| ---------------- | ---------------------------------------------------------------------------------------------------------- |
| `valuation/`     | DCF engine, `StockData` / `StockAssumptions`, and DCF parameter/result models (see `valuation/AGENTS.md`). |
| `agents/`        | AI agent packages and stage-local schemas (see `agents/AGENTS.md`).                                        |
| `agents/common/` | Agent runtime: model factory, streaming, tool wiring, creed, agent names (see `agents/common/AGENTS.md`).  |
| `config/`        | Settings, model config, provider capability flags (see `config/AGENTS.md`).                                |
| `http/`          | HTTP transport retries (see `http/AGENTS.md`).                                                             |
| `integrations/`  | External adapters: Perplexity, financial MCP (see `integrations/AGENTS.md`).                               |

## For AI Agents

### Working In This Directory

- **Structured Output**: Use `valuation/schema.py` for financial inputs/outputs; use each stage's `schema.py` for agent contracts (`agents/surveyor/schema.py`, etc.).
- **Async Execution**: Ensure all network calls (AI agents, search tools) are asynchronous.
- **Type Safety**: Maintain strict typing for all financial metrics (typically `float`).

### Testing Requirements

- Run the full test suite with `uv run pytest`.
- Add unit tests for any new financial calculation logic in `tests/dcf_analysis/`.
- Ensure agent tool changes are verified with integration tests (mocking external API calls).

### Common Patterns

- **Agent-Tool Binding**: AI agents use pydantic-ai tool registration with detailed docstrings for tool discovery.
- **Financial Modeling**: Follow the "Bottom-Up/Line-Item" approach for Free Cash Flow (FCF) projections as seen in `DCFAnalysis`.
- **Dependency direction**: `agents/common` does not import stage packages; stages may import earlier-stage schemas only.

## Dependencies

### Internal

- Packages under `discount_analyst/` compose as: `config` → runtime (`http`, `integrations`, `agents/common`) → stage agents → `valuation` for DCF (isolated from research-stage prompts).

### External

- **pydantic-ai**: The primary framework for building and running analysis agents.
- **pydantic**: Used for data validation and structured data modeling.
- **perplexityai**: Powers the `web_search` and `sec_filings_search` capabilities of the agent.
- **aiolimiter**: Manages API rate limits for external services.
- **marimo**: The interactive notebook environment for analysis.

<!-- MANUAL: Any manually added notes below this line are preserved on regeneration -->
