### ApprovalRequired

Bases: `Exception`

Exception to raise when a tool call requires human-in-the-loop approval.

See [tools docs](../../deferred-tools/#human-in-the-loop-tool-approval) for more information.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `metadata` | `dict[str, Any] | None` | Optional dictionary of metadata to attach to the deferred tool call. This metadata will be available in DeferredToolRequests.metadata keyed by tool_call_id. | `None` |

Source code in `pydantic_ai_slim/pydantic_ai/exceptions.py`

```python
class ApprovalRequired(Exception):
    """Exception to raise when a tool call requires human-in-the-loop approval.

    See [tools docs](../deferred-tools.md#human-in-the-loop-tool-approval) for more information.

    Args:
        metadata: Optional dictionary of metadata to attach to the deferred tool call.
            This metadata will be available in `DeferredToolRequests.metadata` keyed by `tool_call_id`.
    """

    def __init__(self, metadata: dict[str, Any] | None = None):
        self.metadata = metadata
        super().__init__()

```
