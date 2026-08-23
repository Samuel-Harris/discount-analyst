---
name: investigate-workflow-failures
description: >-
  Diagnose why a Discount Analyst dashboard workflow_run_id failed or was
  cancelled. Groups FAILED and CANCELLED ticker/agent errors from SQLite,
  Logfire, code, and optional conversations or vendor probes. Distinguishes
  persist/tool/schema crashes from intended gate or Sentinel rejections.
  Use when the user runs /investigate-workflow-failures <uuid>, asks why a
  workflow failed, what broke a UUID, or to triage dashboard pipeline errors.
  Do not use for qualitative agent-conversation review (see analyse-workflow-run).
  Do not implement fixes.
---

# Investigate workflow failures

Diagnose **causes** of every currently **FAILED** and **CANCELLED** ticker lane (and a failed Surveyor) for one `workflow_runs.id`. Do **not** fix anything.

Intended COMPLETED outcomes (`data_quality_rejection`, `sentinel_rejection`, rating-table SELL) are **not** errors. Mention their count so the batch is not mistaken for a total washout; do not investigate them as failures.

## Hard rules

- **Diagnose only.** Do not patch code, open a fix PR, POST `/retry_failed_agents`, cancel, or delete.
- **Do not destroy data.** Host dashboard SQLite is read-only (`mode=ro` or a copy). Artefacts are new files only.
- **Redact credentials** (`api_token=`, similar query secrets) in chat and in `diagnosis.md`. Ticker text and conversations are not confidential; keys are.
- **Never trust one field.** `workflow_runs.error_message` is often null. API detail omits per-run `error_message`. Stored SQLite text is the **last** attempt after retries. Terminal scrollback is the **last** crash.
- **Do not copy SQL from `analyse-workflow-run`.** That skill’s canned queries are stale (`finished_at`, `backend/db/models.py`, `"exit_code": 0` JSON). PRAGMA first; columns from `backend/src/discount_analyst/adapters/persistence/models.py`.

## When not to use this skill

User asked to **review / analyse / audit agent quality, conversations, or Appraiser valuations** → [analyse-workflow-run](../analyse-workflow-run/SKILL.md).

After this diagnosis, you may **point** at that skill. Do not run its six-subagent HTML path unless the user asks.

## Artefacts

```text
.cursor/artefacts/investigate-workflow-failures/<workflow-run-id>/<n>/
```

`<n>` is `1`, `2`, … — the next unused positive integer under that UUID — so a later investigation does not overwrite an earlier one.

| Path                    | Purpose                                                                |
| ----------------------- | ---------------------------------------------------------------------- |
| `diagnosis.md`          | Required causal report (same content as the chat answer, written down) |
| `dashboard.sqlite`      | Optional copy of the host DB used                                      |
| `conversation_digests/` | Only if you exported conversations for unexplained lanes               |

`.cursor/artefacts/` is gitignored.

Create the folder:

```bash
uuid="<workflow-run-id>"
base=".cursor/artefacts/investigate-workflow-failures/${uuid}"
mkdir -p "$base"
next=1
while [ -d "$base/$next" ]; do next=$((next + 1)); done
mkdir -p "$base/$next"
```

## Steps

Copy this checklist and work it in order.

```text
- [ ] 1. Parse UUID; create artefact dir <uuid>/<n>/
- [ ] 2. Check prior artefacts/handoffs for this UUID
- [ ] 3. Locate SQLite (prod → dev → default); abort if 0 rows
- [ ] 4. Optional copy; PRAGMA; run cluster script
- [ ] 5. Logfire exception timeline over the run window
- [ ] 6. For each error bucket: map to code (started_at vs HEAD)
- [ ] 7. Extra evidence only where still unexplained
- [ ] 8. Chat + diagnosis.md; do not fix
- [ ] 9. Update this skill if you learned something durable
```

### 1. Identity and prior work

Parse the UUID from `/investigate-workflow-failures <uuid>` or from the user message.

Before rediscovering: `.cursor/artefacts/investigate-workflow-failures/<uuid>/`, `.cursor/artefacts/analyse-workflow-run/<uuid>/`, `.cursor/artefacts/handoffs/` (search the UUID).

### 2. Find the row (stop if missing)

Query in order; **stop and ask** which DB if all return 0 rows:

| Path                         | When                                                                              |
| ---------------------------- | --------------------------------------------------------------------------------- |
| `data/dashboard.prod.sqlite` | VS Code PROD stack (`DASHBOARD_DATABASE_PATH`) — default for saved dashboard runs |
| `data/dashboard.dev.sqlite`  | DEV stack                                                                         |
| `data/dashboard.sqlite`      | Config default when env unset; usually not where prod runs live                   |

SQLite often stores enum **names** (`FAILED`, `SURVEYOR`, `SENTINEL_REJECTION`); `models.py` values and the API JSON are lowercase (`failed`, `surveyor`). Always compare with `lower(...)`. `WHERE status = 'failed'` misses `FAILED` rows.

Optional: `GET http://127.0.0.1:8000/api/workflow_runs/<uuid>` for the nested tree. It is **not** sufficient for error text.

If the API may still be writing, copy then query the copy:

```bash
cp data/dashboard.prod.sqlite \
  ".cursor/artefacts/investigate-workflow-failures/<uuid>/<n>/dashboard.sqlite"
```

Open copies and host files **read-only**.

### 3. Cluster (mandatory, before transcripts)

```bash
uv run python .cursor/skills/investigate-workflow-failures/scripts/cluster_workflow_failures.py \
  --workflow-id "<uuid>" \
  --sqlite-path "<sqlite used in step 2>"
```

In-scope rows match **Retry failed and cancelled agents**:

- `runs.status` in `{failed, cancelled}`
- failed Surveyor (`agent_executions.workflow_run_id` set, `run_id` null, status failed)
- lane executions status failed or cancelled
- `lane_aborted` + run failed (gate-abort with SKIPPED children)

SKIPPED executions often **copy** the originating error. The originating FAILED/CANCELLED row is the one with `started_at` set (conversation may still be missing if the crash was post-agent or mid-stream).

Group before diving. Several unrelated buckets in one workflow is normal.

### 4. Logfire (fill gaps and recover first cause)

Call Logfire `query_schema_reference` once. Queries: [investigation-queries.md](references/investigation-queries.md).

- Window from `workflow_runs.started_at` → `completed_at` (pad ~1 hour). If `completed_at` is null, use now. **Max 14 days**; split or warn if the span is longer.
- Filter `attributes->>'workflow_run_id' = '<uuid>'`. Always `LIMIT`.
- Prefer `is_exception` / `exception_type` / `exception_message` / `span_name` / `attributes->>'ticker'`.
- `attributes->>'agent_name'` is often **null** on pipeline-failed spans. Span names like `Surveyor entry pipeline failed` wrap **lane** failures, not Surveyor-agent guilt.
- List exceptions **in time order**, not just counts. Retries (`Workflow failed-agent retry scheduled`, multiple `Workflow execution started`) mean SQLite holds the **last** error.
- A week of retries will fill `LIMIT 80` with early-batch exceptions. Always also filter `attributes->>'ticker'` for each in-scope ticker, and page `start_timestamp > last_seen` until the window is exhausted.
- Project is often `discount-analyst`. Generate a UI link for the user.
- Sparse tagging: absence of a span does not prove the stage did not run — SQLite executions are occupancy.

### 5. Map buckets to code

For each cluster, grep the **models and adapters that raise that string**, then check whether HEAD already diverges from `started_at` (git log / blame). State “as of the run” vs “as of now”.

Starting pointers (verify; do not freeze August 2026 behaviour):

| Fingerprint                                                                       | Read                                                                                                             |
| --------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------- |
| `DataQualityRejection` vs `SentinelRejection` `model_type`                        | `adapters/persistence/crud/run_executions.py` (`persist_ticker_run_final_verdict`), `domain/decisions/schema.py` |
| FMP 402 / no confident match / `resolution_notes`                                 | `adapters/market_data/candidate_gates.py`, `fmp_client.py`                                                       |
| `EodhdRealTimeQuote` / `close='NA'`                                               | `adapters/market_data/eodhd_client.py`                                                                           |
| `run_stream()` / `EvaluationReport` / `UnexpectedModelBehavior` output validation | `agents/runtime/streaming_retries.py`, `agents/sentinel/schema.py`                                               |
| `web_fetch` max retries                                                           | pydantic-ai tool retries (default 1); HTTP status is in the same message or prior span                           |
| `Rate limit reached` / TPM                                                        | Provider quota; may be the last overlay after earlier gate/persist errors                                        |
| Failed-agent retry overlay                                                        | `entrypoints/api/routers/workflow_runs.py`, `prepare_retry_failed_agents`                                        |
| Status rollup                                                                     | `adapters/persistence/crud/workflow_runs.py` `recompute_workflow_status`                                         |

Taxonomy: [failure-kinds.md](references/failure-kinds.md).

### 6. Extra evidence (only if still unexplained)

Allowed and encouraged when SQLite + Logfire do not explain an in-scope lane:

- Conversation digest export (reuse analyse-workflow-run scripts; `--output-dir` = this numbered artefact folder). XOR-join Surveyor or you drop it.
- `agent_conversation_message_parts`: `part_kind = 'tool_return'`, `tool_name` in (`web_fetch`, `terminal_exec`). Terminal bodies are text `exit_code: 0`, **not** JSON `"exit_code": 0`. `%timeout%` matches `timeout 600` in commands — prefer `exit_code: 124` or Logfire Timeout types.
- Live FMP/EODHD **GET** probes when a vendor-plan or identity cause is suspected. Do not write vendor data into the dashboard DB.

Do **not** spawn six qualitative subagents to answer a persist ValidationError.

### 7. Answer

Lead with the answer in chat, then write the same into `diagnosis.md`.

```markdown
# Workflow <uuid> — failure diagnosis

- Artefact: `.cursor/artefacts/investigate-workflow-failures/<uuid>/<n>/`
- SQLite: <path> (copied: yes/no)
- Logfire window: <start> → <end>
- Workflow status / `error_message`: …

## In scope

N FAILED + C CANCELLED ticker lanes (of M total). Surveyor: …

## Not errors

K COMPLETED lanes (decision_type breakdown). Do not treat these as failures.

## Buckets

### Bucket 1 — <name> (count, tickers)

- Stored error (redacted):
- Likely root cause (first vs last if retried):
- Evidence (SQLite / Logfire / snapshot / conversation / vendor):
- Code to read:

## What completed

Tickers and `decision_type` (list, no deep dive).

## Unexplained

Lanes still open after all evidence, if any.
```

Offer `analyse-workflow-run` only if the user wants qualitative review next.

## Maintain this skill

After the investigation, **update this skill** (SKILL.md, `references/`, or `scripts/`) when either is true:

1. You found a **durable insight** future agents should know (new failure fingerprint, join gotcha, Logfire trap, schema change, secret-in-error pattern).
2. The skill has **drifted** from the repo (wrong path, column, enum, stale taxonomy, SQL that fails `PRAGMA`).

Keep changes mechanical: fix the classifier or reference, do not freeze one-off ticker stories. Re-read `models.py` rather than patching memory. Do not “fix” this skill by copying queries from `analyse-workflow-run`.

If you update the skill, say so in the chat answer in one line.

## Architecture agents must hold

```text
Surveyor (workflow-scoped) and/or Profiler (per portfolio ticker)
  → candidate gate (dashboard only)
  → Researcher → Strategist → Sentinel
  → Appraiser if Sentinel proceeds
  → rating table → Verdict
```

`agent_executions` parent is XOR. Joining only through `runs` **drops Surveyor**.

`Profiler`/`Surveyor` can COMPLETE as conversations and the **lane** still FAILED if the candidate gate or persist after the agent throws.
