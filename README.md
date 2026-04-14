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

### Pipeline agents (`discount_analyst`)

Structured settings are defined in [`discount_analyst/config/settings.py`](discount_analyst/config/settings.py). They load from **`discount_analyst/.env`** (path resolved next to the `discount_analyst` package, not the repository root unless you place the file there by convention).

Nested fields use double underscores in environment variable names, for example:

| Variable                            | Purpose                         |
| ----------------------------------- | ------------------------------- |
| `PYDANTIC__AI_GATEWAY_API_KEY`      | Gateway key used by Pydantic AI |
| `PYDANTIC__LOGFIRE_API_KEY`         | Logfire key                     |
| `PERPLEXITY__API_KEY`               | Perplexity API key              |
| `PERPLEXITY__RATE_LIMIT_PER_MINUTE` | Perplexity rate limit           |
| `ANTHROPIC__API_KEY`                | Optional Anthropic key          |
| `OPENAI__API_KEY`                   | Optional OpenAI key             |
| `GOOGLE__API_KEY`                   | Optional Google GenAI key       |
| `FMP__API_KEY`                      | Financial Modeling Prep         |
| `EODHD__API_KEY`                    | EODHD                           |

Optional provider blocks can be omitted when unused; consult the settings model for required combinations.

### Local dashboard (`backend`)

[`backend/settings/config.py`](backend/settings/config.py) exposes `DashboardSettings` with the `DASHBOARD_` prefix and optional **repository root** `.env` (Pydantic loads `env_file=".env"` relative to the process working directory — use the repo root when you start uvicorn).

| Variable                           | Default                   | Purpose                                                                   |
| ---------------------------------- | ------------------------- | ------------------------------------------------------------------------- |
| `DASHBOARD_DATABASE_PATH`          | `data/dashboard.sqlite`   | SQLite file for workflow runs, executions, and conversations              |
| `DASHBOARD_DEFAULT_MODEL`          | (see `ModelName` in code) | Default LLM for dashboard-driven runs                                     |
| `DASHBOARD_RISK_FREE_RATE`         | `0.037`                   | Risk-free rate passed into valuation stages                               |
| `DASHBOARD_USE_PERPLEXITY`         | `false`                   | Toggle Perplexity-backed behaviour where wired                            |
| `DASHBOARD_USE_MCP_FINANCIAL_DATA` | `true`                    | Toggle MCP financial data integration                                     |
| `DASHBOARD_LOG_LEVEL`              | `INFO`                    | Minimum Logfire level for dashboard process logs (`DEBUG`–`CRITICAL`)     |
| `DASHBOARD_LOGFIRE_TOKEN`          | _(unset)_                 | Optional Logfire token; when set, spans and logs are also sent to Logfire |

### Frontend (Vite)

| Variable                | Default                 | Purpose                                                                                                   |
| ----------------------- | ----------------------- | --------------------------------------------------------------------------------------------------------- |
| `VITE_API_PREFIX`       | `/api`                  | Prefix for browser `fetch` calls (see [`frontend/src/api/client.ts`](frontend/src/api/client.ts))         |
| `VITE_DEV_PROXY_TARGET` | `http://127.0.0.1:8000` | **Dev only:** Vite proxy target for `/api` (set to `http://backend:8000` under Docker Compose, see below) |

## Local dashboard (API and UI)

The dashboard is a **local-only** FastAPI app under [`backend/`](backend/) plus a Vite + React UI under [`frontend/`](frontend/).

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
from backend.settings.config import DashboardSettings
from backend.db.seed import seed
from backend.db.session import create_dashboard_engine, create_session_factory

settings = DashboardSettings()
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

Continuous integration runs `uv run pre-commit run --all-files`, `uv run pytest`, and `uv run pyright` (see [`.github/workflows/ci.yml`](.github/workflows/ci.yml)).

## Docker Compose

Compose is a **local convenience** for running the dashboard stack; it does not change the product boundary of “no cloud deployment”.

**Prerequisites:** Docker Engine or Docker Desktop with [Compose V2](https://docs.docker.com/compose/) (`docker compose`).

### Development stack (FastAPI + Vite)

[`docker-compose.yml`](docker-compose.yml) runs:

- **backend** — image built from [`backend/docker/Dockerfile`](backend/docker/Dockerfile), port **8000**, SQLite on a named volume at `DASHBOARD_DATABASE_PATH=/data/dashboard.sqlite`
- **frontend** — Vite dev server from [`frontend/Dockerfile`](frontend/Dockerfile) `development` stage, port **5173**, with `VITE_DEV_PROXY_TARGET=http://backend:8000` so `/api` from the browser reaches the backend service

Optional secrets and pipeline keys: add a repository root `.env` file; Compose references it when present (`env_file` with `required: false` in [`docker-compose.yml`](docker-compose.yml)). You still need **`discount_analyst/.env`** for agent settings when running **non-mock** workflows inside the backend container.

Wrapper (foreground; pass `-d` for detached):

```bash
./scripts/docker/compose-up.sh
```

Then open **http://localhost:5173**. The SQLite file lives in the `dashboard_sqlite` Docker volume until you remove it (`docker compose down -v`).

### Production-like smoke stack (nginx + static UI)

[`docker-compose.prod.yml`](docker-compose.prod.yml) builds the static frontend (`frontend/Dockerfile` `production` stage), serves it with nginx using [`docker/nginx.dashboard.conf`](docker/nginx.dashboard.conf), and reverse-proxies `/api` to the backend on the internal network. Published port **8080** maps to nginx port 80.

```bash
./scripts/docker/compose-up-prod.sh
```

Open **http://localhost:8080**. SQLite uses the separate volume `dashboard_sqlite_prod`.

### Building images without Compose

```bash
docker build -f backend/docker/Dockerfile -t discount-analyst-backend .
docker build -f frontend/Dockerfile --target production -t discount-analyst-web .
```
