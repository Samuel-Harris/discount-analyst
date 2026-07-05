<!-- Parent: ../AGENTS.md -->
<!-- Generated: 2026-04-05 | Updated: 2026-05-31 (canonical toolkit DCF) -->

# valuation

## Purpose

Valuation domain: shared `StockData` / `StockAssumptions` schemas plus policy-free toolkit helpers for Appraiser terminal calculations. `toolkit/dcf.py` is the canonical in-repo DCF calculation surface. Intentionally free of agent prompt/runtime imports. **Percentage convention:** caller- and model-facing rates use `*_pct` fields (e.g. `4.5` means 4.5%); helpers convert to fractional rates internally where needed.

## Key Files

| File        | Description                                                      |
| ----------- | ---------------------------------------------------------------- |
| `schema.py` | Shared `StockData` and `StockAssumptions` schemas for valuation. |

## Subdirectories

| Directory  | Purpose                                                                                             |
| ---------- | --------------------------------------------------------------------------------------------------- |
| `toolkit/` | Optional deterministic helpers for DCF, reverse DCF, multiples, scenario distributions, and checks. |

## Dependencies

### Internal

- `toolkit/` is imported by Appraiser terminal scripts and tests under `tests/discount_analyst/valuation/`; it must not import pydantic-ai, backend persistence, or final rating policy.

### External

- **pydantic**.
- **rich** for optional reporting-table helpers.
