---
name: analyse-workflow-run
description: >-
  End-to-end analysis of a Discount Analyst dashboard workflow run: telemetry
  (Logfire), SQLite conversation digests (host `data/dashboard.prod.sqlite` for
  saved production runs), per-agent qualitative review via subagents, and a single
  HTML report. Writes all artefacts under
  `.cursor/artefacts/analyse-workflow-run/<workflow-run-id>/`. Use when the user
  asks to analyse, review, or audit agent quality, conversations, Appraiser
  valuations, or Curator portfolio allocations for a `workflow_run_id`. Do not
  use to diagnose why a workflow failed (see investigate-workflow-failures).
---

# Analyse workflow run

Repeatable workflow to produce **telemetry + conversation** review for one `workflow_runs.id` (UUID).

If the user asked **why this workflow failed** (or `/investigate-workflow-failures`), use [investigate-workflow-failures](../investigate-workflow-failures/SKILL.md) instead. This skill is the qualitative HTML path, not failure triage.

## Artefact layout (required)

All outputs for a single run live under:

```text
.cursor/artefacts/analyse-workflow-run/<workflow-run-id>/
```

| Path (relative to that directory)                                     | Purpose                                                                                                                                                                                                                                                         |
| --------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `dashboard.sqlite` (or copy renamed e.g. `from_run_dashboard.sqlite`) | Dashboard SQLite — copy from host `data/dashboard.prod.sqlite` into this folder for analysis — **do not commit** (parent `.gitignore` ignores `.cursor/artefacts/`).                                                                                            |
| `conversation_digests/`                                               | Per-ticker `.md` digests, workflow-scoped Surveyor/Curator (`{AGENT}___workflow__.md`), and `_MERGED_<AGENT>.md` for subagent input.                                                                                                                            |
| `aggregated_conversations/`                                           | Transcripts: one `*.md` per agent (`SURVEYOR.md`, `CURATOR.md`, `PROFILER.md`, …). **Default:** issue-focused export (≤6,000 lines per file, compressed prompts + heuristic ticker prioritisation). **`--full-transcripts`:** uncapped verbatim message stream. |
| `<workflow-run-id>_agent_review.html`                                 | Final report (self-contained HTML): data sources, qualitative sections, Logfire appendix. Open in a browser.                                                                                                                                                    |

Never place run-specific artefacts loose under `.cursor/artefacts/analyse-workflow-run/` — always nest each run in its own `<workflow-run-id>/` subdirectory.

Further layout and script-flag detail: [`references/artefact-layout.md`](references/artefact-layout.md).

## Prerequisites

- **Workflow UUID** (e.g. from UI, API, or Logfire `workflow_run_id`).
- **SQLite** containing that row: host [`data/dashboard.prod.sqlite`](../../../data/dashboard.prod.sqlite) holds saved production workflow runs. Copy into the artefact directory before analysis. Confirm the row exists:

  ```sql
  SELECT id, status, started_at FROM workflow_runs WHERE id = '<uuid>';
  ```

  If this returns **0 rows**, stop — do not treat an empty digest export as success. Ask for the correct SQLite file or a fresh copy of `data/dashboard.prod.sqlite`.

  You can also query the `appraiser_reports` table directly in SQLite to verify the updated method-agnostic valuation distributions:

  ```sql
  SELECT ar.ticker, ar.company_name, ar.currency, ar.current_share_price,
         ar.expected_intrinsic_value, ar.p10_intrinsic_value, ar.p50_intrinsic_value, ar.p90_intrinsic_value,
         ar.distribution_method, ar.data_quality
  FROM appraiser_reports ar
  JOIN agent_executions ae ON ar.agent_execution_id = ae.id
  JOIN runs r ON ae.run_id = r.id
  WHERE r.workflow_run_id = '<uuid>';
  ```

  Check the workflow-scoped Curator execution (may be `skipped` with no conversation on older or incomplete runs):

  ```sql
  SELECT id, status, error_message, started_at, completed_at
  FROM agent_executions
  WHERE workflow_run_id = '<uuid>' AND agent_name = 'curator';
  ```

  Query persisted Curator allocations (`portfolio_allocations` is the post-`finalise_curator_proposal` record, not the raw LLM `CuratorProposal`):

  ```sql
  SELECT pap.sort_order, pap.ticker, pap.company_name, pap.is_existing_position,
         pap.current_weight_pct, pap.target_weight_pct,
         pap.acceptable_weight_low_pct, pap.acceptable_weight_high_pct,
         pap.policy_kind, pap.forced_zero_reason, pap.action, pap.rationale
  FROM portfolio_allocation_positions pap
  JOIN portfolio_allocations pa ON pap.allocation_id = pa.id
  JOIN agent_executions ae ON pa.agent_execution_id = ae.id
  WHERE ae.workflow_run_id = '<uuid>' AND ae.agent_name = 'curator'
  ORDER BY pap.sort_order;
  ```

  ```sql
  SELECT pa.allocation_date, pa.current_cash_weight_pct, pa.cash_target_weight_pct,
         pa.cash_acceptable_weight_low_pct, pa.cash_acceptable_weight_high_pct,
         pa.cash_rationale, pa.portfolio_rationale
  FROM portfolio_allocations pa
  JOIN agent_executions ae ON pa.agent_execution_id = ae.id
  WHERE ae.workflow_run_id = '<uuid>' AND ae.agent_name = 'curator';
  ```

  ```sql
  SELECT parc.sort_order, parc.label, parc.mechanism, parc.allocation_effect, pap.ticker
  FROM portfolio_allocation_risk_clusters parc
  JOIN portfolio_allocations pa ON parc.allocation_id = pa.id
  JOIN agent_executions ae ON pa.agent_execution_id = ae.id
  JOIN portfolio_allocation_risk_cluster_members m ON m.cluster_id = parc.id
  JOIN portfolio_allocation_positions pap ON m.allocation_position_id = pap.id
  WHERE ae.workflow_run_id = '<uuid>' AND ae.agent_name = 'curator'
  ORDER BY parc.sort_order, m.sort_order;
  ```

  Decision mix (holdings vs prospects; Sentinel rejection vs rating table) — required for pipeline synthesis:

  ```sql
  SELECT is_existing_position, entry_path, decision_type, final_rating, recommended_action, COUNT(*) AS n
  FROM runs
  WHERE workflow_run_id = '<uuid>'
  GROUP BY 1, 2, 3, 4, 5
  ORDER BY n DESC;
  ```

  And check for terminal tool execution returns (lane-scoped **and** workflow-scoped Surveyor/Curator). Terminal bodies are text `exit_code: 0`, not JSON `"exit_code": 0`:

  ```sql
  SELECT ae.agent_name,
         COUNT(*) AS total_calls,
         SUM(CASE WHEN p.content_text LIKE '%exit_code: 0%' THEN 1 ELSE 0 END) AS success_calls,
         SUM(CASE WHEN p.content_text LIKE '%exit_code: 124%' THEN 1 ELSE 0 END) AS timeout_calls
  FROM agent_conversation_message_parts p
  JOIN agent_conversation_messages m ON p.conversation_message_id = m.id
  JOIN agent_conversations ac ON m.conversation_id = ac.id
  JOIN agent_executions ae ON ac.agent_execution_id = ae.id
  LEFT JOIN runs r ON ae.run_id = r.id
  WHERE (ae.workflow_run_id = '<uuid>' OR r.workflow_run_id = '<uuid>')
    AND p.part_kind = 'tool_return' AND p.tool_name = 'terminal_exec'
  GROUP BY ae.agent_name;
  ```

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

   Verify the workflow row (query above). If copy is impossible, stop and ask for a file path. If the dashboard API is writing to the host DB, prefer a SQLite backup (consistent snapshot) over `cp`:

   ```bash
   uv run python -c "import sqlite3; from pathlib import Path; s=sqlite3.connect('file:data/dashboard.prod.sqlite?mode=ro', uri=True); t=sqlite3.connect(Path('.cursor/artefacts/analyse-workflow-run/<uuid>/dashboard.sqlite')); s.backup(t); t.close(); s.close()"
   ```

3. **Export digests** (conversation text + tool surface for subagents):

   ```bash
   uv run python .cursor/skills/analyse-workflow-run/scripts/export_conversation_digests.py \
     --workflow-id "<uuid>" \
     --sqlite-path ".cursor/artefacts/analyse-workflow-run/<uuid>/dashboard.sqlite" \
     --output-dir ".cursor/artefacts/analyse-workflow-run/<uuid>"
   ```

   Creates `conversation_digests/` with:
   - **Workflow-scoped** conversations (`agent_executions` with `workflow_run_id`, `run_id` null) — Surveyor **and** Curator use ticker label `__workflow__` in filenames (`SURVEYOR___workflow__.md`, `CURATOR___workflow__.md`).
   - **Per-ticker** conversations (`runs` → lane-scoped `agent_executions` → `agent_conversations`), ordered by agent and ticker.
   - **`_MERGED_<AGENT>.md`** per agent present (e.g. `_MERGED_SURVEYOR.md`, `_MERGED_CURATOR.md`). Agent names in SQLite are **lowercase** (`surveyor`, `curator`, `profiler`, …); the exporter writes **uppercase** digest filenames.

   Confirm non-empty output (`ls conversation_digests/`). An empty directory means the workflow is missing from the supplied SQLite.

4. **Export aggregated conversations** (human-readable transcripts; **default** aligns with workflow-review issues — capped and compressed):

   ```bash
   uv run python .cursor/skills/analyse-workflow-run/scripts/export_aggregated_conversations.py \
     --workflow-id "<uuid>" \
     --sqlite-path ".cursor/artefacts/analyse-workflow-run/<uuid>/dashboard.sqlite" \
     --output-dir ".cursor/artefacts/analyse-workflow-run/<uuid>"
   ```

   Creates `aggregated_conversations/` with `SURVEYOR.md` and `CURATOR.md` (workflow-scoped, if present) plus `PROFILER.md` … `APPRAISER.md` (per-ticker sections inside each file, ordered by ticker).

   **Behaviour:** Each agent file is **at most 6,000 lines** (override with `--max-lines N`). Duplicate creed/system blocks are stubbed; large `user_prompt` bodies are head/tail thinned; **Appraiser** additionally redacts upstream JSON before `ValuationResult` when that pattern appears; **Curator** additionally redacts packed `<CuratorInput>` JSON. If still over budget, entire **ticker** sections with the lowest heuristic keyword scores (per agent) are dropped first; omitted tickers are listed in a header blockquote. For a legacy uncapped export: add **`--full-transcripts`**.

   Default aggregated files are **issue-focused and incomplete**. Use them for grepping themes. Use `conversation_digests/` plus SQLite for complete ticker/decision counts. Do not treat “3/38 conversations in `RESEARCHER.md`” as missing research.

5. **Logfire appendix:** Run focused `query_run` SQL (counts by `span_name`, `attributes->>'agent_name'`, failure messages) scoped by `attributes->>'workflow_run_id'` — see reference doc. Derive `start_timestamp` / `end_timestamp` from the run's `workflow_runs.started_at` when available, keeping the window ≤ 14 days. Treat Logfire as retry-inclusive telemetry; **SQLite is the source of truth for final ratings and allocation**.

6. **Qualitative pass:** Spawn **seven** parallel subagents (`generalPurpose`, `readonly: true`), one per merged digest that exists:

   `.cursor/artefacts/analyse-workflow-run/<uuid>/conversation_digests/_MERGED_<AGENT>.md`

   Agents: `SURVEYOR`, `PROFILER`, `RESEARCHER`, `STRATEGIST`, `SENTINEL`, `APPRAISER`, `CURATOR`. Skip any agent with no merged file for this run (Curator is often `skipped` when a lane did not complete, and legacy runs may have no Curator row).

   Briefs and untrusted-claim rules: [`references/agent-review-briefs.md`](references/agent-review-briefs.md). Direct subagents to review **terminal usage (`terminal_exec`)** (timeouts, shell errors, formatting, toolkit vs ad-hoc). For `APPRAISER`, evaluate method-agnostic distributions, primary vs cross-check weights, and whether the downstream SELL is robust to a less-conservative mix. For `CURATOR`, evaluate construction against packed `CuratorInput` and persisted `portfolio_allocations`: policy (`investable` / `retain_or_reduce` / `forced_zero`), every input ticker present (including explicit zeros), 15% company cap, shared-risk clusters, cash, and whether the agent re-rated names. Flag web/terminal/`convert_currency` as off-book. If every lane is `forced_zero`, 100% cash is mechanically compelled — do not attribute it to Curator caution.

7. **Pipeline synthesis (parent, required):** After subagents return, the parent independently reconstructs the **book-level** outcome. Per-agent reviews cannot see that a Sentinel “do not proceed” becomes SELL / “Exit the position.” and then Curator `forced_zero`. Follow [`references/pipeline-synthesis.md`](references/pipeline-synthesis.md): query SQLite facts, re-read live gate/policy code, split holdings vs prospects and Sentinel rejection vs rating-table SELL, separate repaired stop-errors from judgement, and verdict whether the allocation is mechanically compelled, economically defensible, or an over-escalation. If the user asked a specific concern (e.g. 100% cash, over-caution), answer it first in the executive summary. Do not concatenate subagent text.

8. **Write report:** `<uuid>_agent_review.html` in the **same** `<uuid>/` folder. **Do not** write a markdown report — the deliverable is HTML only.

## Report format (HTML)

Write a **single self-contained HTML file** (no external CSS/JS/fonts). Requirements:

- `<!DOCTYPE html>`, `<meta charset="utf-8">`, `<meta name="viewport" content="width=device-width, initial-scale=1">`, `<title>` including the workflow UUID.
- Embedded `<style>` for readable typography, section spacing, and styled `<table>` elements (borders, zebra rows optional).
- Semantic structure: `<header>`, `<main>`, `<section>` per major part, `<h1>`–`<h3>` hierarchy.
- Relative links to sibling artefacts where useful (`./conversation_digests/`, `./aggregated_conversations/`, `./dashboard.sqlite`).
- Telemetry and per-ticker summaries as HTML `<table>` elements, not markdown pipe tables.
- Escape user- and agent-generated text (`&`, `<`, `>`) in HTML body content.

## Report structure (suggested)

1. **Data sources** — SQLite path + copy/backup command; Logfire window; note whether `data/dashboard.prod.sqlite` was copied fresh or may be stale.
2. **Executive summary** — If the user asked a specific concern, **lead with that answer**. Then: tickers (`workflow_run_portfolio_tickers` / `runs`) split by **holding vs prospect** and by `decision_type` (Sentinel rejection vs rating table); Sentinel pass count; Appraiser skip vs complete; Curator status, cash target, and position count. Profiler coverage: warn only if a **Profiler-entry** lane lacks a Profiler conversation — Surveyor-originated names have no Profiler conversation by design. A count below 25 is not automatically incomplete.
3. **Pipeline synthesis** — Required. Causal chain from screening/research/thesis/gate/valuation/policy to the book (see [`references/pipeline-synthesis.md`](references/pipeline-synthesis.md)). Distinguish mechanical policy from model judgement, valid company caution from book liquidation, and repaired operational errors from remaining quality defects. Include a **per-ticker decision table** (ticker, holding?, path, thesis verdict, support/weaken/gap counts, action, independent reading).
4. **Terminal Tool Analytics** — `terminal_exec` counts, success rate, timeouts, errors, toolkit vs ad-hoc (include workflow-scoped Surveyor/Curator; do not join only via `runs`). Bodies are text `exit_code: 0`, not JSON.
5. **Appraiser Valuation Audit** — EXPECTED, P10, P50, P90, current price, currency, methods/weights, data quality. Recompute the blend; note whether SELL is table-correct and robust.
6. **Curator Allocation Audit** — Persisted positions (current vs target, range, policy, action), cash, clusters. Note skipped/absent Curator. Compare `CuratorProposal` with finalised rows. State whether cash/zeros were compelled by packed policy.
7. **Qualitative conversation review** — one `<section>` per agent from subagents (inputs to synthesis, not a substitute for it), including Curator when `_MERGED_CURATOR.md` exists.
8. **Appendix: telemetry** — Logfire tables, retry vs final-state notes.

## Codebase pointers

- Models: [`backend/src/discount_analyst/adapters/persistence/models.py`](../../../backend/src/discount_analyst/adapters/persistence/models.py) — `WorkflowRun` (`started_at`, `status`), `Run` (`ticker`, `final_rating`, `decision_type`), `AgentExecution` (XOR parent: `workflow_run_id` or `run_id`; Surveyor and Curator are workflow-scoped), `AgentConversation` (`agent_execution_id`), messages, parts, `AppraiserReport`, `PortfolioAllocation` / `PortfolioAllocationPosition` / `PortfolioAllocationRiskCluster`.
- Gate and policy (re-read during synthesis): [`agents/sentinel/derive_thesis_verdict.py`](../../../backend/src/discount_analyst/agents/sentinel/derive_thesis_verdict.py), `sentinel_proceeds_to_valuation` in [`agents/sentinel/schema.py`](../../../backend/src/discount_analyst/agents/sentinel/schema.py), [`application/decisions/builders.py`](../../../backend/src/discount_analyst/application/decisions/builders.py) (`build_sentinel_rejection`), [`domain/allocations/eligibility.py`](../../../backend/src/discount_analyst/domain/allocations/eligibility.py), [`agents/curator/system_prompt.py`](../../../backend/src/discount_analyst/agents/curator/system_prompt.py).
- Agent enum: `AgentNameDb` — seven pipeline agents (`surveyor`, `profiler`, `researcher`, `strategist`, `sentinel`, `appraiser`, `curator`; no `ARBITER`; legacy `arbiter` rows were migrated in alembic `0004`). SQLite stores **lowercase** values. Runtime `AgentName` / Logfire span `agent_name` is **uppercase**.
- Config default DB: `common/config.py` → `Settings.database_path` defaults to `data/dashboard.sqlite`; production analysis uses **`data/dashboard.prod.sqlite`**.
- Export scripts: stdlib-only, live under `.cursor/skills/analyse-workflow-run/scripts/` (no repo imports).
- Review briefs: [`references/agent-review-briefs.md`](references/agent-review-briefs.md), [`references/pipeline-synthesis.md`](references/pipeline-synthesis.md).

## Optional deep interview

For ambiguous scope (“how deep?”, “which tickers?”), use the **deep-interview** skill first; save spec under `.cursor/artefacts/interviews/`.
