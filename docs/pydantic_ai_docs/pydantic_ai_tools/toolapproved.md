### ToolApproved

Indicates that a tool call has been approved and that the tool function should be executed.

Source code in `pydantic_ai_slim/pydantic_ai/tools.py`

```python
@dataclass(kw_only=True)
class ToolApproved:
    """Indicates that a tool call has been approved and that the tool function should be executed."""

    override_args: dict[str, Any] | None = None
    """Optional tool call arguments to use instead of the original arguments."""

    kind: Literal['tool-approved'] = 'tool-approved'

```

#### override_args

```python
override_args: dict[str, Any] | None = None

```

Optional tool call arguments to use instead of the original arguments.
