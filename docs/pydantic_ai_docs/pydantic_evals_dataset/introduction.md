Dataset management for pydantic evals.

This module provides functionality for creating, loading, saving, and evaluating datasets of test cases. Each case must have inputs, and can optionally have a name, expected output, metadata, and case-specific evaluators.

Datasets can be loaded from and saved to YAML or JSON files, and can be evaluated against a task function to produce an evaluation report.
