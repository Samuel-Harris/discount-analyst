<!-- Parent: ../AGENTS.md -->
<!-- Generated: 2026-02-23 | Updated: 2026-02-23 -->

# tests

## Purpose

The `tests/` directory contains the automated test suite for the Discount Analyst project. Its primary role is to ensure the reliability and mathematical accuracy of the core financial analysis logic, particularly the Discounted Cash Flow (DCF) model. It serves as a regression suite to maintain code quality as the project's AI-driven data gathering and analysis components evolve.

## Key Files

| File | Description |
| --------- | ---------------------------- |
| `tests/dcf_analysis/test_dcf_analysis.py` | Comprehensive unit tests for the DCF calculation engine using real-world stock data scenarios. |

## Subdirectories

| Directory | Purpose |
| --------- | ----------------------------------------- |
| `dcf_analysis/` | Contains tests specifically targeting the Discounted Cash Flow analysis module. |

## For AI Agents

### Working In This Directory

- Follow the established pattern of using `Pydantic` models (e.g., `TestCase`) to define structured test data and expected results.
- When adding tests for new financial analysis logic, ensure they are added to the corresponding subdirectory (e.g., `dcf_analysis/`).
- Use `pytest.mark.parametrize` for data-driven testing to cover multiple scenarios efficiently.

### Testing Requirements

- Run the full test suite from the project root using `uv run pytest`.
- New features should include unit tests and, where applicable, integration tests with `yfinance` mocks (using the `yfinance` pytest marker).
- Ensure that test coverage is maintained or improved as per the configuration in `pytest.ini`.

### Common Patterns

- **Parametrized Testing**: Extensive use of `pytest.mark.parametrize` to run tests across multiple stock data scenarios.
- **Model-Driven Tests**: Using `Pydantic`'s `BaseModel` to structure test cases, making them easier to read and maintain.
- **Approximate Matching**: Using `pytest.approx` for comparing floating-point results in financial calculations.

## Dependencies

### Internal

- `discount_analyst.dcf_analysis`: The core DCF calculation logic being tested.
- `discount_analyst.shared.models.data_types`: Shared Pydantic models for financial data and assumptions.

### External

- **pytest**: The primary framework for running and structuring tests.
- **pydantic**: Used for defining structured test case data and expected results.

<!-- MANUAL: Any manually added notes below this line are preserved on regeneration -->
