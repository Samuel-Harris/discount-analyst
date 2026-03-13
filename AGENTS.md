<!-- Generated: 2026-02-23 | Updated: 2026-02-23 (hooks added) -->

# Discount Analyst

## Purpose

An AI-powered stock analysis tool ("Discount Analyst") for identifying and valuing promising small-cap UK and US equities. The name reflects two goals: finding stocks trading at a discount to intrinsic value, and doing so cheaply — minimising manual effort and API costs.

## Investment Workflow

The tool supports a seven-stage pipeline. Stages 1 and 5 are automated by AI agents in this repo; stages 2–4 involve a lightweight manual step and external AI tools; stage 6 uses an AI model (Claude, Gemini, or ChatGPT) to evaluate buy recommendations; stage 7 is a human investment decision.

### Stage 1 — Survey (automated)

`scripts/run_surveyor.py` runs the `discount_analyst/surveyor/surveyor.py` agent, which uses AI-powered web research to screen for promising small-cap stocks across UK and US markets. It outputs a ranked list of candidates with tickers, exchange listings, market caps, and a rationale for each.

### Stage 2 — Shortlist (manual)

The analyst reviews the Surveyor output and manually selects the top ~10 most promising candidates.

### Stage 3 — Categorise (manual)

Each shortlisted stock is manually categorised as either a **value** stock (mature business believed to be trading below intrinsic value) or a **growth** stock (high-growth company, often pre-profit).

### Stage 4 — Deep research and checklist scoring (external AI tools)

An AI model (ChatGPT or Gemini, run interactively) is prompted with a structured deep-research prompt to produce a comprehensive research report for each stock. The prompts differ by category:

- **Value stocks**: assessed on financial health, valuation multiples, competitive moats, balance sheet strength, and red flags.
- **Growth stocks**: assessed on revenue growth quality, unit economics, market opportunity, product differentiation, customer metrics, and catalysts.

A separate AI agent then scores the resulting report against a detailed checklist for the appropriate category and produces a section-by-section pass/fail summary. Stocks that satisfy enough checklist criteria proceed to stage 5.

> Note: the deep-research prompts and checklist prompts are not committed to this repository.

### Stage 5 — DCF valuation (automated)

Stocks that pass the checklist are processed by `scripts/run_dcf_analysis.py`, which runs the `discount_analyst/appraiser/appraiser.py` agent to perform a full Discounted Cash Flow valuation. The agent consumes the research report produced in stage 4 and writes structured output (agent analysis + DCF figures) to `outputs/`.

### Stage 6 — Evaluate (external AI)

Use an AI model (Claude, Gemini, or ChatGPT) to evaluate whether to buy each stock based on the research report and the DCF analysis output.

### Stage 7 — Buy (human decision)

The analyst reviews the DCF outputs and AI buy recommendations across all stocks that reached stage 5 and buys those with the greatest margin of safety — i.e. where the current market price is furthest below the intrinsic value estimated by the Appraiser.

## Key Files

| File                 | Description                                                                                                            |
| -------------------- | ---------------------------------------------------------------------------------------------------------------------- |
| `pyproject.toml`     | Project metadata, uv configuration, and dependencies.                                                                  |
| `uv.lock`            | Locked versions of all project dependencies.                                                                           |
| `README.md`          | Overview, quick start instructions, and high-level documentation.                                                      |
| `LICENSE`            | MIT License terms for the repository.                                                                                  |
| `pytest.ini`         | Configuration for the `pytest` test suite, including coverage settings.                                                |
| `.cursor/hooks.json` | Cursor hooks: `sessionStart` (injects branch + uv env context) and `afterFileEdit` (auto-runs `ruff` on Python files). |

## Subdirectories

| Directory           | Purpose                                                                     |
| ------------------- | --------------------------------------------------------------------------- |
| `discount_analyst/` | Core source code for the analysis engine (see `discount_analyst/AGENTS.md`) |
| `scripts/`          | Entry point scripts for running analyses (see `scripts/AGENTS.md`)          |
| `tests/`            | Comprehensive unit and integration tests (see `tests/AGENTS.md`)            |
| `dashboards/`       | React web dashboards, including MCP Tool curation (see `dashboards/AGENTS.md`) |

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
