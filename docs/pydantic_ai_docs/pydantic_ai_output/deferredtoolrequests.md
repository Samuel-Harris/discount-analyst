### DeferredToolRequests

Tool calls that require approval or external execution.

This can be used as an agent's `output_type` and will be used as the output of the agent run if the model called any deferred tools.

Results can be passed to the next agent run using a DeferredToolResults object with the same tool call IDs.

See [deferred tools docs](../../deferred-tools/#deferred-tools) for more information.

Source code in `pydantic_ai_slim/pydantic_ai/tools.py`

```python
@dataclass(kw_only=True)
class DeferredToolRequests:
    """Tool calls that require approval or external execution.

    This can be used as an agent's `output_type` and will be used as the output of the agent run if the model called any deferred tools.

    Results can be passed to the next agent run using a [`DeferredToolResults`][pydantic_ai.tools.DeferredToolResults] object with the same tool call IDs.

    See [deferred tools docs](../deferred-tools.md#deferred-tools) for more information.
    """

    calls: list[ToolCallPart] = field(default_factory=list)
    """Tool calls that require external execution."""
    approvals: list[ToolCallPart] = field(default_factory=list)
    """Tool calls that require human-in-the-loop approval."""
    metadata: dict[str, dict[str, Any]] = field(default_factory=dict)
    """Metadata for deferred tool calls, keyed by `tool_call_id`."""

```

#### calls

```python
calls: list[ToolCallPart] = field(default_factory=list)

```

Tool calls that require external execution.

#### approvals

```python
approvals: list[ToolCallPart] = field(default_factory=list)

```

Tool calls that require human-in-the-loop approval.

#### metadata

```python
metadata: dict[str, dict[str, Any]] = field(
    default_factory=dict
)

```

Metadata for deferred tool calls, keyed by `tool_call_id`.
