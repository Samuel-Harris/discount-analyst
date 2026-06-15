# Logfire — workflow run queries

- **Project:** often `discount-analyst` if the token is not project-scoped (pass `project` on `query_run`).
- **Window:** `end_timestamp − start_timestamp` must be **≤ 14 days**.
- **Filter:** `attributes->>'workflow_run_id' = '<uuid>'`
- **Always** `LIMIT` (e.g. 100) on exploratory selects.

## Examples

**Count rows for a run:**

```sql
SELECT COUNT(*) AS n
FROM records
WHERE attributes->>'workflow_run_id' = '<uuid>'
  AND start_timestamp >= '<iso-start>'
  AND start_timestamp < '<iso-end>'
LIMIT 10
```

**Spans by name:**

```sql
SELECT span_name, COUNT(*) AS n
FROM records
WHERE attributes->>'workflow_run_id' = '<uuid>'
  AND start_timestamp >= '<iso-start>'
  AND start_timestamp < '<iso-end>'
GROUP BY span_name
ORDER BY n DESC
LIMIT 40
```

**Agent-tagged rows:**

```sql
SELECT attributes->>'agent_name' AS agent, COUNT(*) AS n
FROM records
WHERE attributes->>'workflow_run_id' = '<uuid>'
  AND start_timestamp >= '<iso-start>'
  AND start_timestamp < '<iso-end>'
GROUP BY 1
ORDER BY n DESC
LIMIT 20
```

**Terminal execution tracking:**

Query `terminal_exec` tool calls, counting execution attempts and isolating potential timeouts, exceptions, or shell error codes:

```sql
SELECT
  span_name,
  COUNT(*) AS total_calls,
  SUM(CASE WHEN message LIKE '%timeout%' OR attributes->>'exception.type' LIKE '%Timeout%' THEN 1 ELSE 0 END) AS timeouts,
  SUM(CASE WHEN attributes->'exception.type' IS NOT NULL THEN 1 ELSE 0 END) AS exceptions
FROM records
WHERE attributes->>'workflow_run_id' = '<uuid>'
  AND (span_name LIKE '%terminal_exec%' OR message LIKE '%terminal_exec%')
  AND start_timestamp >= '<iso-start>'
  AND start_timestamp < '<iso-end>'
GROUP BY span_name
LIMIT 20
```

**Appraiser model runs and token costs:**

Track token usage metrics and model invocations specifically for the `APPRAISER` agent to audit analysis costs:

```sql
SELECT
  span_name,
  COUNT(*) AS invocations,
  SUM(CAST(attributes->'usage'->>'prompt_tokens' AS INT)) AS prompt_tokens,
  SUM(CAST(attributes->'usage'->>'completion_tokens' AS INT)) AS completion_tokens,
  SUM(CAST(attributes->'usage'->>'total_tokens' AS INT)) AS total_tokens
FROM records
WHERE attributes->>'workflow_run_id' = '<uuid>'
  AND attributes->>'agent_name' = 'APPRAISER'
  AND attributes->'usage'->>'total_tokens' IS NOT NULL
  AND start_timestamp >= '<iso-start>'
  AND start_timestamp < '<iso-end>'
GROUP BY span_name
LIMIT 10
```

Call `query_schema_reference` on the Logfire MCP server once per session if the agent needs full column documentation.
