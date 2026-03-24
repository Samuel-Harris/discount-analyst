<!-- Parent: ../AGENTS.md -->
<!-- Generated: 2026-02-23 | Updated: 2026-02-23 -->

# scripts

## Purpose

The `scripts/` directory contains utility and entry-point scripts for the Discount Analyst project. These scripts facilitate data preparation (like parsing documentation) and execution of the core financial analysis workflows, including AI-driven market research and Discounted Cash Flow (DCF) calculations.

## Key Files

| File                  | Description                                                                                                                                                                                                                                                             |
| --------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `md_docs_parser.py`   | Utility to split a large markdown document into a hierarchical directory structure of smaller markdown files.                                                                                                                                                           |
| `agents/run_dcf_analysis.py` | Main execution script that orchestrates the Appraiser AI agent and performs DCF valuation analysis. Writes output (agent + DCF) to `outputs/` in the same JSON format as `model_cost_comparison.py`.                                                                    |
| `agents/run_surveyor.py`     | Runs the Surveyor AI agent to discover cheap small-cap stock candidates in UK and US markets. Prints results to the terminal and writes output to `outputs/` as JSON (`{timestamp}-surveyor-{model}.json`).                                                             |
| `shared.py`           | Shared data types (`ModelRunOutput`, `SurveyorRunOutput`, `RunResult`, `RunConfig`, etc.), constants, and helpers (`write_model_output`, `write_surveyor_output`, `calc_actual_cost`) used by `agents/run_dcf_analysis.py`, `agents/run_surveyor.py`, and `cost_comparison/` scripts. |

## Subdirectories

| Directory          | Purpose                                                                                 |
| ------------------ | --------------------------------------------------------------------------------------- |
| `agents/`          | Entry points for the Surveyor and DCF / Appraiser workflows (`run_surveyor.py`, `run_dcf_analysis.py`). |
| `cost_comparison/` | Model cost/speed comparison script (see `cost_comparison/AGENTS.md`).                   |

## For AI Agents

### Working In This Directory

- Scripts should follow the established pattern of using `argparse` for CLI interaction.
- Ensure any new execution scripts leverage `logfire` for observability and `rich` for terminal output.
- Follow the modularity principle: keep business logic in `discount_analyst/` and use scripts here as thin orchestration layers.

### Testing Requirements

- Currently, there are no automated tests for these scripts. Test changes by running the scripts with sample inputs.
- Example execution: `uv run python scripts/agents/run_dcf_analysis.py --dir path/to/stock_folder --risk-free-rate 0.045`. Each `--dir` must contain `deep-research.md` and `surveyor-report.json` (a single `SurveyorCandidate`). Repeat `--dir` for batch runs.
- Verify `md_docs_parser.py` by checking the generated directory and file structure.

### Common Patterns

- **CLI Orchestration**: Using `argparse` and `asyncio` for running analysis tasks.
- **Observability**: Integration with `logfire` for tracking agent execution and data validation.
- **Rich Output**: Using `rich.console`, `Table`, and `Panel` for professional terminal reports.

## Dependencies

### Internal

- `discount_analyst.shared`: Configuration, settings, and shared models.
- `discount_analyst.appraiser`: AI agent logic and prompt creation.
- `discount_analyst.surveyor`: Surveyor agent for stock candidate discovery.
- `discount_analyst.dcf_analysis`: Core financial calculation engine.
- `scripts.shared`: `ModelRunOutput`, `SurveyorRunOutput`, `write_model_output`, `write_surveyor_output`, and cost helpers (used by `agents/run_dcf_analysis.py`, `agents/run_surveyor.py`, and `cost_comparison/`).

### External

- **pydantic**: Data validation and argument parsing.
- **logfire**: Observability and logging.
- **rich**: Enhanced terminal UI components.
- **argparse**: Standard CLI argument handling.
- **asyncio**: Asynchronous execution for AI agents.

<!-- MANUAL: Any manually added notes below this line are preserved on regeneration -->
