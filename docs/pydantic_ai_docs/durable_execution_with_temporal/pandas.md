### Pandas

When `logfire.info` is used inside an activity and the `pandas` package is among your project's dependencies, you may encounter the following error which seems to be the result of an import race condition:

```text
AttributeError: partially initialized module 'pandas' has no attribute '_pandas_parser_CAPI' (most likely due to a circular import)

```

To fix this, you can use the [`temporalio.workflow.unsafe.imports_passed_through()`](https://python.temporal.io/temporalio.workflow.unsafe.html#imports_passed_through) context manager to proactively import the package and not have it be reloaded in the workflow sandbox:

temporal_activity.py

```python
from temporalio import workflow

with workflow.unsafe.imports_passed_through():
    import pandas

```
