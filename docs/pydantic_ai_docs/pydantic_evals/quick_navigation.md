## Quick Navigation

**Getting Started:**

- [Installation](#installation)
- [Quick Start](quick-start/)
- [Core Concepts](core-concepts/)

**Evaluators:**

- [Evaluators Overview](evaluators/overview/) - Compare evaluator types and learn when to use each approach
- [Built-in Evaluators](evaluators/built-in/) - Complete reference for exact match, instance checks, and other ready-to-use evaluators
- [LLM as a Judge](evaluators/llm-judge/) - Use LLMs to evaluate subjective qualities, complex criteria, and natural language outputs
- [Custom Evaluators](evaluators/custom/) - Implement domain-specific scoring logic and custom evaluation metrics
- [Span-Based Evaluation](evaluators/span-based/) - Evaluate internal agent behavior (tool calls, execution flow) using OpenTelemetry traces. Essential for complex agents where correctness depends on _how_ the answer was reached, not just the final output. Also ensures eval assertions align with production telemetry.

**How-To Guides:**

- [Logfire Integration](how-to/logfire-integration/) - Visualize results
- [Dataset Management](how-to/dataset-management/) - Save, load, generate
- [Concurrency & Performance](how-to/concurrency/) - Control parallel execution
- [Retry Strategies](how-to/retry-strategies/) - Handle transient failures
- [Metrics & Attributes](how-to/metrics-attributes/) - Track custom data

**Examples:**

- [Simple Validation](examples/simple-validation/) - Basic example

**Reference:**

- [API Documentation](../api/pydantic_evals/dataset/)
