# Failure kinds

Classify **in-scope** FAILED/CANCELLED lanes. Confirm in code; do not treat the label as proof.

A gate `rejected` + run `FAILED` + error containing `DataQualityRejection`/`SentinelRejection` is a **persist bug**, not “the ticker is invalid”. A gate reject that persisted correctly is run `COMPLETED` with `decision_type=data_quality_rejection` — **out of scope** as an error.

If some lanes COMPLETED, FAILED is usually per-ticker, not “the workflow is broken globally”.

| Kind                              | Typical SQLite                                                                                 | Typical Logfire                                                                            | Meaning                                                                                             |
| --------------------------------- | ---------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------- |
| Schema / persist                  | Pydantic `model_validate` on wrong union member; `DataQualityRejection` vs `SentinelRejection` | Same `ValidationError` across many tickers near gate persist                               | Orchestrator bug, not a bad stock                                                                   |
| Vendor plan / coverage            | `resolution_notes` HTTP 402/403; search 0 rows; user-facing “no confident FMP match”           | `httpx.HTTPStatusError`                                                                    | Plan/coverage or identity; **not** “ticker does not exist” until you check search-by-ticker vs name |
| Vendor payload                    | `"NA"` / `"N/A"` into `float`; `EodhdRealTimeQuote.close`                                      | `float_parsing`                                                                            | Weekend/NA quote, not necessarily delisted                                                          |
| Tool retry exhaustion             | `Tool 'web_fetch' exceeded max retries count of 1`                                             | `UnexpectedModelBehavior`; prior span has 401/403/timeout                                  | Default tool retries are 1; 4xx is not retried usefully                                             |
| Structured output                 | `{payload: EvaluationReport}` wrap; missing fields; `run_stream()` cannot retry                | `Output validation failed during streaming, and retries are not supported in run_stream()` | Schema/stream, not “the model is stupid”                                                            |
| HTTP timeout / empty stored error | Run FAILED, `error_message` null or empty; maybe no conversation                               | `httpx.ReadTimeout` / `ReadError`                                                          | Infrastructure hole; Logfire required                                                               |
| Provider rate limit               | `Rate limit reached` / TPM / tokens per min                                                    | same in exception_message                                                                  | Transient provider quota; last stored error after retries may be only this                          |
| Retry overlay                     | `completed_at` days after `started_at`; last error is 403 while snapshots still show FMP 402   | Multiple `Workflow execution started` / `failed-agent retry scheduled`                     | Stored error is the **last** attempt                                                                |
| Surveyor failed                   | No ticker runs, or workflow FAILED with surveyor execution failed                              | Surveyor stage exception                                                                   | Workflow fails even with no lanes (`recompute_workflow_status`)                                     |
| Cancelled                         | `status=cancelled` on run or execution                                                         | Cancel span                                                                                | In scope (retry button). Not the same as FAILED                                                     |
| Intended rejection                | COMPLETED + `sentinel_rejection` or `data_quality_rejection`                                   | “Applying … rejection verdict”                                                             | **Not** a workflow error for that ticker                                                            |
| Agent quality                     | Conversation exists, schema valid, gate passed, still FAILED with a reasoning bug              | Little or no exception                                                                     | Rare; only then consider `analyse-workflow-run`                                                     |

## Classifier fingerprints (substring / exception_type)

Use these as **first-pass** labels in the cluster script, then confirm:

1. `DataQualityRejection` / `SentinelRejection` + `model_type` → persist union
2. `EodhdRealTimeQuote` / `close=` → vendor payload
3. `EvaluationReport` / `material_data_gaps` / `run_stream()` → structured output
4. `web_fetch` + `max retries` → tool retry exhaustion (read HTTP code from the same string or prior span)
5. `402` / `ACCESS DENIED` / FMP in `resolution_notes` → vendor plan (check snapshots; retries may have overwritten `runs.error_message`)
6. `httpx.ReadTimeout` / `ReadError` / empty `error_message` → timeout / hole
7. `HTTP 401` / `403` in stored URL → last vendor HTTP (redact `api_token`); still look earlier in Logfire
8. `Rate limit reached` / `tokens per min` / `TPM` → provider rate limit

## Join gotchas

- Surveyor: `agent_executions.workflow_run_id` set, `run_id` null. Filter `(ae.workflow_run_id = ? OR r.workflow_run_id = ?)`.
- SKIPPED downstream rows copy the failing stage’s error. Originating row: FAILED/CANCELLED with `started_at` set.
- `candidate_snapshots` often keep the **first** gate story after retries overwrite `runs.error_message`. `gate_probed_at` can still be the last attempt.
- Long-retried workflows: a global Logfire `LIMIT 80` is not the full timeline. Filter `attributes->>'ticker'` for each in-scope lane.
- Last TPM / connection error after a failed-agent retry can leave **zero** conversation messages (prior transcript wiped; stream never checkpointed).
- Agent names in SQLite are often **lowercase** (`profiler`). Digest filenames may be `PROFILER_…`. `runs.entry_path` may be stored as `SURVEYOR` / `PROFILER` even though `models.py` enum **values** are lowercase — filter with `lower(...)`.
- Workflow/run/execution **status** in SQLite is commonly the enum **name** (`FAILED`, `CANCELLED`, `COMPLETED`), not the `models.py` value (`failed`). Always compare case-insensitively. `WHERE status = 'failed'` returns 0 rows on a FAILED workflow.
- Terminal success is text `exit_code: 0` in `tool_return` parts, not JSON.
