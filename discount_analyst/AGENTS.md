<!-- Parent: ../AGENTS.md -->
<!-- Generated: 2026-02-23 | Updated: 2026-04-03 -->

# discount_analyst

## Purpose

The core source code for the "Discount Analyst" stock analysis engine. This directory contains the implementation of the financial modeling logic (DCF), the AI agents for automated research, and the shared utilities required to perform comprehensive, low-cost stock valuations.

## Key Files

| File                                              | Description                                                                                                           |
| ------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------- |
| `dcf_analysis/dcf_analysis.py`                    | Implementation of the Discounted Cash Flow calculation engine.                                                        |
| `agents/appraiser/appraiser.py`                   | Factory for the Appraiser agent with model-native or optional Perplexity-backed search tools.                         |
| `agents/surveyor/surveyor.py`                     | Factory for the Surveyor agent for discovering cheap small-cap stock candidates.                                      |
| `agents/researcher/researcher.py`                 | Factory for the Researcher agent that produces structured `DeepResearchReport` output from `SurveyorCandidate`.       |
| `agents/strategist/strategist.py`                 | Factory for the Strategist agent that produces `MispricingThesis` from `SurveyorCandidate` + `DeepResearchReport`.    |
| `agents/arbiter/arbiter.py`                       | Factory for the Arbiter agent that produces `EvaluationReport` from candidate + deep research + thesis.               |
| `shared/ai/agent_factory.py`                      | Shared `AgentSpec` + `create_agent` factory used by pipeline agents (Strategist/Arbiter use no-tools mode).           |
| `shared/ai/streamed_agent_run.py`                 | Shared streaming helper wrapping `stream_with_retries` and returning output, usage, and elapsed time.                 |
| `shared/schemas/stock.py`                         | Core financial schemas: `StockData` and `StockAssumptions` used by DCF and Appraiser output typing.                   |
| `shared/schemas/surveyor.py`                      | Surveyor enums and schemas: `SurveyorCandidate`, `SurveyorOutput`, and `KeyMetrics`.                                  |
| `shared/schemas/researcher.py`                    | Researcher report schemas: `DeepResearchReport` plus nested neutral-evidence sections and data-gap progression.       |
| `shared/schemas/strategist.py`                    | Strategist output schema: `MispricingThesis`.                                                                         |
| `shared/schemas/arbiter.py`                       | Arbiter output schema: `EvaluationReport`.                                                                            |
| `shared/schemas/appraiser.py`                     | Appraiser output schema: `AppraiserOutput` (`StockData` + `StockAssumptions`).                                        |
| `shared/config/settings.py`                       | Application configuration using `pydantic-settings` for API keys and environment variables.                           |
| `shared/config/ai_models_config.py`               | Configuration for LLM models, including token budgets and thinking parameters.                                        |
| `../scripts/workflows/run_surveyor_to_arbiter.py` | Surveyor once, then sequential Researcher, Strategist, and Arbiter per candidate (see `scripts/workflows/AGENTS.md`). |

## Subdirectories

| Directory       | Purpose                                                                                                            |
| --------------- | ------------------------------------------------------------------------------------------------------------------ |
| `dcf_analysis/` | Core logic for financial calculations and DCF modeling. (see `dcf_analysis/AGENTS.md`)                             |
| `agents/`       | AI agent packages for surveyor, researcher, strategist, arbiter, and appraiser workflows. (see `agents/AGENTS.md`) |
| `shared/`       | Common data structures, configuration, and utility modules used across the package. (see `shared/AGENTS.md`)       |

## For AI Agents

### Working In This Directory

- **Structured Output**: Always use the Pydantic schemas in `shared/schemas/stock.py` and `shared/schemas/surveyor.py` for agent outputs and internal data passing.
- **Async Execution**: Ensure all network calls (AI agents, search tools) are asynchronous.
- **Type Safety**: Maintain strict typing for all financial metrics (typically `float`).

### Testing Requirements

- Run the full test suite with `uv run pytest`.
- Add unit tests for any new financial calculation logic in `tests/dcf_analysis/`.
- Ensure agent tool changes are verified with integration tests (mocking external API calls).

### Common Patterns

- **Agent-Tool Binding**: AI agents use the `@agent.tool_plain` decorator with detailed Google-style docstrings for tool discovery.
- **Financial Modeling**: Follow the "Bottom-Up/Line-Item" approach for Free Cash Flow (FCF) projections as seen in `DCFAnalysis`.
- **Rate Limiting**: Use the `aiolimiter` in `agents/appraiser/appraiser.py` when making calls to external search or LLM APIs.

## Dependencies

### Internal

- This is the root source directory; submodules depend on `discount_analyst.shared`.

### External

- **pydantic-ai**: The primary framework for building and running analysis agents.
- **pydantic**: Used for data validation and structured data modeling.
- **perplexityai**: Powers the `web_search` and `sec_filings_search` capabilities of the agent.
- **aiolimiter**: Manages API rate limits for external services.
- **marimo**: The interactive notebook environment for analysis.

<!-- MANUAL: Any manually added notes below this line are preserved on regeneration -->
