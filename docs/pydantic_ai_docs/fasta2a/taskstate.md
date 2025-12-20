### TaskState

```python
TaskState: TypeAlias = Literal[
    "submitted",
    "working",
    "input-required",
    "completed",
    "canceled",
    "failed",
    "rejected",
    "auth-required",
    "unknown",
]

```

The possible states of a task.
