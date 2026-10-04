# Pipeline synthesis (parent agent)

Per-agent subagents cannot see the composition of the book. After they return, the **parent** must independently reconstruct how Surveyor → Profiler → Researcher → Strategist → Sentinel → Appraiser → Curator produced the allocation. Do **not** concatenate subagent prose into the HTML report.

Treat Luna (and every other lane model) as untrusted. Subagent findings are claims. SQLite rows and live pipeline code are facts.

**Live path (new runs):** Sentinel and Appraiser are research/valuation **memos**. There is no live BUY/SELL/HOLD rating and no allocation policy kind. **Curator weights are the recommendation.** Data-quality rejects skip Researcher→Appraiser, are omitted from the Curator LLM pack, and are application-stamped `[0,0,0]`. Historical SQLite may still contain `rating_table` / `sentinel_rejection` rows and a stored `final_rating`; treat those as display of old runs, not current behaviour.

## Separate three layers

| Layer                  | Question                                                                           | Typical mistake                                                                                         |
| ---------------------- | ---------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------- |
| Historical stop-errors | Did a crash or rate-limit halt the run, and was it later repaired?                 | Treating Logfire exceptions as the reason every name is sized to zero                                   |
| Gate / stamp           | What did **code** force once an agent submitted structured output?                 | Blaming Curator for 100% cash when every lane was a data-quality reject (stamped zeros, LLM not called) |
| Judgement              | Was the model’s evidence labelling, thesis design, valuation, or sizing warranted? | Equating a Sentinel “do not proceed” **label** with “intrinsic value is below price; exit at 0%”        |

SQLite is authoritative for **final** outcomes (`runs`, `run_final_decisions`, `evaluation_reports`, `portfolio_allocations`). Logfire counts include retries.

## Required fact queries (adapt after `.schema`)

Decision mix, holdings vs prospects:

```sql
SELECT is_existing_position, decision_type, final_rating, recommended_action, COUNT(*) AS n
FROM runs
WHERE workflow_run_id = '<uuid>'
GROUP BY 1, 2, 3, 4
ORDER BY n DESC;
```

On **new** runs expect `decision_type` in `{appraised, data_quality_rejection}` and `final_rating` NULL. `rating_table` / `sentinel_rejection` and a stored rating mean a historical run.

Sentinel derived verdict vs red-flag screen:

```sql
SELECT er.thesis_verdict, er.overall_red_flag_verdict, COUNT(*) AS n
FROM evaluation_reports er
JOIN agent_executions ae ON ae.id = er.agent_execution_id
JOIN runs r ON r.id = ae.run_id
WHERE r.workflow_run_id = '<uuid>'
GROUP BY 1, 2;
```

Question-assessment tallies (the derivation input):

```sql
SELECT qa.verdict, qa.confidence, qa.gap_kind, COUNT(*) AS n
FROM evaluation_question_assessments qa
JOIN evaluation_reports er ON er.id = qa.evaluation_report_id
JOIN agent_executions ae ON ae.id = er.agent_execution_id
JOIN runs r ON r.id = ae.run_id
WHERE r.workflow_run_id = '<uuid>'
GROUP BY 1, 2, 3
ORDER BY n DESC;
```

Per-ticker support/weaken/gap counts:

```sql
SELECT r.ticker, r.is_existing_position, r.decision_type, r.final_rating,
       er.thesis_verdict,
       SUM(CASE WHEN qa.verdict = 'Supports thesis' THEN 1 ELSE 0 END) AS supports,
       SUM(CASE WHEN qa.verdict = 'Neutral' THEN 1 ELSE 0 END) AS neutral,
       SUM(CASE WHEN qa.verdict = 'Weakens thesis' THEN 1 ELSE 0 END) AS weakens,
       SUM(CASE WHEN qa.verdict = 'Breaks thesis' THEN 1 ELSE 0 END) AS breaks,
       SUM(CASE WHEN qa.gap_kind = 'never_disclosed' THEN 1 ELSE 0 END) AS never_disclosed,
       SUM(CASE WHEN qa.gap_kind = 'contradicted' THEN 1 ELSE 0 END) AS contradicted,
       SUM(CASE WHEN qa.gap_kind = 'calendar' THEN 1 ELSE 0 END) AS calendar_gaps
FROM runs r
JOIN agent_executions ae ON ae.run_id = r.id AND ae.agent_name = 'sentinel'
JOIN evaluation_reports er ON er.agent_execution_id = ae.id
JOIN evaluation_question_assessments qa ON qa.evaluation_report_id = er.id
WHERE r.workflow_run_id = '<uuid>'
GROUP BY r.ticker
ORDER BY r.is_existing_position DESC, r.ticker;
```

Lane origin (Profiler coverage is **not** “< 25 conversations”):

```sql
SELECT entry_path, is_existing_position, COUNT(*) AS n
FROM runs
WHERE workflow_run_id = '<uuid>'
GROUP BY 1, 2;
```

Warn only when a **Profiler-entry** lane lacks a Profiler conversation. Surveyor-originated names never have Profiler conversations by design.

Appraiser completions (live path does **not** skip Appraiser after Sentinel):

```sql
SELECT status, COUNT(*) AS n
FROM agent_executions ae
LEFT JOIN runs r ON r.id = ae.run_id
WHERE (ae.workflow_run_id = '<uuid>' OR r.workflow_run_id = '<uuid>')
  AND ae.agent_name = 'appraiser'
GROUP BY status;
```

`SKIPPED` Appraiser on a **new** run is DQR (or a lane failure before Sentinel), not a Sentinel skip. Historical runs may still show Appraiser skipped after `sentinel_rejection`.

## Live code to re-read (do not rely on memory)

| Effect                                                 | Module                                                                                          |
| ------------------------------------------------------ | ----------------------------------------------------------------------------------------------- |
| Derived `thesis_verdict` from assessments / `gap_kind` | `backend/src/discount_analyst/agents/sentinel/derive_thesis_verdict.py`                         |
| Whether Appraiser runs                                 | `ticker_lane_stage.py` / CLI `run_full_workflow.py` — always after Sentinel except DQR          |
| New-run completion artefact                            | `AppraisedDecision` via `build_appraised_decision`                                              |
| Historical Sentinel/rating JSON (display only)         | `application/decisions/builders.py` (`build_sentinel_rejection`, `build_rating_table_decision`) |
| Curator pack + DQR stamps                              | `application/allocations/assemble.py`, `finalise.py`                                            |
| Curator may size any valued lane                       | `agents/curator/system_prompt.py`                                                               |

Derivation (current): Medium/High Breaks → BROKEN; Weakens with `gap_kind` in `{none, contradicted}` → WEAKENED; `never_disclosed` is a soft gap like `calendar`; Unproven fires only on the printed (non-soft) set when Low share ≥ 50% **and** the full list has at least one Weakens or Breaks; any remaining soft gap → reservations; else intact. Labels do **not** skip Appraiser.

## Distinctions the report must make

- **Holdings vs prospects.** Curator `action` (`enter` / `increase` / `hold` / `reduce` / `exit` / `avoid`) is derived from current weight vs the proposed band, not from a BUY/SELL chip.
- **Historical ratings vs live book.** A stored `final_rating` is an old run. New `appraised` rows have a null rating; the book is the recommendation.
- **DQR stamp vs Curator discretion.** If every lane is DQR, the LLM is not called; cash is synthesised at 100% plus stamped zeros. That is mechanical, not Curator caution.
- **Sentinel label vs valuation.** Weakened/unproven/broken strings remain evidence for Appraiser and Curator. They are not “intrinsic value is below price”.
- **Tool/cache failure vs missing economics.** Official helper failures (SEC user-agent, Companies House cache, missing `curl`/`pdftotext`) must not be treated as thesis-breaking facts unless the filing itself is absent.

## Causal-chain template

Write this in the HTML **Pipeline synthesis** section, with ticker examples:

1. What Surveyor/Profiler actually admitted (null metrics, mandate-fit language, red-flag catalogues).
2. Which Researcher gaps were unpublished economics vs promoted tool failures.
3. How Strategist questions were framed (unpublished cohort/ARR bridges vs last-period facts).
4. What Sentinel **code** did with those assessments vs what the model’s own `thesis_verdict` said before overwrite.
5. Which names reached Appraiser (all non-DQR on new runs) and whether the valuation memo is coherent.
6. What Curator sized (weights, cash, 15% cap) versus DQR stamps.
7. Independent verdict on the **book**: discretionary Curator sizing, DQR-only cash, or a historical forced-zero liquidation that the live path no longer produces.

If the user asked a specific concern (over-caution, cash, a ticker), **lead the executive summary with that answer**.
