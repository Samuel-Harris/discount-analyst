# Investigation queries

Ground truth for column names: `backend/src/discount_analyst/adapters/persistence/models.py`. **Always `PRAGMA table_info(...)`** (or `.schema`) on `workflow_runs`, `runs`, `agent_executions`, `candidate_snapshots` before adapting the SQL below. Never paste these blindly; never copy queries from `analyse-workflow-run`.

Prefer the cluster script for the first pass. Use these when you need a slice the script did not print.

Open SQLite read-only:

```bash
sqlite3 "file:data/dashboard.prod.sqlite?mode=ro" "PRAGMA table_info(workflow_runs);"
```

Statuses: compare with `lower(status)`. Live prod SQLite stores enum **names** (`FAILED`, `CANCELLED`, `COMPLETED`) even though `models.py` values are lowercase (`failed`). `WHERE status = 'failed'` will miss rows. Same for `entry_path` (`SURVEYOR`) and `decision_type` (`SENTINEL_REJECTION`).

## SQLite (adapt after PRAGMA)

```sql
-- Header
SELECT id, status, started_at, completed_at, error_message
FROM workflow_runs WHERE id = '<uuid>';

-- Lane outcomes
SELECT ticker, status, entry_path, lane_aborted, decision_type,
       final_rating, error_message
FROM runs
WHERE workflow_run_id = '<uuid>'
ORDER BY ticker;

-- Failed / cancelled agents (XOR parent — includes Surveyor)
SELECT COALESCE(r.ticker, '__workflow__') AS ticker,
       ae.agent_name, ae.status, ae.started_at, ae.error_message
FROM agent_executions ae
LEFT JOIN runs r ON ae.run_id = r.id
WHERE ae.workflow_run_id = '<uuid>'
   OR r.workflow_run_id = '<uuid>'
ORDER BY ticker, ae.started_at;

-- Gate internals (often older than runs.error_message)
SELECT cs.ticker, cs.gate_status, cs.gate_failure_reason,
       cs.resolved_ticker, cs.gate_data_source, cs.resolution_notes
FROM candidate_snapshots cs
JOIN agent_executions ae ON cs.agent_execution_id = ae.id
LEFT JOIN runs r ON ae.run_id = r.id
WHERE ae.workflow_run_id = '<uuid>'
   OR r.workflow_run_id = '<uuid>'
ORDER BY cs.ticker;
```

Conversation tool returns (Surveyor XOR join). Bodies are **text** (`exit_code: 0`), not JSON:

```sql
SELECT COALESCE(r.ticker, '__workflow__') AS ticker,
       ae.agent_name, p.tool_name, p.content_text
FROM agent_conversation_message_parts p
JOIN agent_conversation_messages m ON p.conversation_message_id = m.id
JOIN agent_conversations ac ON m.conversation_id = ac.id
JOIN agent_executions ae ON ac.agent_execution_id = ae.id
LEFT JOIN runs r ON ae.run_id = r.id
WHERE (ae.workflow_run_id = '<uuid>' OR r.workflow_run_id = '<uuid>')
  AND p.part_kind = 'tool_return'
  AND p.tool_name IN ('web_fetch', 'terminal_exec')
ORDER BY ticker, ae.agent_name;
```

Optional live API (no per-run error text):

```bash
curl -s "http://127.0.0.1:8000/api/workflow_runs/<uuid>"
```

## Logfire

Call `query_schema_reference` once. DataFusion SQL. Filter `attributes->>'workflow_run_id'`. Typed columns: `exception_type`, `exception_message`, `is_exception`, `span_name`. JSON `attributes->>'exception.type'` is a fallback.

Window = SQLite `started_at` − 1h through `completed_at` + 1h, still **≤ 14 days**. Always `LIMIT`. Project often `discount-analyst`.

Redact `api_token=` and `apikey=` from every quoted `exception_message`.

```sql
SELECT exception_type, COUNT(*) AS n
FROM records
WHERE attributes->>'workflow_run_id' = '<uuid>'
  AND start_timestamp >= '<iso-start>'
  AND start_timestamp < '<iso-end>'
  AND exception_type IS NOT NULL
GROUP BY exception_type
ORDER BY n DESC
LIMIT 20;

SELECT start_timestamp, span_name, exception_type,
       substr(exception_message, 1, 220) AS exception_message,
       attributes->>'ticker' AS ticker,
       attributes->>'agent_name' AS agent_name
FROM records
WHERE attributes->>'workflow_run_id' = '<uuid>'
  AND start_timestamp >= '<iso-start>'
  AND start_timestamp < '<iso-end>'
  AND (is_exception = true OR exception_type IS NOT NULL)
ORDER BY start_timestamp
LIMIT 80;

-- Required when retries span days: LIMIT 80 on the global list stops mid-history.
SELECT start_timestamp, span_name, exception_type,
       substr(exception_message, 1, 280) AS exception_message
FROM records
WHERE attributes->>'workflow_run_id' = '<uuid>'
  AND attributes->>'ticker' = '<in-scope-ticker>'
  AND start_timestamp >= '<iso-start>'
  AND start_timestamp < '<iso-end>'
  AND (is_exception = true OR exception_type IS NOT NULL)
ORDER BY start_timestamp
LIMIT 50;

SELECT start_timestamp, span_name, attributes->>'ticker' AS ticker
FROM records
WHERE attributes->>'workflow_run_id' = '<uuid>'
  AND start_timestamp >= '<iso-start>'
  AND start_timestamp < '<iso-end>'
  AND (span_name LIKE '%retry%' OR span_name LIKE '%Workflow%')
ORDER BY start_timestamp
LIMIT 40;
```

Many failed-agent retries fill `LIMIT 80` / `LIMIT 40` with the first attempt. Page with `start_timestamp > '<last-seen>'` and/or filter by in-scope ticker until the window is exhausted.

Generate a UI link with `project_logfire_ui_link` / `project_logfire_link` after you have timestamps or trace ids.

## Conversation export (optional)

Reuse, do not duplicate:

```bash
uv run python .cursor/skills/analyse-workflow-run/scripts/export_conversation_digests.py \
  --workflow-id "<uuid>" \
  --sqlite-path "<sqlite>" \
  --output-dir ".cursor/artefacts/investigate-workflow-failures/<uuid>/<n>"
```
