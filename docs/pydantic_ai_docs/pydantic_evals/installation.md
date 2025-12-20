## Installation

To install the Pydantic Evals package, run:

```bash
pip install pydantic-evals

```

```bash
uv add pydantic-evals

```

`pydantic-evals` does not depend on `pydantic-ai`, but has an optional dependency on `logfire` if you'd like to use OpenTelemetry traces in your evals, or send evaluation results to [logfire](https://pydantic.dev/logfire).

```bash
pip install 'pydantic-evals[logfire]'

```

```bash
uv add 'pydantic-evals[logfire]'

```
