<!-- Parent: ../AGENTS.md -->
<!-- Generated: 2026-05-31 | Updated: 2026-07-11 -->

# toolkit

## Purpose

Optional, deterministic valuation helpers for Appraiser terminal analysis. These modules provide reusable arithmetic primitives for DCF, reverse DCF, comparable multiples, scenario distributions, sanity checks, and Rich terminal summaries. They are starter tools only: they do not own Appraiser output schemas, persistence, dashboard contracts, or investment-rating policy.

## Key Files

| File               | Description                                                                        |
| ------------------ | ---------------------------------------------------------------------------------- |
| `dcf.py`           | FCFF projection, present value, terminal value, and per-share DCF helpers.         |
| `reverse_dcf.py`   | Implied growth and margin-of-safety helpers for reverse-valuation checks.          |
| `multiples.py`     | Peer multiple summaries and EV multiple per-share valuation helpers.               |
| `scenarios.py`     | Weighted expected value and percentile distribution helpers.                       |
| `sanity_checks.py` | Monotonic percentile, expected-value, terminal-value, GDP-growth, and peer checks. |
| `reporting.py`     | Rich table helper for method summaries.                                            |

## Subdirectories

| Directory   | Purpose                                        |
| ----------- | ---------------------------------------------- |
| `examples/` | Small runnable examples for terminal analysis. |

## For AI Agents

### Working In This Directory

- Keep helpers deterministic, JSON-serialisable, and free of pydantic-ai/runtime imports.
- Do not add final recommendation logic or hidden policy decisions here.
- Prefer simple functions over framework abstractions; these helpers are meant to be copied into or called from terminal-backed analysis.

### Testing Requirements

- Run `uv run pytest tests/discount_analyst/valuation/` after changing toolkit helpers.

## Dependencies

### Internal

- None required for core helpers; examples import modules from this package.

### External

- `rich` for `reporting.py`.

<!-- MANUAL: Any manually added notes below this line are preserved on regeneration -->
