<!-- Parent: ../AGENTS.md -->
<!-- Generated: 2026-03-03 | Updated: 2026-03-03 -->

# models

## Purpose

Central Pydantic models for financial data and agent outputs. Defines the canonical types used across DCF analysis, the Appraiser agent, and scripts.

## Key Files

| File | Description |
| --------- | ---------------------------- |
| `data_types.py` | Pydantic models for `StockData`, `StockAssumptions`, and `AppraiserOutput`. Includes computed fields for derived financial metrics. |

## Subdirectories

None.

## For AI Agents

### Working In This Directory

- **Source of Truth**: Use `data_types.py` as the primary reference for all structured data models.
- **Metric Definitions**: When adding new financial metrics to `StockData`, include detailed `Field` descriptions for AI tool discovery.

### Testing Requirements

- Ensure all Pydantic models are validated against sample financial data.
- Test computed fields in `StockData` for edge cases like zero revenue or zero debt.

### Common Patterns

- **Computed Fields**: Use `@computed_field` for derived financial ratios and metrics (e.g. `ebit_margin`, `enterprise_value`).
- **Field Descriptions**: Rich `Field` descriptions enable AI tool discovery and documentation.

## Dependencies

### Internal

- This directory is used by `discount_analyst.dcf_analysis`, `discount_analyst.appraiser`, and scripts.

### External

- **pydantic**: Data validation and modeling.

<!-- MANUAL: Any manually added notes below this line are preserved on regeneration -->
