---
name: analyse-workflow-run
description: >-
  End-to-end analysis of a Discount Analyst dashboard workflow run: telemetry
  (Logfire), SQLite conversation digests (compose `DASHBOARD_DATABASE_PATH`),
  per-agent qualitative review via subagents, and a single markdown report.
  Writes all artefacts under `.cursor/artefacts/analyse-workflow-run/<workflow-run-id>/`.
  Use when the user asks to analyse, review, or audit a workflow run, agent
  conversations for a run, or `workflow_run_id` / UUID from the dashboard pipeline.
---

# Analyse workflow run

Repeatable workflow to produce **telemetry + conversation** review for one `workflow_runs.id` (UUID).

## Artefact layout (required)

All outputs for a single run live under:

```text
.cursor/artefacts/analyse-workflow-run/<workflow-run-id>/
```

| Path (relative to that directory)                       | Purpose                                                                                                                                                                                                                                           |
| ------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `from_compose_dashboard.sqlite` (or `dashboard.sqlite`) | Copied DB from backend container — **do not commit** (parent `.gitignore` ignores `.cursor/artefacts/`).                                                                                                                                          |
| `conversation_digests/`                                 | Per-ticker `.md` digests + `_MERGED_<AGENT>.md` for subagent input.                                                                                                                                                                               |
| `aggregated_conversations/`                             | Transcripts: one `*.md` per agent (`SURVEYOR.md`, `PROFILER.md`, …). **Default:** issue-focused export (≤6,000 lines per file, compressed prompts + heuristic ticker prioritisation). **`--full-transcripts`:** uncapped verbatim message stream. |
| `<workflow-run-id>_agent_review.md`                     | Final report: data sources, qualitative sections, Logfire appendix.                                                                                                                                                                               |

Never place run-specific artefacts loose under `.cursor/artefacts/analyse-workflow-run/` — always nest each run in its own `<workflow-run-id>/` subdirectory.

## Prerequisites

- **Workflow UUID** (e.g. from UI, API, or Logfire `workflow_run_id`).
- **SQLite** containing that row: normally `docker cp <backend>:/data/dashboard.sqlite` per [`docker-compose.yml`](../../../docker-compose.yml) (`DASHBOARD_DATABASE_PATH: /data/dashboard.sqlite`). Confirm with `SELECT id, status FROM workflow_runs WHERE id = ?`.
- **Logfire** (optional but recommended): project token with `query_run`; queries must use a **≤ 14 day** window and `LIMIT`. See [`references/logfire-queries.md`](references/logfire-queries.md).

## Steps (agent)

1. **Create directory:** `.cursor/artefacts/analyse-workflow-run/<workflow-run-id>/`.
2. **Obtain DB:** If the user’s machine has the compose stack, copy the live DB into that directory (e.g. `from_compose_dashboard.sqlite`). If copy is impossible, stop and ask for a file path.
3. **Export digests** (conversation text + tool surface for subagents):

   ```bash
   uv run python .cursor/skills/analyse-workflow-run/scripts/export_conversation_digests.py \
     --workflow-id "<uuid>" \
     --sqlite-path ".cursor/artefacts/analyse-workflow-run/<uuid>/from_compose_dashboard.sqlite" \
     --output-dir ".cursor/artefacts/analyse-workflow-run/<uuid>"
   ```

4. **Export aggregated conversations** (human-readable transcripts; **default** aligns with workflow-review issues — capped and compressed):

   ```bash
   uv run python .cursor/skills/analyse-workflow-run/scripts/export_aggregated_conversations.py \
     --workflow-id "<uuid>" \
     --sqlite-path ".cursor/artefacts/analyse-workflow-run/<uuid>/from_compose_dashboard.sqlite" \
     --output-dir ".cursor/artefacts/analyse-workflow-run/<uuid>"
   ```

   Creates `.cursor/artefacts/analyse-workflow-run/<uuid>/aggregated_conversations/` with `SURVEYOR.md` (if present) plus `PROFILER.md` … `APPRAISER.md` (per-ticker sections inside each file, ordered by ticker).

   **Behaviour:** Each agent file is **at most 6,000 lines** (override with `--max-lines N`). Duplicate creed/system blocks are stubbed; large `user_prompt` bodies are head/tail thinned; **Appraiser** additionally redacts upstream JSON before `ValuationResult` when that pattern appears. If still over budget, entire **ticker** sections with the lowest heuristic keyword scores (per agent) are dropped first. For a legacy uncapped export: add **`--full-transcripts`**.

5. **Logfire appendix:** Run focused `query_run` SQL (counts by `span_name`, `attributes->>'agent_name'`, failure messages) scoped by `attributes->>'workflow_run_id'` — see reference doc.
6. **Qualitative pass:** Spawn **seven** parallel subagents (`generalPurpose`, `readonly: true`), each reading **one** file:

   `.cursor/artefacts/analyse-workflow-run/<uuid>/conversation_digests/_MERGED_<AGENT>.md`

   Agent names match DB enum: `SURVEYOR`, `PROFILER`, `RESEARCHER`, `STRATEGIST`, `SENTINEL`, `APPRAISER` (merged files use those prefixes).

7. **Write report:** `<uuid>_agent_review.md` in the **same** `<uuid>/` folder. Link paths relative to that folder (`./from_compose_dashboard.sqlite`, `./conversation_digests/`, `./aggregated_conversations/`, script paths as above).

## Report structure (suggested)

1. **Data sources** — compose DB path + copy command; Logfire window; note repo `data/dashboard.sqlite` may be stale.
2. **Executive summary** — tickers, profiler coverage if `< 25` conversations, sentinel pass count.
3. **Qualitative conversation review** — one subsection per agent from subagents.
4. **Appendix: telemetry** — Logfire table + any pipeline-only notes.

## Codebase pointers

- Models: `backend/db/models.py` — `AgentConversation` (`workflow_agent_execution_id` XOR `agent_execution_id`), messages, parts.
- Compose DB env: `docker-compose.yml` → `backend.environment.DASHBOARD_DATABASE_PATH`.

## Optional deep interview

For ambiguous scope (“how deep?”, “which tickers?”), use the **deep-interview** skill first; save spec under `.cursor/artefacts/interviews/`.
