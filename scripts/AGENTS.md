<!-- Parent: ../AGENTS.md -->
<!-- Generated: 2026-02-23 | Updated: 2026-04-02 -->

# scripts

## Purpose

The `scripts/` directory contains utility and entry-point scripts for the Discount Analyst project. These scripts facilitate data preparation (like parsing documentation) and execution of the core financial analysis workflows, including AI-driven market research and Discounted Cash Flow (DCF) calculations.

## Key Files

| File                      | Description                                                                                                                       |
| ------------------------- | --------------------------------------------------------------------------------------------------------------------------------- |
| `md_docs_parser.py`       | Splits a large markdown document into a hierarchical folder/file structure of smaller markdown files.                             |
| `agents/run_appraiser.py` | Runs Appraiser + DCF workflows from research folders and writes `AppraiserRunOutput` JSON (`--no-mcp` supported).                 |
| `agents/run_surveyor.py`  | Runs Surveyor stock discovery and writes `SurveyorRunOutput` JSON (`--no-mcp` supported).                                         |
| `shared.py`               | Shared script models, CLI argument helpers, output writers, and cost helpers used by `agents/` and `cost_comparison/` scripts.    |

## Subdirectories

| Directory          | Purpose                                                                                               |
| ------------------ | ----------------------------------------------------------------------------------------------------- |
| `agents/`          | Entry points for Surveyor and DCF / Appraiser workflows (`run_surveyor.py`, `run_appraiser.py`).      |
| `cost_comparison/` | Model cost/speed comparison script (see `cost_comparison/AGENTS.md`).                                 |

## For AI Agents

### Working In This Directory

- Scripts should follow the established pattern of using `argparse` for CLI interaction.
- Ensure any new execution scripts leverage `logfire` for observability and `rich` for terminal output.
- Follow the modularity principle: keep business logic in `discount_analyst/` and use scripts here as thin orchestration layers.

### Testing Requirements

- Currently, there are no automated tests for these scripts. Test changes by running the scripts with sample inputs.
- Example execution: `uv run python scripts/agents/run_appraiser.py --dir path/to/stock_folder --risk-free-rate 0.045`. Each `--dir` must contain `deep-research.md` and `surveyor-report.json` (a single `SurveyorCandidate`). Repeat `--dir` for batch runs. Default model and web-search mode come from `scripts.shared.DEFAULT_AGENT_CLI_DEFAULTS` (GPT 5.1, model-native search); pass `--perplexity` to use Perplexity-backed tools. Pass `--no-mcp` to omit EODHD/FMP MCP toolsets (required for Google models). If the surveyor ticker is missing from `deep-research.md`, the script prompts in an interactive terminal; non-interactive runs need the ticker present in the report.
- Verify `md_docs_parser.py` by checking the generated directory and file structure.

### Common Patterns

- **CLI Orchestration**: Using `argparse` and `asyncio` for running analysis tasks.
- **Observability**: Integration with `logfire` for tracking agent execution and data validation.
- **Rich Output**: Using `rich.console`, `Table`, and `Panel` for professional terminal reports.

## Dependencies

### Internal

- `discount_analyst.shared`: Configuration, settings, and shared models.
- `discount_analyst.agents.appraiser`: AI agent logic and prompt creation.
- `discount_analyst.agents.surveyor`: Surveyor agent for stock candidate discovery.
- `discount_analyst.dcf_analysis`: Core financial calculation engine.
- `scripts.shared`: `AppraiserRunOutput`, `SurveyorRunOutput`, `DEFAULT_AGENT_CLI_DEFAULTS`, `SCRIPTS_OUTPUTS_DIR`, `write_agent_json`, `write_model_output` (cost comparison), and cost helpers (used by `agents/run_appraiser.py`, `agents/run_surveyor.py`, and `cost_comparison/`).

### External

- **pydantic**: Data validation and argument parsing.
- **logfire**: Observability and logging.
- **rich**: Enhanced terminal UI components.
- **argparse**: Standard CLI argument handling.
- **asyncio**: Asynchronous execution for AI agents.

<!-- MANUAL: Any manually added notes below this line are preserved on regeneration -->
