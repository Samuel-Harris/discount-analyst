## Code-First Evaluation

Pydantic Evals follows a **code-first approach** where you define all evaluation components (datasets, experiments, tasks, cases and evaluators) in Python code, or as serialized data loaded by Python code. This differs from platforms with fully web-based configuration.

When you run an _Experiment_ you'll see a progress indicator and can print the results wherever you run your python code (IDE, terminal, etc). You also get a report object back that you can serialize and store or send to a notebook or other application for further visualization and analysis.

If you are using [Pydantic Logfire](https://logfire.pydantic.dev/docs/guides/web-ui/evals/), your experiment results automatically appear in the Logfire web interface for visualization, comparison, and collaborative analysis. Logfire serves as a observability layer - you write and run evals in code, then view and analyze results in the web UI.
