### DeferredToolResults

Results for deferred tool calls from a previous run that required approval or external execution.

The tool call IDs need to match those from the DeferredToolRequests output object from the previous run.

See [deferred tools docs](../../deferred-tools/#deferred-tools) for more information.

Source code in `pydantic_ai_slim/pydantic_ai/tools.py`

```python
@dataclass(kw_only=True)
class DeferredToolResults:
    """Results for deferred tool calls from a previous run that required approval or external execution.

    The tool call IDs need to match those from the [`DeferredToolRequests`][pydantic_ai.output.DeferredToolRequests] output object from the previous run.

    See [deferred tools docs](../deferred-tools.md#deferred-tools) for more information.
    """

    calls: dict[str, DeferredToolCallResult | Any] = field(default_factory=dict)
    """Map of tool call IDs to results for tool calls that required external execution."""
    approvals: dict[str, bool | DeferredToolApprovalResult] = field(default_factory=dict)
    """Map of tool call IDs to results for tool calls that required human-in-the-loop approval."""

```

#### calls

```python
calls: dict[str, DeferredToolCallResult | Any] = field(
    default_factory=dict
)

```

Map of tool call IDs to results for tool calls that required external execution.

#### approvals

```python
approvals: dict[str, bool | DeferredToolApprovalResult] = (
    field(default_factory=dict)
)

```

Map of tool call IDs to results for tool calls that required human-in-the-loop approval.
