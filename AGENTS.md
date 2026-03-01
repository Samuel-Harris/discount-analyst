<!-- Generated: 2026-02-23 | Updated: 2026-02-23 (hooks added) -->

# Discount Analyst

## Purpose

An AI-powered stock analysis tool ("Discount Analyst") designed for automated, low-cost stock analysis (e.g., Discounted Cash Flow - DCF). It uses AI agents to automate research and financial analysis, minimizing manual input while providing comprehensive reports for investment decision-making.

## Key Files

| File | Description |
| --------- | ---------------------------- |
| `pyproject.toml` | Project metadata, uv configuration, and dependencies. |
| `uv.lock` | Locked versions of all project dependencies. |
| `README.md` | Overview, quick start instructions, and high-level documentation. |
| `LICENSE` | MIT License terms for the repository. |
| `pytest.ini` | Configuration for the `pytest` test suite, including coverage settings. |
| `.cursor/hooks.json` | Cursor hooks: `sessionStart` (injects branch + uv env context) and `afterFileEdit` (auto-runs `ruff` on Python files). |

## Subdirectories

| Directory | Purpose |
| --------- | ----------------------------------------- |
| `discount_analyst/` | Core source code for the analysis engine (see `discount_analyst/AGENTS.md`) |
| `scripts/` | Entry point scripts for running analyses (see `scripts/AGENTS.md`) |
| `tests/` | Comprehensive unit and integration tests (see `tests/AGENTS.md`) |

## For AI Agents

### Working In This Directory

- Use `uv` for all dependency management and environment execution.
- Maintain strict typing with Pydantic models for data structures.
- Use `logfire` for logging and monitoring analysis runs.
- Follow the modular pattern: keep core logic in `discount_analyst/` and execution logic in `scripts/`.

### Testing Requirements

- Run the full test suite using `uv run pytest`.
- Ensure new features include unit tests and, where applicable, integration tests with `yfinance` mocks.
- Maintain or improve the current test coverage as configured in `pytest.ini`.

### Common Patterns

- Async/Await: Most financial data fetching and AI agent calls are asynchronous.
- AI Agents: Uses `pydantic-ai` for structured AI agent interaction.
- Data Validation: Extensively uses `Pydantic` for validating financial data and agent outputs.

## Dependencies

### External

- **pydantic-ai**: AI agent framework for structured analysis.
- **yfinance**: Fetching real-time and historical financial data.
- **perplexityai**: AI-powered web research and data gathering.
- **logfire**: Observability, logging, and monitoring.
- **httpx**: Asynchronous HTTP client for API interactions.
- **rich**: Enhanced terminal output and progress indicators.

<!-- MANUAL: Any manually added notes below this line are preserved on regeneration -->
