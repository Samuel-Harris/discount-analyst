<!-- Parent: ../AGENTS.md -->
<!-- Generated: 2026-02-23 | Updated: 2026-02-23 -->

# dcf_analysis

## Purpose

The `tests/dcf_analysis/` directory contains unit tests specifically for the Discounted Cash Flow (DCF) analysis engine. Its primary role is to validate the mathematical accuracy and consistency of the DCF calculations by testing the engine against a variety of real-world financial scenarios.

## Key Files

| File | Description |
| --------- | ---------------------------- |
| `test_dcf_analysis.py` | A comprehensive test suite that uses parametrized test cases to verify DCF results (intrinsic value, enterprise value, equity value) for multiple companies. |

## Subdirectories

*No subdirectories currently present.*

## For AI Agents

### Working In This Directory

- Use the existing `TestCase` Pydantic model in `test_dcf_analysis.py` when adding new test scenarios.
- Ensure that test data (e.g., `ebit`, `revenue`, `market_cap`) is realistic and aligns with the expected `DCFAnalysisResult`.
- When adding a new test case, provide a descriptive `id` (e.g., the company name).

### Testing Requirements

- Run the tests in this directory using:
  ```bash
  poetry run pytest tests/dcf_analysis/
  ```
- All financial comparisons must use `pytest.approx` to account for floating-point precision differences.

### Common Patterns

- **Parametrized Scenarios**: Use `pytest.mark.parametrize` to run the same test logic across multiple `TestCase` instances.
- **Model-Based Assertions**: Assertions are performed by dumping Pydantic models and comparing them with `pytest.approx`.

## Dependencies

### Internal

- `discount_analyst.dcf_analysis.dcf_analysis`: The core DCF calculation logic.
- `discount_analyst.dcf_analysis.data_types`: Data structures for DCF parameters and results.
- `discount_analyst.shared.data_types`: Shared models for stock data and assumptions.

### External

- **pytest**: Test runner and parametrization framework.
- **pydantic**: Data validation and modeling for test cases.

<!-- MANUAL: Any manually added notes below this line are preserved on regeneration -->
