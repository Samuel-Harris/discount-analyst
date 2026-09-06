# Pipeline synthesis (parent agent)

Per-agent subagents cannot see the composition of the book. After they return, the **parent** must independently reconstruct how Surveyor → Profiler → Researcher → Strategist → Sentinel → (Appraiser) → rating table → Curator produced the final ratings and allocation. Do **not** concatenate subagent prose into the HTML report.

Treat Luna (and every other lane model) as untrusted. Subagent findings are claims. SQLite rows and live pipeline code are facts.

## Separate three layers

| Layer                  | Question                                                                            | Typical mistake                                                                                            |
| ---------------------- | ----------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------- |
| Historical stop-errors | Did a crash or rate-limit halt the run, and was it later repaired?                  | Treating Logfire exceptions as the reason every name is SELL                                               |
| Gate / policy          | What did **code** force once an agent submitted structured output?                  | Blaming Curator for 100% cash when every lane was packed `forced_zero`                                     |
| Judgement              | Was the model’s evidence labelling, thesis design, or valuation actually warranted? | Equating “thesis unproven — do not proceed to valuation” with “intrinsic value is below price; exit at 0%” |

SQLite is authoritative for **final** outcomes (`runs`, `run_final_decisions`, `evaluation_reports`, `portfolio_allocations`). Logfire counts include retries (e.g. more “Sentinel gate did not pass” spans than final rejections).

## Required fact queries (adapt after `.schema`)

Decision mix, holdings vs prospects:

```sql
SELECT is_existing_position, decision_type, final_rating, recommended_action, COUNT(*) AS n
FROM runs
WHERE workflow_run_id = '<uuid>'
GROUP BY 1, 2, 3, 4
ORDER BY n DESC;
```

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

Appraiser skips vs completions:

```sql
SELECT status, COUNT(*) AS n
FROM agent_executions ae
LEFT JOIN runs r ON r.id = ae.run_id
WHERE (ae.workflow_run_id = '<uuid>' OR r.workflow_run_id = '<uuid>')
  AND ae.agent_name = 'appraiser'
GROUP BY status;
```

`SKIPPED` after a Sentinel rejection is intended, not a crash.

## Live code to re-read (do not rely on memory)

| Effect                                                     | Module                                                                  |
| ---------------------------------------------------------- | ----------------------------------------------------------------------- |
| Derived `thesis_verdict` from assessments / `gap_kind`     | `backend/src/discount_analyst/agents/sentinel/derive_thesis_verdict.py` |
| Whether Appraiser runs                                     | `sentinel_proceeds_to_valuation` in `agents/sentinel/schema.py`         |
| Sentinel reject → SELL / “Exit the position.”              | `application/decisions/builders.py` (`build_sentinel_rejection`)        |
| Rating → `investable` / `retain_or_reduce` / `forced_zero` | `domain/allocations/eligibility.py`                                     |
| Curator must obey packed policy                            | `agents/curator/system_prompt.py`                                       |

One-strike rule (current): any `Weakens thesis` with `gap_kind` in `{none, never_disclosed, contradicted}` becomes **do not proceed**, regardless of the balance of other answers or whether the name is already held. Calendar-only Weakens become reservations and **can** proceed.

## Distinctions the report must make

- **Holdings vs prospects.** “Do not initiate” is a weaker economic claim than “exit the position at target 0%”. Do not roll them into one “all SELL” headline without the split.
- **Sentinel rejection vs rating-table SELL.** The former is a pre-valuation proof-gate failure. The latter is a margin-of-safety table after Appraiser. They are not interchangeable evidence.
- **Mechanical vs discretionary.** If every packed policy is `forced_zero`, Curator **cannot** hold equity. Challenge the upstream rating/gate, not Curator nerve.
- **Valid company caution vs book liquidation.** Printed deterioration can justify *caution* on a name without justifying an unvalued forced-zero across the whole book.
- **Tool/cache failure vs missing economics.** Official helper failures (SEC user-agent, Companies House cache, missing `curl`/`pdftotext`) must not be treated as thesis-breaking facts unless the filing itself is absent.

## Causal-chain template

Write this in the HTML **Pipeline synthesis** section, with ticker examples:

1. What Surveyor/Profiler actually admitted (null metrics, mandate-fit language, red-flag catalogues).
2. Which Researcher gaps were unpublished economics vs promoted tool failures.
3. How Strategist questions were framed (recovery theses fail closed-book Sentinel; overvaluation theses can pass on the same missing granularity).
4. What Sentinel **code** did with those assessments vs what the model’s own `thesis_verdict` said before overwrite.
5. Which names reached Appraiser and whether those SELLs recompute from stored distributions.
6. What Curator was legally allowed to size.
7. Independent verdict on the **book** (e.g. 100% cash): mechanically compelled, economically defensible, or an over-escalation of a research stop into a liquidation.

If the user asked a specific concern (over-caution, cash, a ticker), **lead the executive summary with that answer**.
