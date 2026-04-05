<!-- Generated: 2026-02-23 | Updated: 2026-04-03 (researcher workflow added) -->

# Discount Analyst

## Purpose

An AI-powered stock analysis tool ("Discount Analyst") for identifying and valuing promising small-cap UK and US equities. The name reflects two goals: finding stocks trading at a discount to intrinsic value, and doing so cheaply — minimising manual effort and API costs.

## Investment Workflow

The tool supports a seven-stage pipeline. Stages 1 and 5 are automated by AI agents in this repo, and stage 4 can now be generated in-repo via the Researcher agent workflow; stages 2–3 remain lightweight manual steps, stage 6 uses an AI model (Claude, Gemini, or ChatGPT) to evaluate buy recommendations, and stage 7 is a human investment decision.

### Stage 1 — Survey (automated)

`scripts/agents/run_surveyor.py` runs the `discount_analyst/agents/surveyor/surveyor.py` agent, which uses AI-powered web research to screen for promising small-cap stocks across UK and US markets. It outputs a ranked list of candidates with tickers, exchange listings, market caps, and a rationale for each.

### Stage 2 — Shortlist (manual)

The analyst reviews the Surveyor output and manually selects the top ~10 most promising candidates.

### Stage 3 — Categorise (manual)

Each shortlisted stock is manually categorised as either a **value** stock (mature business believed to be trading below intrinsic value) or a **growth** stock (high-growth company, often pre-profit).

### Stage 4 — Deep research and checklist scoring (in-repo Researcher or external AI tools)

Deep research can be produced either by the in-repo `Researcher` agent (`scripts/agents/run_researcher.py`, or the `scripts/workflows/run_surveyor_then_researcher.py`, `scripts/workflows/run_surveyor_researcher_strategist.py`, or `scripts/workflows/run_surveyor_to_sentinel.py` pipelines) or by an external AI model (ChatGPT/Gemini run interactively). The checklist-scoring step can still be done externally. Prompts differ by category:

- **Value stocks**: assessed on financial health, valuation multiples, competitive moats, balance sheet strength, and red flags.
- **Growth stocks**: assessed on revenue growth quality, unit economics, market opportunity, product differentiation, customer metrics, and catalysts.

A separate AI agent then scores the resulting report against a detailed checklist for the appropriate category and produces a section-by-section pass/fail summary. Stocks that satisfy enough checklist criteria proceed to stage 5.

> Note: the deep-research prompts and checklist prompts are not committed to this repository.

### Stage 5 — DCF valuation (automated)

Stocks that pass the checklist are processed by `scripts/agents/run_appraiser.py` (per-stock `--dir` folders containing `deep-research.md` and `surveyor-report.json`), which runs the `discount_analyst/agents/appraiser/appraiser.py` agent to perform a full Discounted Cash Flow valuation. The agent consumes the deep-research report plus structured Surveyor candidate context and writes output (agent analysis + DCF figures) to `outputs/`.

### Stage 6 — Evaluate (external AI)

Use an AI model (Claude, Gemini, or ChatGPT) to evaluate whether to buy each stock based on the research report and the DCF analysis output.

### Stage 7 — Buy (human decision)

The analyst reviews the DCF outputs and AI buy recommendations across all stocks that reached stage 5 and buys those with the greatest margin of safety — i.e. where the current market price is furthest below the intrinsic value estimated by the Appraiser.

## Key Files

| File                                                      | Description                                                                                                            |
| --------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------- |
| `pyproject.toml`                                          | Project metadata, uv configuration, and dependencies.                                                                  |
| `uv.lock`                                                 | Locked versions of all project dependencies.                                                                           |
| `README.md`                                               | Overview, quick start instructions, and high-level documentation.                                                      |
| `LICENSE`                                                 | MIT License terms for the repository.                                                                                  |
| `pytest.ini`                                              | Configuration for the `pytest` test suite, including coverage settings.                                                |
| `.cursor/hooks.json`                                      | Cursor hooks: `sessionStart` (injects branch + uv env context) and `afterFileEdit` (auto-runs `ruff` on Python files). |
| `scripts/agents/run_researcher.py`                        | Runs Researcher from Surveyor output selectors (`<json>` or `<json>:<TICKER>`) and writes one JSON per candidate.      |
| `scripts/agents/run_strategist.py`                        | Runs Strategist from Researcher output selectors (`<json>` or `<json>:<TICKER>`) and writes one JSON per target.       |
| `scripts/agents/run_sentinel.py`                          | Runs Sentinel from Strategist output selectors (`<json>` or `<json>:<TICKER>`) and writes one JSON per target.         |
| `scripts/workflows/run_surveyor_then_researcher.py`       | Runs Surveyor once, then Researcher per candidate (no Strategist).                                                     |
| `scripts/workflows/run_surveyor_researcher_strategist.py` | Runs Surveyor once, Researcher per candidate, then Strategist per successful Researcher.                               |
| `scripts/workflows/run_surveyor_to_sentinel.py`           | Runs Surveyor once, Researcher per candidate, then Strategist and Sentinel per successful prior stage.                 |

## Subdirectories

| Directory           | Purpose                                                                     |
| ------------------- | --------------------------------------------------------------------------- |
| `discount_analyst/` | Core source code for the analysis engine (see `discount_analyst/AGENTS.md`) |
| `scripts/`          | Entry point scripts for running analyses (see `scripts/AGENTS.md`)          |
| `tests/`            | Comprehensive unit and integration tests (see `tests/AGENTS.md`)            |

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
