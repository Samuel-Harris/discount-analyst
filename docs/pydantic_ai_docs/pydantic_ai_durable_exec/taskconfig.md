### TaskConfig

Bases: `TypedDict`

Configuration for a task in Prefect.

These options are passed to the `@task` decorator.

Source code in `pydantic_ai_slim/pydantic_ai/durable_exec/prefect/_types.py`

```python
class TaskConfig(TypedDict, total=False):
    """Configuration for a task in Prefect.

    These options are passed to the `@task` decorator.
    """

    retries: int
    """Maximum number of retries for the task."""

    retry_delay_seconds: float | list[float]
    """Delay between retries in seconds. Can be a single value or a list for custom backoff."""

    timeout_seconds: float
    """Maximum time in seconds for the task to complete."""

    cache_policy: CachePolicy
    """Prefect cache policy for the task."""

    persist_result: bool
    """Whether to persist the task result."""

    result_storage: ResultStorage
    """Prefect result storage for the task. Should be a storage block or a block slug like `s3-bucket/my-storage`."""

    log_prints: bool
    """Whether to log print statements from the task."""

```

#### retries

```python
retries: int

```

Maximum number of retries for the task.

#### retry_delay_seconds

```python
retry_delay_seconds: float | list[float]

```

Delay between retries in seconds. Can be a single value or a list for custom backoff.

#### timeout_seconds

```python
timeout_seconds: float

```

Maximum time in seconds for the task to complete.

#### cache_policy

```python
cache_policy: CachePolicy

```

Prefect cache policy for the task.

#### persist_result

```python
persist_result: bool

```

Whether to persist the task result.

#### result_storage

```python
result_storage: ResultStorage

```

Prefect result storage for the task. Should be a storage block or a block slug like `s3-bucket/my-storage`.

#### log_prints

```python
log_prints: bool

```

Whether to log print statements from the task.
