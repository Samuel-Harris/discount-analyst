<!-- Parent: ../AGENTS.md -->
<!-- Generated: 2026-03-03 | Updated: 2026-04-03 -->

# schemas

## Purpose

Central Pydantic schemas for financial data and agent outputs. This directory defines canonical model types used by DCF analysis, Surveyor, Researcher, Appraiser, and script entry points.

## Key Files

| File          | Description                                                                                                                       |
| ------------- | --------------------------------------------------------------------------------------------------------------------------------- |
| `stock.py`    | `StockData` and `StockAssumptions` models used by DCF and Appraiser output typing.                                                |
| `surveyor.py` | Surveyor enums (`Exchange`, `Currency`, `StockCategory`) and models (`KeyMetrics`, `SurveyorCandidate`, `SurveyorOutput`).        |
| `researcher.py` | Researcher output schemas (`DeepResearchReport`, `MarketNarrative`, and nested report sections) built from `SurveyorCandidate`. |
| `appraiser.py`  | Appraiser output schema (`AppraiserOutput`): `StockData` + `StockAssumptions` for DCF workflows.                                |
| `__init__.py` | Package initialization file for `discount_analyst.shared.schemas`.                                                                |

## Subdirectories

None.

## For AI Agents

### Working In This Directory

- **Source of truth**: Use `stock.py` for DCF/Appraiser financial line items, `appraiser.py` for Appraiser agent output typing, `surveyor.py` for Surveyor candidate/output schemas, and `researcher.py` for structured deep-research outputs.
- **Metric Definitions**: When adding new financial metrics to `StockData`, include detailed `Field` descriptions for tool and prompt clarity.

### Testing Requirements

- Ensure all schema changes are validated with `uv run pytest`.
- Test computed fields in `StockData` for edge cases like zero revenue or zero debt.

### Common Patterns

- **Computed Fields**: Keep derived financial metrics in `StockData` with `@computed_field`.
- **Field Descriptions**: Rich `Field` descriptions improve model reliability and documentation quality.

## Dependencies

### Internal

- Used by `discount_analyst.dcf_analysis`, `discount_analyst.agents.appraiser`, `discount_analyst.agents.surveyor`, and scripts.

### External

- **pydantic**: Data validation and modeling.

<!-- MANUAL: Any manually added notes below this line are preserved on regeneration -->
