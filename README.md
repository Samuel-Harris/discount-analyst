# Discount Analyst

[![CI](https://github.com/Samuel-Harris/discount-analyst/actions/workflows/ci.yml/badge.svg)](https://github.com/Samuel-Harris/discount-analyst/actions/workflows/ci.yml)

An AI-powered stock analysis tool for identifying and valuing promising small-cap UK and US equities. The name "Discount Analyst" reflects two goals: it is designed to find stocks trading at a discount to intrinsic value, and to do so cheaply — minimising manual effort and API costs.

## Investment Workflow

The tool supports a five-stage pipeline: Surveyor, Researcher, and Strategist run in-repo; you still use an external AI model to weigh the buy case after DCF, then decide trades yourself.

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

**3. Value — DCF analysis**
Pass names that are ready for valuation to the Appraiser agent for a full Discounted Cash Flow analysis:

```bash
uv run python scripts/agents/run_appraiser.py \
  --sentinel-report-and-ticker scripts/outputs/<sentinel-run>.json \
  --risk-free-rate <RATE>
```

Use the Sentinel artefact written under `scripts/outputs/` after `run_sentinel.py` (or the full pipeline). The script follows the same `path.json` / `path.json:TICKER` selector pattern as Sentinel; it loads Surveyor, Researcher, and Strategist JSON paths from fields inside the Sentinel run record.

**4. Evaluate — AI buy recommendation**
Use an AI model (Claude, Gemini, or ChatGPT) to evaluate whether to buy each stock based on the research report, Strategist thesis, and the DCF analysis output.

**5. Buy — act on the margin of safety**
Review the DCF outputs across all analysed stocks. Buy the stocks with the greatest margin of safety — i.e. where the current market price is furthest below the intrinsic value estimated by the Appraiser.

## Quick Start

1. [Install uv](https://docs.astral.sh/uv/getting-started/installation/) if needed
2. Configure environment variables for the agents you run (see [Environment variables](#environment-variables))
3. Install dependencies: `uv sync`
4. Run the Surveyor to find candidates: `uv run python scripts/agents/run_surveyor.py`, or run survey → research → strategy in one command: `uv run python scripts/workflows/run_surveyor_researcher_strategist.py`
5. After Researcher/Strategist/Sentinel (step 2 above — or `scripts/workflows/run_full_workflow.py` for the full gated pipeline through Arbiter and verdicts JSON), run DCF analysis: `uv run python scripts/agents/run_appraiser.py --sentinel-report-and-ticker scripts/outputs/<sentinel>.json --risk-free-rate <decimal e.g. 0.045>`

## Environment variables

### Application settings (pipeline + dashboard)

All configuration lives in a single [`discount_analyst/config/settings.py`](discount_analyst/config/settings.py) model. Values load from **`discount_analyst/.env`**, then the **repository root** `.env` if it exists (later keys override earlier ones). The FastAPI app imports the same model via [`backend/settings/config.py`](backend/settings/config.py) (aliases: `Settings`, `DashboardSettings`, `load_settings`, `load_dashboard_settings`).

Nested groups use double underscores, for example `PERPLEXITY__API_KEY`, `LOGGING__LOGFIRE_API_KEY`, `EODHD__DISABLED`.

| Variable                            | Purpose                                                                                |
| ----------------------------------- | -------------------------------------------------------------------------------------- |
| `LOGGING__LOGFIRE_API_KEY`          | Logfire ingest token (CLI agents and dashboard; non-empty)                             |
| `PERPLEXITY__API_KEY`               | Perplexity API key                                                                     |
| `PERPLEXITY__RATE_LIMIT_PER_MINUTE` | Perplexity rate limit                                                                  |
| `ANTHROPIC__API_KEY`                | Optional Anthropic key                                                                 |
| `OPENAI__API_KEY`                   | Optional OpenAI key                                                                    |
| `GOOGLE__API_KEY`                   | Optional Google GenAI key                                                              |
| `FMP__API_KEY`                      | Financial Modeling Prep                                                                |
| `EODHD__API_KEY`                    | EODHD                                                                                  |
| `EODHD__DISABLED`                   | Set to `true` to skip EODHD MCP (FMP unchanged)                                        |
| `LOGGING__LOG_LEVEL`                | Logfire console minimum for the dashboard process (`DEBUG`–`CRITICAL`; default `INFO`) |
| `DASHBOARD_DATABASE_PATH`           | SQLite path for workflow runs (default `data/dashboard.sqlite`)                        |
| `DASHBOARD_DEFAULT_MODEL`           | Default LLM for dashboard-driven runs                                                  |
| `DASHBOARD_RISK_FREE_RATE`          | Risk-free rate for valuation stages                                                    |
| `DASHBOARD_USE_PERPLEXITY`          | Toggle Perplexity-backed behaviour where wired                                         |
| `DASHBOARD_USE_MCP_FINANCIAL_DATA`  | Toggle MCP financial data in dashboard runs                                            |
| `ENV` or `DASHBOARD_DEPLOY_ENV`     | `DEV` or `PROD` (mock vs live server behaviour)                                        |

Optional provider blocks can be omitted when unused; consult the settings model for required combinations.

### Frontend (Vite)

| Variable                | Default                 | Purpose                                                                                                   |
| ----------------------- | ----------------------- | --------------------------------------------------------------------------------------------------------- |
| `VITE_API_PREFIX`       | `/api`                  | Prefix for browser `fetch` calls (see [`frontend/src/api/client.ts`](frontend/src/api/client.ts))         |
| `VITE_DEV_PROXY_TARGET` | `http://127.0.0.1:8000` | **Dev only:** Vite proxy target for `/api` (set to `http://backend:8000` under Docker Compose, see below) |

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
from backend.settings.config import load_dashboard_settings
from backend.db.seed import seed
from backend.db.session import create_dashboard_engine, create_session_factory

settings = load_dashboard_settings()
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
uv run uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

Terminal 2 — UI:

```bash
cd frontend && npm run dev
```

Open the printed dev server URL (by default port **5173**). Browser calls go to `/api`, which Vite proxies to `VITE_DEV_PROXY_TARGET`.

### Tests and static checks

From the repository root:

```bash
uv run pytest
uv run pyright
cd frontend && npm test
```

Continuous integration runs `uv run pre-commit run --all-files`, `uv run pytest` (with coverage for `discount_analyst/` and `backend/`), `uv run pyright`, a Node job that runs `npm run build` and `npm test` in `frontend/`, and a job that regenerates the dashboard OpenAPI spec and Orval client then fails on `git diff` drift (see [`.github/workflows/ci.yml`](.github/workflows/ci.yml)).

## Docker Compose

Compose is a **local convenience** for running the dashboard stack; it does not change the product boundary of “no cloud deployment”.

**Prerequisites:** Docker Engine or Docker Desktop with [Compose V2](https://docs.docker.com/compose/) (`docker compose`).

### Dashboard stack (nginx + static UI)

[`docker-compose.yml`](docker-compose.yml) runs a **production-like** smoke stack:

- **backend** — image from [`backend/docker/Dockerfile`](backend/docker/Dockerfile), exposed on **8000** inside the Compose network only, SQLite on a named volume at `DASHBOARD_DATABASE_PATH=/data/dashboard.sqlite`, with **`ENV=PROD`** so mock mode is not forced server-side (this matches the static UI image, which is built with `ENV=PROD`).
- **web** — static assets from [`frontend/Dockerfile`](frontend/Dockerfile) `production`, served by nginx using [`docker/nginx.dashboard.conf`](docker/nginx.dashboard.conf), which reverse-proxies `/api` to the backend. Published port **8080** maps to nginx port **80**.

Add a repository root `.env` with at least **`LOGGING__LOGFIRE_API_KEY`** (and other keys required by [`discount_analyst/config/settings.py`](discount_analyst/config/settings.py)); Compose references it when present (`env_file` with `required: false` in [`docker-compose.yml`](docker-compose.yml)).

From the repository root (foreground; pass `-d` for detached):

```bash
docker compose -f docker-compose.yml up --build
```

Open **http://localhost:8080**. SQLite uses the volume `dashboard_sqlite_prod` until you remove it (`docker compose down -v`).

### Building images without Compose

```bash
docker build -f backend/docker/Dockerfile -t discount-analyst-backend .
docker build -f frontend/Dockerfile --target production -t discount-analyst-web .
```
