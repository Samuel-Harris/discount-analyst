<!-- Generated: 2026-02-23 | Updated: 2026-08-15 (sync-workflow skill) -->

# Discount Analyst

## Purpose

An AI-powered stock analysis tool ("Discount Analyst") for identifying and valuing promising small-cap UK and US equities. The name reflects two goals: finding stocks trading at a discount to intrinsic value, and doing so cheaply — minimising manual effort and API costs.

## Investment Workflow

The live automated pipeline is documented in [`current_workflow.md`](current_workflow.md) (regenerate with the `sync-workflow` skill). Dashboard and CLI run:

**Surveyor** (universe screen) and/or **Profiler** (named portfolio tickers) → deterministic candidate gate (dashboard only) → **Researcher** → **Strategist** → **Sentinel** (valuation gate) → **Appraiser** (if the gate passes) → deterministic rating table → `Verdict`.

Human decision sits after that `Verdict`. One-shot agents remain available via `uv run discount-analyst agent {surveyor,profiler,researcher,strategist,sentinel,appraiser}`.

## Key Files

| File                                           | Description                                                                                                          |
| ---------------------------------------------- | -------------------------------------------------------------------------------------------------------------------- |
| `pyproject.toml`                               | Package metadata, `module-root = "backend/src"`, Import Linter, console script `discount-analyst`.                   |
| `uv.lock`                                      | Locked dependencies.                                                                                                 |
| `README.md`                                    | Quick start and high-level docs.                                                                                     |
| `current_workflow.md`                          | Implementation-accurate snapshot of the agentic pipeline (schemas, gates, orchestration).                            |
| `pytest.ini`                                   | Coverage for `discount_analyst`; `testpaths = backend/tests`.                                                        |
| `backend/AGENTS.md`                            | **Placement guide** for the modular monolith (domain / agents / application / adapters / entrypoints / composition). |
| `backend/src/discount_analyst/`                | Installable Python package.                                                                                          |
| `backend/migrations/`                          | Alembic config + revision chain.                                                                                     |
| `backend/tools/`                               | OpenAPI export, Alembic check, terminal verify.                                                                      |
| `backend/services/agent_terminal/`             | Separate terminal orchestrator (HTTP only from the monolith).                                                        |
| `.cursor/skills/analyse-workflow-run/SKILL.md`           | Analyse a dashboard `workflow_run_id`.                                                                               |
| `.cursor/skills/sync-workflow/SKILL.md`                  | Regenerate `current_workflow.md` from live pipeline code.                                                            |

## Subdirectories

| Directory   | Purpose                                                                                      |
| ----------- | -------------------------------------------------------------------------------------------- |
| `backend/`  | Server-side monolith + migrations + tests + tools + agent-terminal (see `backend/AGENTS.md`) |
| `frontend/` | Vite + React dashboard SPA (see `frontend/AGENTS.md`)                                        |

## For AI Agents

### Working In This Directory

- Use `uv` for dependency management and execution.
- Place new Python code per `backend/AGENTS.md`; run `uv run lint-imports` after structural changes.
- After changing third-party imports or `[project] dependencies`, run `uv run tach check-external`.
- Do not reintroduce `common.*`, `scripts.*`, or top-level `backend.app` / `backend.db` import paths.

### Testing Requirements

- `uv run pytest` (suite under `backend/tests/`).
- `uv run lint-imports` for architecture contracts.
- `uv run tach check-external` for pyproject.toml dependency accuracy (monolith + agent-terminal).

### Common Patterns

- Settings: `discount_analyst.config.settings`.
- API: `discount_analyst.composition.api:create_app`.
- CLI: `discount-analyst` console script → `discount_analyst.composition.cli:main`.

## Dependencies

### External

- **pydantic-ai**, **yfinance**, **perplexityai**, **logfire**, **httpx**, **rich**, **FastAPI**, **SQLModel**, **Alembic**.

<!-- MANUAL: Any manually added notes below this line are preserved on regeneration -->
