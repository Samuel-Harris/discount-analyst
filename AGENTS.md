<!-- Generated: 2026-02-23 | Updated: 2026-07-11 (backend modular monorepo) -->

# Discount Analyst

## Purpose

An AI-powered stock analysis tool ("Discount Analyst") for identifying and valuing promising small-cap UK and US equities. The name reflects two goals: finding stocks trading at a discount to intrinsic value, and doing so cheaply — minimising manual effort and API costs.

## Investment Workflow

The tool supports a seven-stage pipeline. Stages 1 and 5 are automated by AI agents in this repo, and stage 4 can be generated in-repo via the Researcher agent; stages 2–3 remain lightweight manual steps, stage 6 uses an external AI model to evaluate buy recommendations, and stage 7 is a human investment decision.

### Stage 1 — Survey (automated)

`uv run discount-analyst agent surveyor` runs the Surveyor agent (`backend/src/discount_analyst/agents/surveyor/`), which screens for promising small-cap stocks and writes JSON under `backend/outputs/`.

### Stage 2 — Shortlist (manual)

The analyst reviews Surveyor output and selects the top ~10 candidates.

### Stage 3 — Categorise (manual)

Each shortlisted stock is categorised as **value** or **growth**.

### Stage 4 — Deep research and checklist scoring

Deep research via `uv run discount-analyst agent researcher` (or `workflow run` for the full gated pipeline) or an external AI. Checklist scoring may still be external.

### Stage 5 — Intrinsic-value distribution (automated)

`uv run discount-analyst agent appraiser` (from Sentinel selectors) writes a method-agnostic intrinsic-value distribution to `backend/outputs/`.

### Stage 6 — Evaluate (external AI)

Use Claude, Gemini, or ChatGPT against the research report and Appraiser output.

### Stage 7 — Buy (human decision)

Buy where market price is furthest below expected intrinsic value.

## Key Files

| File                                           | Description                                                                                                          |
| ---------------------------------------------- | -------------------------------------------------------------------------------------------------------------------- |
| `pyproject.toml`                               | Package metadata, `module-root = "backend/src"`, Import Linter, console script `discount-analyst`.                   |
| `uv.lock`                                      | Locked dependencies.                                                                                                 |
| `README.md`                                    | Quick start and high-level docs.                                                                                     |
| `pytest.ini`                                   | Coverage for `discount_analyst`; `testpaths = backend/tests`.                                                        |
| `backend/AGENTS.md`                            | **Placement guide** for the modular monolith (domain / agents / application / adapters / entrypoints / composition). |
| `backend/src/discount_analyst/`                | Installable Python package.                                                                                          |
| `backend/migrations/`                          | Alembic config + revision chain.                                                                                     |
| `backend/tools/`                               | OpenAPI export, Alembic check, terminal verify.                                                                      |
| `backend/services/agent_terminal/`             | Separate terminal orchestrator (HTTP only from the monolith).                                                        |
| `.cursor/skills/analyse-workflow-run/SKILL.md` | Analyse a dashboard `workflow_run_id`.                                                                               |

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
