<!-- Parent: ../AGENTS.md -->
<!-- Generated: 2026-04-05 -->

# valuation

## Purpose

Valuation domain: `StockData` / `StockAssumptions`, DCF parameter and result models, and the `DCFAnalysis` engine. Intentionally free of agent prompt/runtime imports.

## Key Files

| File              | Description                                      |
| ----------------- | ------------------------------------------------ |
| `schema.py`       | `StockData`, `StockAssumptions`.                 |
| `data_types.py`   | `DCFAnalysisParameters`, `DCFAnalysisResult`.    |
| `dcf_analysis.py` | `DCFAnalysis` class and `dcf_analysis()` method. |

## Dependencies

### Internal

- `schema.py` is imported by `data_types.py`; tests live in `tests/dcf_analysis/`.

### External

- **pydantic**.
