<!-- Parent: ../AGENTS.md -->
<!-- Generated: 2026-02-23 | Updated: 2026-02-23 -->

# dcf_analysis

## Purpose

The core financial modeling engine for calculating the intrinsic value of a stock using the Discounted Cash Flow (DCF) method. This directory implements the mathematical logic for Weighted Average Cost of Capital (WACC), Free Cash Flow (FCF) projections, and Terminal Value calculations based on provided financial data and assumptions.

## Key Files

| File | Description |
| --------- | ---------------------------- |
| `dcf_analysis.py` | Primary implementation of the `DCFAnalysis` class, containing the step-by-step logic for enterprise value calculation. |
| `data_types.py` | Pydantic models for `DCFAnalysisParameters` and `DCFAnalysisResult`, ensuring structured data flow for the analysis engine. |

## Subdirectories

*No subdirectories currently exist in this folder.*

## For AI Agents

### Working In This Directory

- **Mathematical Accuracy**: Ensure any modifications to the DCF logic align with standard financial modeling practices (e.g., CAPM for cost of equity, "Bottom-Up" for FCF).
- **Validation**: Use the Pydantic models in `data_types.py` for all inputs and outputs. The `DCFAnalysis` class includes validation checks for growth rates and forecast periods.
- **Pure Logic**: This directory should remain focused on pure financial calculation logic, independent of data fetching or AI agent orchestration.

### Testing Requirements

- **Unit Testing**: All financial formulas must be covered by unit tests in `tests/dcf_analysis/` to prevent regression.
- **Edge Cases**: Verify behavior with extreme inputs (e.g., zero debt, negative growth rates, very short forecast periods).

### Common Patterns

- **Initialization**: `DCFAnalysis` is initialized with a `DCFAnalysisParameters` object containing both raw `StockData` and `StockAssumptions`.
- **Method Flow**: The engine follows a standard flow: `_calculate_discount_rate` -> `_forecast_free_cash_flows` -> `_calculate_terminal_value` -> `_calculate_enterprise_value`.

## Dependencies

### Internal

- `discount_analyst.shared.data_types`: Depends on `StockData` and `StockAssumptions` models.

### External

- **pydantic**: Used for defining strict data structures for analysis parameters and results.

<!-- MANUAL: Any manually added notes below this line are preserved on regeneration -->
