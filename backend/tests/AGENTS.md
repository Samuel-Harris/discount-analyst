<!-- Parent: ../AGENTS.md -->
<!-- Generated: 2026-02-23 | Updated: 2026-08-30 -->

# tests

## Purpose

The `tests/` directory contains the automated test suite for the Discount Analyst project. Its primary role is to ensure the reliability and mathematical accuracy of core financial analysis logic, particularly deterministic valuation toolkit helpers. It serves as a regression suite to maintain code quality as the project's AI-driven data gathering and analysis components evolve.

## Key Files

| File                                                                    | Description                                                                                                                                                                                                   |
| ----------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `tests/conftest.py`                                                     | Suite-wide defaults so `discount_analyst.config.settings` can import during collection (sets `LOGGING__LOGFIRE_API_KEY` unless already present).                                                              |
| `tests/discount_analyst/agents/appraiser/test_appraiser_schema.py`      | Tests for method-agnostic Appraiser output validation and percentile rules.                                                                                                                                   |
| `tests/discount_analyst/agents/surveyor/test_surveyor_schema.py`        | Tests for Surveyor output validation (unique candidate tickers).                                                                                                                                              |
| `tests/discount_analyst/valuation/test_toolkit.py`                      | Tests for deterministic valuation toolkit helpers, including DCF real-world scenarios.                                                                                                                        |
| `tests/discount_analyst/http/test_streaming_retries.py`                 | Unit tests for agent streaming retry helpers (`stream_with_retries`, rate-limit exponential wait, structured-output repair, connection/rate-limit errors at stream start).                                    |
| `tests/discount_analyst/agents/common/test_structured_output_unwrap.py` | Singleton `final_result` envelope unwrap, `EvaluationReport` round-trip of an unwrapped FLXS payload, and factory `final_result` schema staying flat (`ticker` top-level, no `payload`).                      |
| `tests/discount_analyst/integrations/test_financial_data_mcp.py`        | EODHD MCP optional registration (`EODHD__DISABLED`).                                                                                                                                                          |
| `tests/discount_analyst/integrations/test_regulatory_data_*.py` | Canonical models, cache publication, pagination, HTTP policy, toolset wrapping, fixture presence. |
| `tests/discount_analyst/integrations/test_nasdaq_trader.py` / `test_london_stock_exchange.py` | NASDAQ merge/filter and LSE Main/AIM listing tools (mocked HTTP). |
| `tests/discount_analyst/integrations/test_sec_edgar.py` | SEC ticker mapping, period/amendment selection, debt non-duplication, gap-fill. |
| `tests/discount_analyst/integrations/test_companies_house.py` | Companies House resolver, iXBRL mappings, filleted accounts, atomic refresh. |
| `tests/discount_analyst/integrations/test_refresh_regulatory_data.py` | Admin `refresh-regulatory-data` dispatch, flags, and help. |
| `tests/fixtures/regulatory_data/` | Compact NASDAQ, LSE, SEC, and Companies House fixtures for those tests. |
| `tests/discount_analyst/integrations/test_text_only_web_fetch.py`       | Text-only local web fetch (markitdown binary conversion, DeepSeek wiring).                                                                                                                                    |
| `tests/fixtures/web_fetch/`                                             | Minimal PDF and DOCX fixtures with known extractable strings for markitdown integration tests.                                                                                                                |
| `tests/discount_analyst/integrations/test_terminal.py`                  | Terminal HTTP client mocks; optional `@pytest.mark.docker` orchestrator integration.                                                                                                                          |
| `tests/discount_analyst/agents/common/test_streamed_agent_run.py`       | Tests for `run_streamed_agent`.                                                                                                                                                                               |
| `tests/discount_analyst/agents/sentinel/test_sentinel_gate.py`          | Tests for `sentinel_proceeds_to_valuation` (thesis + red-flag gate).                                                                                                                                          |
| `tests/discount_analyst/agents/sentinel/test_derive_thesis_verdict.py`  | Tests for `derive_thesis_verdict` / `finalise_sentinel_evaluation` (gap_kind order, UNPROVEN, question-count mismatch).                                                                                       |
| `tests/discount_analyst/pipeline/test_builders.py`                      | Tests for `build_sentinel_rejection`, `verdict_from_decision`, and tagged `Verdict` JSON round-trip of all three decision kinds.                                                                              |
| `tests/discount_analyst/pipeline/test_candidate_gates.py`               | Pre-Researcher FMP/EODHD gates: auto-correct only on exact or unique strong match; unknown/ambiguous identity keeps the source ticker; listing rejects only on FMP inactive (non-`.L`) or EODHD `IsDelisted`. |
| `tests/discount_analyst/integrations/test_eodhd_client.py`              | EODHD REST client: real-time quote (including `"NA"` close → `None`), fundamentals `IsDelisted`.                                                                                                              |
| `tests/discount_analyst/integrations/test_infallible_toolset.py`        | `format_tool_error` plus `InfallibleToolExecution.wrap_tool_execute` (function-tool errors vs output-kind re-raise).                                                                                          |
| `tests/backend/unit/test_persist_ticker_run_final_verdict.py`           | DQR persist source lookup: Profiler if present, else workflow Surveyor; Researcher id unused.                                                                                                                 |
| `tests/backend/unit/test_dashboard_settings.py`                         | Unified ``Settings`` validation (e.g. non-empty ``LOGGING__LOGFIRE_API_KEY``).                                                                                                                                |
| `tests/backend/unit/test_workflow_api.py`                               | HTTP contract tests for the FastAPI dashboard (`backend`) with isolated SQLite.                                                                                                                               |
| `tests/backend/unit/test_agent_lane_order_sync.py`                      | Keeps `discount_analyst.application.workflows.agent_lane_order` aligned with `frontend/src/features/pipeline-graph/agentLaneOrder.ts`.                                                                        |
| `tests/backend/unit/test_profiler_stage.py`                             | Unit tests for the extracted dashboard `ProfilerStage` and its persistence port.                                                                                                                              |
| `tests/backend/unit/test_mock_surveyor_discoveries.py`                  | Mock Surveyor discovery helpers and deterministic mock Sentinel pass/fail parity for the dashboard.                                                                                                           |
| `tests/backend/unit/test_mock_rating_table_dashboard.py`                | Deterministic mock `RatingTableDecision` helpers for dashboard payloads.                                                                                                                                      |
| `tests/backend/unit/test_appraiser_output_persistence.py`               | Appraiser `AppraiserReport` persistence and `get_appraiser_report_for_run` join behaviour.                                                                                                                    |
| `tests/backend/unit/test_agent_output_persistence.py`                   | Profiler `CandidateSnapshot` persistence (exactly one row at `sort_order=0`).                                                                                                                                 |
| `tests/backend/unit/test_migration_startup.py`                          | Alembic head on startup, metadata verify, and 0009→head agent-execution unify remap (head is 0012).                                               |
| `tests/backend/integration/test_mock_workflow.py`                       | Mock pipeline persistence for `DashboardPipelineRunner` (no live LLM calls); mixed Sentinel lanes.                                                                                                            |
| `tests/backend/integration/test_dashboard_http_e2e.py`                  | Async HTTP path: create mock workflow run, poll until completed, assert detail and conversations.                                                                                                             |

## Subdirectories

| Directory                            | Purpose                                                                                                |
| ------------------------------------ | ------------------------------------------------------------------------------------------------------ |
| `discount_analyst/http/`             | Tests for streaming retry behaviour (`discount_analyst.agents.common.streaming_retries`).              |
| `discount_analyst/integrations/`     | Tests for MCP, Frankfurter FX, web-fetch, and terminal tool wiring.                                    |
| `discount_analyst/agents/common/`    | Tests for streamed agent orchestration and structured-output unwrap.                                   |
| `discount_analyst/agents/appraiser/` | Tests for Appraiser schema contracts.                                                                  |
| `discount_analyst/agents/sentinel/`  | Tests for Sentinel schema helpers.                                                                     |
| `discount_analyst/model_selection/`  | Tests for the per-model context-window table used by conversation usage telemetry.                     |
| `discount_analyst/pipeline/`         | Tests for programmatic verdict builders, tagged `Verdict` JSON, candidate gates, and the rating table. |
| `discount_analyst/valuation/`        | Tests for deterministic valuation toolkit helpers (`discount_analyst.valuation.toolkit`).              |
| `scripts/`                           | Tests for script helpers where present.                                                                |
| `backend/`                           | Tests for the FastAPI `backend` package (`unit/`, `integration/`); shared fixtures in `conftest.py`.   |

## For AI Agents

### Working In This Directory

- Follow the established pattern of using small typed fixtures (dataclasses, Pydantic models, or local helpers) to define structured test data and expected results.
- When adding tests for new financial analysis logic, ensure they are added to the corresponding package subdirectory (e.g., `discount_analyst/valuation/`).
- Use `pytest.mark.parametrize` for data-driven testing to cover multiple scenarios efficiently.

### Testing Requirements

- Run the full test suite from the project root using `uv run pytest`.
- New features should include unit tests and, where applicable, integration tests with `yfinance` mocks (using the `yfinance` pytest marker).
- Ensure that test coverage is maintained or improved as per `pytest.ini` (defaults include `--cov=discount_analyst`, branch coverage, and `--cov-report=term-missing`).

### Common Patterns

- **Parametrized Testing**: Extensive use of `pytest.mark.parametrize` to run tests across multiple stock data scenarios.
- **Model-Driven Tests**: Using `Pydantic`'s `BaseModel` to structure test cases, making them easier to read and maintain.
- **Approximate Matching**: Using `pytest.approx` for comparing floating-point results in financial calculations.

## Dependencies

### Internal

- `backend`: FastAPI app, DB layer, and pipeline runner (see `tests/backend/`).
- `discount_analyst.valuation.toolkit`: Deterministic valuation helpers under test.
- `discount_analyst.valuation.schema`: Stock data and assumptions models.
- `discount_analyst.agents.common.streaming_retries`, `discount_analyst.agents.common.streamed_agent_run`: Streaming behaviour.

### External

- **pytest**: The primary framework for running and structuring tests.
- **pydantic**: Used for defining structured test case data and expected results.

<!-- MANUAL: Any manually added notes below this line are preserved on regeneration -->
