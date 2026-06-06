# Discount Analyst

[![CI](https://github.com/Samuel-Harris/discount-analyst/actions/workflows/ci.yml/badge.svg)](https://github.com/Samuel-Harris/discount-analyst/actions/workflows/ci.yml)

An AI-powered stock analysis tool for identifying and valuing promising small-cap UK and US equities. The name "Discount Analyst" reflects two goals: it is designed to find stocks trading at a discount to intrinsic value, and to do so cheaply — minimising manual effort and API costs.

## Investment Workflow

The tool supports a five-stage pipeline: Surveyor, Researcher, Strategist, Sentinel, and Appraiser run in-repo; you can still use an external AI model to weigh the buy case after valuation, then decide trades yourself.

**1. Survey — discover candidates**
Run the Surveyor agent to screen for promising small-cap stocks across UK and US markets:

```bash
uv run python scripts/agents/run_surveyor.py
```

The agent uses AI-powered web research to surface a ranked list of candidates with market caps, exchange listings, and a rationale for each.

**2. Research & strategy — in-repo agents**
The **Researcher** agent takes each `SurveyorCandidate` (value vs growth is part of the surveyor context) and produces a structured, neutral **deep research** report (`DeepResearchReport`). The **Strategist** agent then reads that report plus the same candidate and outputs a structured **mispricing thesis** (`MispricingThesis`) — interpretation only, no extra web research.

Run the full chain (Surveyor → Researcher → Strategist) in one go:

```bash
uv run python scripts/workflows/run_surveyor_researcher_strategist.py
```

Or run agents separately after Surveyor, using selectors of the form `path/to/surveyor.json` (all candidates) or `path/to/surveyor.json:TICKER` (one ticker):

```bash
uv run python scripts/agents/run_researcher.py --surveyor-report-and-ticker <selector>
uv run python scripts/agents/run_strategist.py --researcher-report-and-ticker <selector>
```

You can still narrow scope by passing a single-ticker selector instead of treating “shortlist” and “categorise” as separate manual stages.

**3. Value — intrinsic-value distribution**
Pass names that are ready for valuation to the Appraiser agent for a method-agnostic intrinsic-value distribution:

```bash
uv run python scripts/agents/run_appraiser.py \
  --sentinel-report-and-ticker scripts/outputs/<sentinel-run>.json \
  --risk-free-rate <RATE>
```

Use the Sentinel artefact written under `scripts/outputs/` after `run_sentinel.py` (or the full pipeline). The script follows the same `path.json` / `path.json:TICKER` selector pattern as Sentinel; it loads Surveyor, Researcher, and Strategist JSON paths from fields inside the Sentinel run record.

**4. Evaluate — AI buy recommendation**
Use an AI model (Claude, Gemini, or ChatGPT) to evaluate whether to buy each stock based on the research report, Strategist thesis, Sentinel review, and Appraiser valuation output.

**5. Buy — act on the margin of safety**
Review the Appraiser distributions across all analysed stocks. Buy the stocks with the greatest margin of safety — i.e. where the current market price is furthest below the expected intrinsic value estimated by the Appraiser.

## Quick Start

1. [Install uv](https://docs.astral.sh/uv/getting-started/installation/) if needed
2. Configure environment variables for the agents you run (see [Environment variables](#environment-variables))
3. Install dependencies: `uv sync`
4. Run the Surveyor to find candidates: `uv run python scripts/agents/run_surveyor.py`, or run survey → research → strategy in one command: `uv run python scripts/workflows/run_surveyor_researcher_strategist.py`
5. After Researcher/Strategist/Sentinel (step 2 above — or `scripts/workflows/run_full_workflow.py` for the full gated pipeline through deterministic rating and verdicts JSON), run Appraiser valuation: `uv run python scripts/agents/run_appraiser.py --sentinel-report-and-ticker scripts/outputs/<sentinel>.json --risk-free-rate <percentage e.g. 4.5>`

## Environment variables

### Application settings (pipeline + dashboard)

All configuration lives in a single [`common/config.py`](common/config.py) model (`Settings`, `load_settings`, module-level `settings`). Values load from **`discount_analyst/.env`**, then the **repository root** `.env` if it exists (later keys override earlier ones). The FastAPI app and agents import from `common.config`.

Nested groups use double underscores, for example `PERPLEXITY__API_KEY`, `LOGGING__LOGFIRE_API_KEY`, `EODHD__DISABLED`.

| Variable                            | Purpose                                                                                                                                                   |
| ----------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `LOGGING__LOGFIRE_API_KEY`          | Logfire ingest token (CLI agents and dashboard; non-empty)                                                                                                |
| `PERPLEXITY__API_KEY`               | Perplexity API key                                                                                                                                        |
| `PERPLEXITY__RATE_LIMIT_PER_MINUTE` | Perplexity rate limit                                                                                                                                     |
| `ANTHROPIC__API_KEY`                | Optional Anthropic key                                                                                                                                    |
| `OPENAI__API_KEY`                   | Optional OpenAI key                                                                                                                                       |
| `GOOGLE__API_KEY`                   | Optional Google GenAI key                                                                                                                                 |
| `DEEPSEEK__API_KEY`                 | Optional DeepSeek key                                                                                                                                     |
| `FMP__API_KEY`                      | Financial Modeling Prep                                                                                                                                   |
| `EODHD__API_KEY`                    | EODHD                                                                                                                                                     |
| `EODHD__DISABLED`                   | Set to `true` to skip EODHD MCP (FMP unchanged)                                                                                                           |
| `LOGGING__LOG_LEVEL`                | Logfire console minimum for the dashboard process (`DEBUG`-`CRITICAL`; default `INFO`)                                                                    |
| `DASHBOARD_DATABASE_PATH`           | SQLite path for workflow runs (default `data/dashboard.sqlite`; VS Code uses separate `data/dashboard.dev.sqlite` and `data/dashboard.prod.sqlite` files) |
| `DASHBOARD_DEFAULT_MODEL`           | Default LLM for dashboard-driven runs                                                                                                                     |
| `DASHBOARD_RISK_FREE_RATE`          | Risk-free rate as a percentage for valuation stages (e.g. `3.7` means 3.7%)                                                                               |
| `DASHBOARD_USE_PERPLEXITY`          | Toggle Perplexity-backed behaviour where wired                                                                                                            |
| `DASHBOARD_USE_MCP_FINANCIAL_DATA`  | Toggle MCP financial data in dashboard runs                                                                                                               |
| `ENV` or `DASHBOARD_DEPLOY_ENV`     | `DEV` or `PROD` (mock vs live server behaviour)                                                                                                           |

Optional provider blocks can be omitted when unused; consult the settings model for required combinations.

When `--perplexity` is not set, agents use Pydantic AI's `WebSearch` and `WebFetch` capabilities. Providers with native support use provider-native tools; providers without native support, such as DeepSeek, use Pydantic AI's local DuckDuckGo search and web-fetch fallbacks.

### Frontend (Vite)

| Variable                | Default                 | Purpose                                                                                           |
| ----------------------- | ----------------------- | ------------------------------------------------------------------------------------------------- |
| `VITE_API_PREFIX`       | `/api`                  | Prefix for browser `fetch` calls (see [`frontend/src/api/client.ts`](frontend/src/api/client.ts)) |
| `VITE_DEV_PROXY_TARGET` | `http://127.0.0.1:8000` | Vite dev/preview proxy target for `/api` (host API on **8000**)                                   |

## Local dashboard (API and UI)

The dashboard is a **local-only** FastAPI app under [`backend/`](backend/) plus a Vite + React UI under [`frontend/`](frontend/). With a workflow run open, use **Recommendations** for a full-width sortable verdict table; the URL can include `?run=<workflow_run_id>&view=recommendations` for deep links.

Logfire is configured with **FastAPI**, **PydanticAI**, and **HTTPX** instrumentation ([`backend/observability/logging.py`](backend/observability/logging.py)), so inbound `/api` requests and outbound model/MCP HTTP traffic emit spans with standard HTTP attributes (including response status when present), consistent with the CLI setup in [`scripts/utils/setup_logfire.py`](scripts/utils/setup_logfire.py).

### Install

```bash
uv sync
cd frontend && npm ci && cd ..
```

### Database migrations

Migrations run **automatically** when the API starts: `create_app` calls `migrate_to_head` with your configured SQLite URL ([`backend/app/main.py`](backend/app/main.py), [`backend/db/migrate.py`](backend/db/migrate.py)).

To run Alembic manually against the same revision bundle, set `sqlalchemy.url` in [`backend/db/alembic.ini`](backend/db/alembic.ini) (or override via Alembic’s `-x` mechanism) so it points at your database file, then from the repository root:

```bash
uv run alembic -c backend/db/alembic.ini upgrade head
```

### Seeding mock workflow data

There is no first-party CLI wrapper: tests and local experiments call `seed` from [`backend/db/seed.py`](backend/db/seed.py) with an open `sqlmodel.Session`. Example one-off:

```bash
uv run python -c "
from sqlmodel import Session
from common.config import load_settings
from backend.db.seed import seed
from backend.db.session import create_dashboard_engine, create_session_factory

settings = load_settings()
engine = create_dashboard_engine(settings)
factory = create_session_factory(engine)
with Session(engine) as s:
    seed(s)
    s.commit()
print('Seeded', settings.database_path)
"
```

### Run the stack (bare metal)

Terminal 1 — API (reload optional):

```bash
uv run uvicorn backend.app.main:create_app --factory --reload --host 127.0.0.1 --port 8000
```

Terminal 2 — UI:

```bash
cd frontend && npm run dev
```

Open the printed dev server URL (by default port **5173**). Browser calls go to `/api`, which Vite proxies to `VITE_DEV_PROXY_TARGET`.

For a **production-like** local stack (static UI, production uvicorn, terminal in Docker), use the VS Code launch configuration **Dashboard: PROD stack** (see [Docker Compose](#docker-compose) below). That runs `pnpm build` + `vite preview` on **8080**, a background production API on **8000**, and `agent-terminal` in Compose on **8001**. Use **Dashboard: API + Frontend** when you need debugpy breakpoints and hot reload on **5173**.

The VS Code dashboard launches keep local data separate: DEV uses `data/dashboard.dev.sqlite`, while PROD uses `data/dashboard.prod.sqlite`. The historical Docker Compose production database lived in the `dashboard_sqlite_prod` volume at `/data/dashboard.sqlite`; copy it to `data/dashboard.prod.sqlite` before running the host PROD stack if you need those saved workflow runs.

Stopping the PROD debug session ends Vite preview only; background API and terminal tasks keep running until you tear them down (`docker compose down`, and stop uvicorn on port **8000** if needed).

### Tests and static checks

From the repository root:

```bash
uv run pytest
uv run pyright
cd frontend && npm test
```

Continuous integration runs `uv run pre-commit run --all-files`, `uv run pytest` (with coverage for `discount_analyst/` and `backend/`), `uv run pyright`, a Node job that runs `npm run build` and `npm test` in `frontend/`, and a job that regenerates the dashboard OpenAPI spec and Orval client then fails on `git diff` drift (see [`.github/workflows/ci.yml`](.github/workflows/ci.yml)).

## Docker Compose

Compose runs only the **agent-terminal** orchestrator (sandbox containers via the Docker socket). The dashboard API and UI run on the **host** for day-to-day work; this does not change the product boundary of “no cloud deployment”.

**Prerequisites:** Docker Engine or Docker Desktop with [Compose V2](https://docs.docker.com/compose/) (`docker compose`). Build the sandbox image once: `make build-terminal-sandbox`.

### Terminal service

From the repository root (foreground; pass `-d` for detached):

```bash
docker compose up --build
```

Optional bind-mount of the repo into sandboxes:

```bash
TERMINAL_WORKSPACE_HOST_PATH="$(pwd)" docker compose up --build
```

The terminal listens on **<http://127.0.0.1:8001>**.

### Production-like local dashboard (host + terminal)

| Component                            | Where                                                       | Port     |
| ------------------------------------ | ----------------------------------------------------------- | -------- |
| UI (built static assets)             | Host — `vite preview` via VS Code **Dashboard: PROD stack** | **8080** |
| API (`ENV=PROD`, production uvicorn) | Host — background task `dashboard:api-prod`                 | **8000** |
| Terminal                             | Docker — `agent-terminal`                                   | **8001** |

Launch **Dashboard: PROD stack** from [`.vscode/launch.json`](.vscode/launch.json). The `preLaunchTask` `dashboard:prod-stack-prep` (see [`.vscode/tasks.json`](.vscode/tasks.json)) starts terminal + alembic + API + `pnpm build` with `ENV=PROD` and `DASHBOARD_DATABASE_PATH=data/dashboard.prod.sqlite`, then opens preview. The DEV debug compound uses `DASHBOARD_DATABASE_PATH=data/dashboard.dev.sqlite`; the application default remains **`data/dashboard.sqlite`** on the host ([`common/config.py`](common/config.py)) for direct commands that do not override it. Add a repository root `.env` with at least **`LOGGING__LOGFIRE_API_KEY`** and other keys required by settings.

For **DEV** debugging (reload, debugpy, Vite dev server), use **Dashboard: API + Frontend** on **5173** / **8000** instead.

**Teardown:** Stopping the PROD debug session does not stop background tasks. Run `docker compose down` and stop the uvicorn process on port **8000** if needed (`lsof -i :8000` or Activity Monitor).

### Building images without Compose

```bash
docker build -f backend/docker/Dockerfile -t discount-analyst-backend .
docker build -f frontend/Dockerfile --target production -t discount-analyst-web .
```
