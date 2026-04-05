<!-- Parent: ../AGENTS.md -->
<!-- Generated: 2026-02-23 | Updated: 2026-04-05 -->

# scripts

## Purpose

The `scripts/` directory contains utility and entry-point scripts for the Discount Analyst project. These scripts facilitate data preparation (like parsing documentation) and execution of the core financial analysis workflows, including AI-driven market research and Discounted Cash Flow (DCF) calculations.

## Key Files

| File                                              | Description                                                                                                                                         |
| ------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------- |
| `md_docs_parser.py`                               | Splits a large markdown document into a hierarchical folder/file structure of smaller markdown files.                                               |
| `agents/run_appraiser.py`                         | Runs Appraiser + DCF from Sentinel run JSON selectors (same pattern as `run_sentinel.py`); writes `AppraiserRunOutput` JSON (`--no-mcp` supported). |
| `agents/run_surveyor.py`                          | Runs Surveyor stock discovery and writes `SurveyorRunOutput` JSON (`--no-mcp` supported).                                                           |
| `agents/run_researcher.py`                        | Runs Researcher from Surveyor JSON selectors and writes one `ResearcherRunOutput` artifact per candidate (`--no-mcp` supported).                    |
| `agents/run_strategist.py`                        | Runs Strategist from Researcher JSON selectors and writes one `StrategistRunOutput` artifact per target (model-only CLI).                           |
| `agents/run_sentinel.py`                          | Runs Sentinel from Strategist JSON selectors and writes one `SentinelRunOutput` artifact per target (model-only CLI).                               |
| `workflows/run_surveyor_then_researcher.py`       | Runs Surveyor once, then sequential Researcher per candidate (no Strategist stage).                                                                 |
| `workflows/run_surveyor_researcher_strategist.py` | Runs Surveyor once, then sequential Researcher and Strategist per candidate.                                                                        |
| `workflows/run_surveyor_to_sentinel.py`           | Runs Surveyor once, then sequential Researcher, Strategist, and Sentinel per candidate.                                                             |
| `workflows/run_surveyor_to_appraiser.py`          | Runs Surveyor once, then sequential Researcher, Strategist, and Sentinel per candidate; Appraiser + DCF when Sentinel authorises valuation.         |

## Subdirectories

| Directory          | Purpose                                                                                                                                                                                        |
| ------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `agents/`          | Entry points for Surveyor, Researcher, Strategist, Sentinel, and DCF/Appraiser workflows (`run_surveyor.py`, `run_researcher.py`, `run_strategist.py`, `run_sentinel.py`, `run_appraiser.py`). |
| `workflows/`       | Multi-agent workflow entry points combining Surveyor through Strategist or Sentinel orchestration.                                                                                             |
| `common/`          | Shared CLI, JSON writers, run-output models, usage and cost helpers (see `common/AGENTS.md`).                                                                                                  |
| `cost_comparison/` | Model cost/speed comparison script (see `cost_comparison/AGENTS.md`).                                                                                                                          |

## For AI Agents

### Working In This Directory

- Scripts should follow the established pattern of using `argparse` for CLI interaction.
- Ensure any new execution scripts leverage `logfire` for observability and `rich` for terminal output.
- Follow the modularity principle: keep business logic in `discount_analyst/` and use scripts here as thin orchestration layers.

### Testing Requirements

- Currently, there are no automated tests for these scripts. Test changes by running the scripts with sample inputs.
- Example execution (Researcher single ticker): `uv run python scripts/agents/run_researcher.py --surveyor-report-and-ticker scripts/outputs/<surveyor>.json:FLXS`.
- Example execution (Researcher all tickers): `uv run python scripts/agents/run_researcher.py --surveyor-report-and-ticker scripts/outputs/<surveyor>.json`.
- Example execution (Strategist): `uv run python scripts/agents/run_strategist.py --researcher-report-and-ticker scripts/outputs/<researcher>.json`.
- Example execution (Sentinel): `uv run python scripts/agents/run_sentinel.py --strategist-report-and-ticker scripts/outputs/<strategist>.json`.
- Example execution (Appraiser): `uv run python scripts/agents/run_appraiser.py --sentinel-report-and-ticker scripts/outputs/<sentinel>.json --risk-free-rate 0.045`. Repeat `--sentinel-report-and-ticker` for multiple Sentinel artifacts; optional `:TICKER` suffix matches `run_sentinel.py`. Default model and web-search mode come from `scripts.common.cli.DEFAULT_AGENT_CLI_DEFAULTS` (GPT 5.1, model-native search); pass `--perplexity` to use Perplexity-backed tools. Pass `--no-mcp` to omit EODHD/FMP MCP toolsets (required for Google models).
- Verify `md_docs_parser.py` by checking the generated directory and file structure.

### Common Patterns

- **CLI Orchestration**: Using `argparse` and `asyncio` for running analysis tasks.
- **Observability**: Integration with `logfire` for tracking agent execution and data validation.
- **Rich Output**: Using `rich.console`, `Table`, and `Panel` for professional terminal reports.

## Dependencies

### Internal

- `discount_analyst.config`, `discount_analyst.agents.*`, `discount_analyst.valuation`: Core package imports from scripts.
- `discount_analyst.agents.appraiser`: AI agent logic and prompt creation.
- `discount_analyst.agents.surveyor`: Surveyor agent for stock candidate discovery.
- `discount_analyst.valuation`: DCF calculation engine.
- `scripts.common.cli`, `scripts.common.constants`, `scripts.common.artifacts`, `scripts.common.usage`, `scripts.common.run_outputs`: CLI defaults, output paths, JSON writers, usage extraction, run-output models (used by `agents/` and `workflows/`).

### External

- **pydantic**: Data validation and argument parsing.
- **logfire**: Observability and logging.
- **rich**: Enhanced terminal UI components.
- **argparse**: Standard CLI argument handling.
- **asyncio**: Asynchronous execution for AI agents.

<!-- MANUAL: Any manually added notes below this line are preserved on regeneration -->
