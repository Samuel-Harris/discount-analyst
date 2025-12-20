### DeltaToolCall

Incremental change to a tool call.

Used to describe a chunk when streaming structured responses.

Source code in `pydantic_ai_slim/pydantic_ai/models/function.py`

```python
@dataclass
class DeltaToolCall:
    """Incremental change to a tool call.

    Used to describe a chunk when streaming structured responses.
    """

    name: str | None = None
    """Incremental change to the name of the tool."""

    json_args: str | None = None
    """Incremental change to the arguments as JSON"""

    _: KW_ONLY

    tool_call_id: str | None = None
    """Incremental change to the tool call ID."""

```

#### name

```python
name: str | None = None

```

Incremental change to the name of the tool.

#### json_args

```python
json_args: str | None = None

```

Incremental change to the arguments as JSON

#### tool_call_id

```python
tool_call_id: str | None = None

```

Incremental change to the tool call ID.
