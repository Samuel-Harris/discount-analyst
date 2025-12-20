### StepConfig

Bases: `TypedDict`

Configuration for a step in the DBOS workflow.

Source code in `pydantic_ai_slim/pydantic_ai/durable_exec/dbos/_utils.py`

```python
class StepConfig(TypedDict, total=False):
    """Configuration for a step in the DBOS workflow."""

    retries_allowed: bool
    interval_seconds: float
    max_attempts: int
    backoff_rate: float

```
