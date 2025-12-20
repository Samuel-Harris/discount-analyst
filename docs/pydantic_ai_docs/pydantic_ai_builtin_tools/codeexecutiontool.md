### CodeExecutionTool

Bases: `AbstractBuiltinTool`

A builtin tool that allows your agent to execute code.

Supported by:

- Anthropic
- OpenAI Responses
- Google

Source code in `pydantic_ai_slim/pydantic_ai/builtin_tools.py`

```python
@dataclass(kw_only=True)
class CodeExecutionTool(AbstractBuiltinTool):
    """A builtin tool that allows your agent to execute code.

    Supported by:

    * Anthropic
    * OpenAI Responses
    * Google
    """

    kind: str = 'code_execution'
    """The kind of tool."""

```

#### kind

```python
kind: str = 'code_execution'

```

The kind of tool.
