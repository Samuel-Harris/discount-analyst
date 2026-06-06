---
name: analyse-workflow-run
description: >-
  End-to-end analysis of a Discount Analyst dashboard workflow run: telemetry
  (Logfire), SQLite conversation digests (host `data/dashboard.prod.sqlite` for
  saved production runs), per-agent qualitative review via subagents, and a single
  HTML report. Writes all artefacts under
  `.cursor/artefacts/analyse-workflow-run/<workflow-run-id>/`. Use when the user
  asks to analyse, review, or audit a workflow run, agent conversations for a
  run, or `workflow_run_id` / UUID from the dashboard pipeline.
---

# Analyse workflow run

Repeatable workflow to produce **telemetry + conversation** review for one `workflow_runs.id` (UUID).

## Artefact layout (required)

All outputs for a single run live under:

```text
.cursor/artefacts/analyse-workflow-run/<workflow-run-id>/
```

| Path (relative to that directory)                                     | Purpose                                                                                                                                                                                                                                           |
| --------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `dashboard.sqlite` (or copy renamed e.g. `from_run_dashboard.sqlite`) | Dashboard SQLite — copy from host `data/dashboard.prod.sqlite` into this folder for analysis — **do not commit** (parent `.gitignore` ignores `.cursor/artefacts/`).                                                                              |
| `conversation_digests/`                                               | Per-ticker `.md` digests + `_MERGED_<AGENT>.md` for subagent input.                                                                                                                                                                               |
| `aggregated_conversations/`                                           | Transcripts: one `*.md` per agent (`SURVEYOR.md`, `PROFILER.md`, …). **Default:** issue-focused export (≤6,000 lines per file, compressed prompts + heuristic ticker prioritisation). **`--full-transcripts`:** uncapped verbatim message stream. |
| `<workflow-run-id>_agent_review.html`                                 | Final report (self-contained HTML): data sources, qualitative sections, Logfire appendix. Open in a browser.                                                                                                                                      |

Never place run-specific artefacts loose under `.cursor/artefacts/analyse-workflow-run/` — always nest each run in its own `<workflow-run-id>/` subdirectory.

Further layout and script-flag detail: [`references/artefact-layout.md`](references/artefact-layout.md).

## Prerequisites

- **Workflow UUID** (e.g. from UI, API, or Logfire `workflow_run_id`).
- **SQLite** containing that row: host [`data/dashboard.prod.sqlite`](../../../data/dashboard.prod.sqlite) holds saved production workflow runs. Copy into the artefact directory before analysis. Confirm the row exists:

  ```sql
  SELECT id, status, started_at FROM workflow_runs WHERE id = '<uuid>';
  ```

  If this returns **0 rows**, stop — do not treat an empty digest export as success. Ask for the correct SQLite file or a fresh copy of `data/dashboard.prod.sqlite`.

- **Logfire** (optional but recommended): project token with `query_run`; queries must use a **≤ 14 day** window and `LIMIT`. See [`references/logfire-queries.md`](references/logfire-queries.md).

### Host SQLite files

| Path                         | Role                                                                                                                                                |
| ---------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------- |
| `data/dashboard.prod.sqlite` | **Primary source** for analysing saved dashboard workflow runs (VS Code PROD stack, `DASHBOARD_DATABASE_PATH=data/dashboard.prod.sqlite`).          |
| `data/dashboard.dev.sqlite`  | Local DEV stack only — use when the run was created under DEV.                                                                                      |
| `data/dashboard.sqlite`      | Application default in [`common/config.py`](../../../common/config.py) when `DASHBOARD_DATABASE_PATH` is unset; not where production runs are kept. |

Historical Docker Compose production data was migrated into `data/dashboard.prod.sqlite` (see [`README.md`](../../../README.md)).

## Steps (agent)

1. **Create directory:** `.cursor/artefacts/analyse-workflow-run/<workflow-run-id>/`.
2. **Obtain DB:** Copy production dashboard SQLite into that directory:

   ```bash
   cp data/dashboard.prod.sqlite \
     ".cursor/artefacts/analyse-workflow-run/<uuid>/dashboard.sqlite"
   ```

   Verify the workflow row (query above). If copy is impossible, stop and ask for a file path.

3. **Export digests** (conversation text + tool surface for subagents):

   ```bash
   uv run python .cursor/skills/analyse-workflow-run/scripts/export_conversation_digests.py \
     --workflow-id "<uuid>" \
     --sqlite-path ".cursor/artefacts/analyse-workflow-run/<uuid>/dashboard.sqlite" \
     --output-dir ".cursor/artefacts/analyse-workflow-run/<uuid>"
   ```

   Creates `conversation_digests/` with:
   - **Workflow-scoped** conversations (`workflow_agent_executions`) — Surveyor uses ticker label `__workflow__` in filenames.
   - **Per-ticker** conversations (`runs` → `agent_executions` → `agent_conversations`), ordered by agent and ticker.
   - **`_MERGED_<AGENT>.md`** per agent present (e.g. `_MERGED_SURVEYOR.md`). Agent names in SQLite are **uppercase** (`SURVEYOR`, `PROFILER`, …).

   Confirm non-empty output (`ls conversation_digests/`). An empty directory means the workflow is missing from the supplied SQLite.

4. **Export aggregated conversations** (human-readable transcripts; **default** aligns with workflow-review issues — capped and compressed):

   ```bash
   uv run python .cursor/skills/analyse-workflow-run/scripts/export_aggregated_conversations.py \
     --workflow-id "<uuid>" \
     --sqlite-path ".cursor/artefacts/analyse-workflow-run/<uuid>/dashboard.sqlite" \
     --output-dir ".cursor/artefacts/analyse-workflow-run/<uuid>"
   ```

   Creates `aggregated_conversations/` with `SURVEYOR.md` (workflow-scoped, if present) plus `PROFILER.md` … `APPRAISER.md` (per-ticker sections inside each file, ordered by ticker).

   **Behaviour:** Each agent file is **at most 6,000 lines** (override with `--max-lines N`). Duplicate creed/system blocks are stubbed; large `user_prompt` bodies are head/tail thinned; **Appraiser** additionally redacts upstream JSON before `ValuationResult` when that pattern appears. If still over budget, entire **ticker** sections with the lowest heuristic keyword scores (per agent) are dropped first; omitted tickers are listed in a header blockquote. For a legacy uncapped export: add **`--full-transcripts`**.

5. **Logfire appendix:** Run focused `query_run` SQL (counts by `span_name`, `attributes->>'agent_name'`, failure messages) scoped by `attributes->>'workflow_run_id'` — see reference doc. Derive `start_timestamp` / `end_timestamp` from the run's `workflow_runs.started_at` when available, keeping the window ≤ 14 days.

6. **Qualitative pass:** Spawn **six** parallel subagents (`generalPurpose`, `readonly: true`), one per merged digest that exists:

   `.cursor/artefacts/analyse-workflow-run/<uuid>/conversation_digests/_MERGED_<AGENT>.md`

   Agents: `SURVEYOR`, `PROFILER`, `RESEARCHER`, `STRATEGIST`, `SENTINEL`, `APPRAISER`. Skip any agent with no merged file for this run.

7. **Write report:** `<uuid>_agent_review.html` in the **same** `<uuid>/` folder. **Do not** write a markdown report — the deliverable is HTML only.

## Report format (HTML)

Write a **single self-contained HTML file** (no external CSS/JS/fonts). Requirements:

- `<!DOCTYPE html>`, `<meta charset="utf-8">`, `<meta name="viewport" content="width=device-width, initial-scale=1">`, `<title>` including the workflow UUID.
- Embedded `<style>` for readable typography, section spacing, and styled `<table>` elements (borders, zebra rows optional).
- Semantic structure: `<header>`, `<main>`, `<section>` per major part, `<h1>`–`<h3>` hierarchy.
- Relative links to sibling artefacts where useful (`./conversation_digests/`, `./aggregated_conversations/`, `./dashboard.sqlite`).
- Telemetry and per-ticker summaries as HTML `<table>` elements, not markdown pipe tables.
- Escape user- and agent-generated text (`&`, `<`, `>`) in HTML body content.

## Report structure (suggested)

1. **Data sources** — SQLite path + copy command; Logfire window; note whether `data/dashboard.prod.sqlite` was copied fresh or may be stale.
2. **Executive summary** — tickers (`workflow_run_portfolio_tickers` / `runs`), profiler coverage if `< 25` conversations, sentinel pass count, runs with `run_final_decisions` / `final_rating` when present.
3. **Qualitative conversation review** — one `<section>` per agent from subagents.
4. **Appendix: telemetry** — Logfire tables + any pipeline-only notes.

## Codebase pointers

- Models: [`backend/db/models.py`](../../../backend/db/models.py) — `WorkflowRun` (`started_at`, `status`), `Run` (`ticker`, `final_rating`, `decision_type`), `AgentConversation` (`workflow_agent_execution_id` XOR `agent_execution_id`), messages, parts.
- Agent enum: `AgentNameDb` — six pipeline agents (no `ARBITER`; legacy `arbiter` rows were migrated in alembic `0004`).
- Config default DB: `common/config.py` → `Settings.database_path` defaults to `data/dashboard.sqlite`; production analysis uses **`data/dashboard.prod.sqlite`**.
- Export scripts: stdlib-only, live under `.cursor/skills/analyse-workflow-run/scripts/` (no repo imports).

## Optional deep interview

For ambiguous scope (“how deep?”, “which tickers?”), use the **deep-interview** skill first; save spec under `.cursor/artefacts/interviews/`.
