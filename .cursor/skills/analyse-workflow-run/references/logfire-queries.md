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

Call `query_schema_reference` on the Logfire MCP server once per session if the agent needs full column documentation.
