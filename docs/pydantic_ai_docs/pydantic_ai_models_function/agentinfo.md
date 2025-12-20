### AgentInfo

Information about an agent.

This is passed as the second to functions used within FunctionModel.

Source code in `pydantic_ai_slim/pydantic_ai/models/function.py`

```python
@dataclass(frozen=True, kw_only=True)
class AgentInfo:
    """Information about an agent.

    This is passed as the second to functions used within [`FunctionModel`][pydantic_ai.models.function.FunctionModel].
    """

    function_tools: list[ToolDefinition]
    """The function tools available on this agent.

    These are the tools registered via the [`tool`][pydantic_ai.Agent.tool] and
    [`tool_plain`][pydantic_ai.Agent.tool_plain] decorators.
    """
    allow_text_output: bool
    """Whether a plain text output is allowed."""
    output_tools: list[ToolDefinition]
    """The tools that can called to produce the final output of the run."""
    model_settings: ModelSettings | None
    """The model settings passed to the run call."""
    model_request_parameters: ModelRequestParameters
    """The model request parameters passed to the run call."""
    instructions: str | None
    """The instructions passed to model."""

```

#### function_tools

```python
function_tools: list[ToolDefinition]

```

The function tools available on this agent.

These are the tools registered via the tool and tool_plain decorators.

#### allow_text_output

```python
allow_text_output: bool

```

Whether a plain text output is allowed.

#### output_tools

```python
output_tools: list[ToolDefinition]

```

The tools that can called to produce the final output of the run.

#### model_settings

```python
model_settings: ModelSettings | None

```

The model settings passed to the run call.

#### model_request_parameters

```python
model_request_parameters: ModelRequestParameters

```

The model request parameters passed to the run call.

#### instructions

```python
instructions: str | None

```

The instructions passed to model.
