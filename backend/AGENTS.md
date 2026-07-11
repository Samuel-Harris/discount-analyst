<!-- Parent: ../AGENTS.md -->
<!-- Generated: 2026-07-11 | Updated: 2026-07-11 -->

# backend

## Purpose

Server-side home for Discount Analyst: the installable `discount_analyst` monolith under `src/`, Alembic migrations, tests, admin tools, and the separate agent-terminal HTTP service. Placement of new Python code is decided here; Import Linter enforces the layer rules.

## Key Files

| File                       | Description                                                                            |
| -------------------------- | -------------------------------------------------------------------------------------- |
| `src/discount_analyst/`    | Installable package (`module-root = "backend/src"`).                                   |
| `migrations/alembic.ini`   | Alembic config; revision chain preserved under `migrations/versions/`.                 |
| `tools/`                   | Admin utilities: OpenAPI export, Alembic drift check, terminal verify.                 |
| `services/agent_terminal/` | Privileged terminal orchestrator (own Dockerfiles/deps; not imported by the monolith). |
| `outputs/`                 | CLI JSON artefacts (formerly `scripts/outputs/`).                                      |

## Subdirectories

| Directory                           | Purpose                                                             |
| ----------------------------------- | ------------------------------------------------------------------- |
| `src/discount_analyst/domain/`      | Pure domain: valuation, decisions, model selection.                 |
| `src/discount_analyst/agents/`      | Agent stages + `runtime/` + `tools/` + `common_prompts/`.           |
| `src/discount_analyst/application/` | Ports, workflow helpers, decision builders, gate result types.      |
| `src/discount_analyst/adapters/`    | Persistence, market data, orchestration, simulation, observability. |
| `src/discount_analyst/entrypoints/` | FastAPI (`api/`) and CLI (`cli/`).                                  |
| `src/discount_analyst/composition/` | Wiring: `api.py`, `cli.py`, `dev_seed.py`.                          |
| `src/discount_analyst/config/`      | `Settings`, AI model config, provider features.                     |
| `migrations/`                       | Alembic env + versions.                                             |
| `tests/`                            | Unit, integration, factories, architecture (import-linter).         |
| `tools/`                            | OpenAPI / Alembic / terminal verify scripts.                        |
| `services/agent_terminal/`          | Separate Dockerised terminal service.                               |

## Placement decision tree

| Put it in…         | When…                                            | Examples                                                 | Forbidden                                                    |
| ------------------ | ------------------------------------------------ | -------------------------------------------------------- | ------------------------------------------------------------ |
| `domain/`          | Pure rules/types with no I/O                     | `IntrinsicValueDistribution`, rating matrix, `ModelName` | Importing agents, adapters, FastAPI, SQLModel, httpx         |
| `agents/`          | LLM stage factories, prompts, agent tool clients | Surveyor/Appraiser, `agents.tools.web_research`          | Importing adapters or entrypoints                            |
| `application/`     | Use-cases, ports, builders over agent schemas    | `application.decisions.builders`, gate result DTOs       | Importing adapters, entrypoints, composition, SQLModel       |
| `adapters/`        | DB, FMP/EODHD gates, mock mode, pipeline runner  | `adapters.persistence`, `adapters.orchestration`         | Cross-imports between persistence / market_data / simulation |
| `entrypoints/`     | HTTP routes/DTOs or CLI argparse                 | `entrypoints.api.routers`, `entrypoints.cli.agents`      | API importing CLI or vice versa                              |
| `composition/`     | App factory / console-script wiring only         | `composition.api:create_app`, `composition.cli:main`     | Business logic                                               |
| `config/`          | Settings and model/provider config               | `config.settings`                                        | Depending on adapters/entrypoints                            |
| `tools/`           | One-off admin scripts outside the package        | `tools/export_dashboard_openapi.py`                      | Being imported by product code                               |
| `tests/factories/` | Shared test builders                             | —                                                        | Reaching into unrelated adapters when a factory suffices     |

**Agent-terminal:** lives under `services/` and must **never** be imported by `discount_analyst`. Talk to it only over HTTP (`TERMINAL_SERVICE_URL`).

## Import Linter (summary)

Coarse layers (high → low): `composition` → `entrypoints` → `adapters` → `application` → `agents` → `config` → `domain`.

Also enforced: domain purity / protected importers; application forbidden adapters+SQLModel; API↔CLI independence; persistence ↔ market_data ↔ simulation independence; agent stage order (appraiser → … → surveyor).

Run: `uv run lint-imports` (also pre-commit + CI job `import-linter`).

## Tach `check-external` (pyproject accuracy)

Import Linter does **not** verify that third-party imports match declared dependencies. Tach does:

```bash
uv run tach check-external
```

Config: root [`tach.toml`](../tach.toml). Source roots cover the monolith (`backend/src`) and agent-terminal (`backend/services/agent_terminal`). Each package’s `pyproject.toml` must declare every external import (and must not declare unused product deps). Wired into pre-commit and CI (`tach-check-external`).

## How to run

```bash
# API
uv run uvicorn discount_analyst.composition.api:create_app --factory --reload --host 127.0.0.1 --port 8000

# CLI
uv run discount-analyst agent surveyor --help
uv run discount-analyst workflow run --help
uv run discount-analyst admin export-openapi
uv run discount-analyst admin check-alembic-schema

# Tests + architecture
uv run pytest
uv run lint-imports
uv run tach check-external

# Terminal (Docker)
make verify-terminal
```

## For AI Agents

### Working In This Directory

- Prefer updating callers over compatibility shims (`backend.*` / `common.*` / `scripts.*` are gone).
- Wire real vs mock via `adapters.simulation` from orchestration/composition — do not import simulation from persistence.
- Keep Alembic revision IDs stable; only change `script_location` / import paths in `env.py`.

### Testing Requirements

- `uv run pytest` from repo root (`testpaths = backend/tests`).
- Architecture: `backend/tests/architecture/test_import_linter.py`.

### Common Patterns

- Settings: `discount_analyst.config.settings`.
- Dashboard app: `discount_analyst.composition.api:create_app`.
- Pipeline runner: `discount_analyst.adapters.orchestration.sqlmodel_runner`.

## Dependencies

### Internal

- Package imports are exclusively `discount_analyst.*` (plus `backend.tools` via CLI `runpy` for admin scripts).

### External

- FastAPI, SQLModel/Alembic, pydantic-ai, Logfire, httpx, Rich.

<!-- MANUAL: Any manually added notes below this line are preserved on regeneration -->
