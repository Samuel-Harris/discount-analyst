<!-- Parent: ../AGENTS.md -->
<!-- Generated: 2026-04-05 | Updated: 2026-05-31 -->

# pipeline

## Purpose

Non-LLM pipeline contracts for **human-facing verdicts**: `SentinelRejection` (programmatic short-circuit when Sentinel blocks valuation), `DataQualityRejection` (pre-Researcher ticker/listing gate failure), `RatingTableDecision` (deterministic post-Appraiser rating from `rating_decision_table.py`), and **`Verdict`** (hoisted summary fields plus typed `decision: RatingTableDecision | SentinelRejection | DataQualityRejection`). Builders live in `builders.py`. Deterministic pre-Researcher gates live in `candidate_gates.py`.

## Key Files

| File                       | Description                                                                                                                               |
| -------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------- |
| `schema.py`                | `SentinelRejection`, `DataQualityRejection`, `RatingTableDecision`, `Verdict`, related rationale types.                                   |
| `candidate_gates.py`       | `validate_candidate`, pass/reject `CandidateGateResult` union, and internal FMP profile / EODHD ticker/listing probes (no `quote-short`). |
| `rating_decision_table.py` | Flat ``match`` on ``(MoS, conviction, reservations)`` and ``(rating, position)`` with ``assert_never``.                                   |
| `builders.py`              | `build_sentinel_rejection`, `build_data_quality_rejection`, `build_rating_table_decision`, `verdict_from_decision`.                       |
| `__init__.py`              | Package docstring only (no barrel re-exports).                                                                                            |

## Dependencies

- Uses `InvestmentRating` and `MarginOfSafetyAssessment` from `discount_analyst.rating.*` (explicit submodule imports; no barrel file on `discount_analyst.rating`).
- Uses `EvaluationReport`, `ThesisVerdict`, `MispricingThesis`, `SurveyorLaneContext` for rejection and rating-table construction.

## For AI Agents

- Keep this package free of pydantic-ai agents and tools; orchestration belongs in `scripts/workflows/` and `backend/pipeline/`.
