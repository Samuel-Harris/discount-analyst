### MemoryTool

Bases: `AbstractBuiltinTool`

A builtin tool that allows your agent to use memory.

Supported by:

- Anthropic

Source code in `pydantic_ai_slim/pydantic_ai/builtin_tools.py`

```python
@dataclass(kw_only=True)
class MemoryTool(AbstractBuiltinTool):
    """A builtin tool that allows your agent to use memory.

    Supported by:

    * Anthropic
    """

    kind: str = 'memory'
    """The kind of tool."""

```

#### kind

```python
kind: str = 'memory'

```

The kind of tool.
