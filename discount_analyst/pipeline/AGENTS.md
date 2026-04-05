<!-- Parent: ../AGENTS.md -->
<!-- Generated: 2026-04-05 -->

# pipeline

## Purpose

Non-LLM pipeline contracts for **human-facing verdicts**: `SentinelRejection` (programmatic short-circuit when Sentinel blocks valuation) and `Verdict` (hoisted summary fields plus `decision: ArbiterDecision | SentinelRejection` for provenance). Builders live in `builders.py`.

## Key Files

| File          | Description                                          |
| ------------- | ---------------------------------------------------- |
| `schema.py`   | `SentinelRejection`, `Verdict`.                      |
| `builders.py` | `build_sentinel_rejection`, `verdict_from_decision`. |
| `__init__.py` | Re-exports public API.                               |

## Dependencies

- Imports `ArbiterDecision` from `discount_analyst.agents.arbiter.schema` only (not the agent package graph for “LLM” confusion).
- Uses `InvestmentRating` from `discount_analyst.rating` for hoisted ratings.
- Uses `EvaluationReport`, `ThesisVerdict`, `MispricingThesis` for rejection construction.

## For AI Agents

- Keep this package free of pydantic-ai agents and tools; orchestration belongs in `scripts/workflows/`.
