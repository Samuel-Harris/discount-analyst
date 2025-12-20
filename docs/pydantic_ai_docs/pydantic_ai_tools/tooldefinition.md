### ToolDefinition

Definition of a tool passed to a model.

This is used for both function tools and output tools.

Source code in `pydantic_ai_slim/pydantic_ai/tools.py`

```python
@dataclass(repr=False, kw_only=True)
class ToolDefinition:
    """Definition of a tool passed to a model.

    This is used for both function tools and output tools.
    """

    name: str
    """The name of the tool."""

    parameters_json_schema: ObjectJsonSchema = field(default_factory=lambda: {'type': 'object', 'properties': {}})
    """The JSON schema for the tool's parameters."""

    description: str | None = None
    """The description of the tool."""

    outer_typed_dict_key: str | None = None
    """The key in the outer [TypedDict] that wraps an output tool.

    This will only be set for output tools which don't have an `object` JSON schema.
    """

    strict: bool | None = None
    """Whether to enforce (vendor-specific) strict JSON schema validation for tool calls.

    Setting this to `True` while using a supported model generally imposes some restrictions on the tool's JSON schema
    in exchange for guaranteeing the API responses strictly match that schema.

    When `False`, the model may be free to generate other properties or types (depending on the vendor).
    When `None` (the default), the value will be inferred based on the compatibility of the parameters_json_schema.

    Note: this is currently supported by OpenAI and Anthropic models.
    """

    sequential: bool = False
    """Whether this tool requires a sequential/serial execution environment."""

    kind: ToolKind = field(default='function')
    """The kind of tool:

    - `'function'`: a tool that will be executed by Pydantic AI during an agent run and has its result returned to the model
    - `'output'`: a tool that passes through an output value that ends the run
    - `'external'`: a tool whose result will be produced outside of the Pydantic AI agent run in which it was called, because it depends on an upstream service (or user) or could take longer to generate than it's reasonable to keep the agent process running.
        See the [tools documentation](../deferred-tools.md#deferred-tools) for more info.
    - `'unapproved'`: a tool that requires human-in-the-loop approval.
        See the [tools documentation](../deferred-tools.md#human-in-the-loop-tool-approval) for more info.
    """

    metadata: dict[str, Any] | None = None
    """Tool metadata that can be set by the toolset this tool came from. It is not sent to the model, but can be used for filtering and tool behavior customization.

    For MCP tools, this contains the `meta`, `annotations`, and `output_schema` fields from the tool definition.
    """

    @property
    def defer(self) -> bool:
        """Whether calls to this tool will be deferred.

        See the [tools documentation](../deferred-tools.md#deferred-tools) for more info.
        """
        return self.kind in ('external', 'unapproved')

    __repr__ = _utils.dataclasses_no_defaults_repr

```

#### name

```python
name: str

```

The name of the tool.

#### parameters_json_schema

```python
parameters_json_schema: ObjectJsonSchema = field(
    default_factory=lambda: {
        "type": "object",
        "properties": {},
    }
)

```

The JSON schema for the tool's parameters.

#### description

```python
description: str | None = None

```

The description of the tool.

#### outer_typed_dict_key

```python
outer_typed_dict_key: str | None = None

```

The key in the outer [TypedDict] that wraps an output tool.

This will only be set for output tools which don't have an `object` JSON schema.

#### strict

```python
strict: bool | None = None

```

Whether to enforce (vendor-specific) strict JSON schema validation for tool calls.

Setting this to `True` while using a supported model generally imposes some restrictions on the tool's JSON schema in exchange for guaranteeing the API responses strictly match that schema.

When `False`, the model may be free to generate other properties or types (depending on the vendor). When `None` (the default), the value will be inferred based on the compatibility of the parameters_json_schema.

Note: this is currently supported by OpenAI and Anthropic models.

#### sequential

```python
sequential: bool = False

```

Whether this tool requires a sequential/serial execution environment.

#### kind

```python
kind: ToolKind = field(default='function')

```

The kind of tool:

- `'function'`: a tool that will be executed by Pydantic AI during an agent run and has its result returned to the model
- `'output'`: a tool that passes through an output value that ends the run
- `'external'`: a tool whose result will be produced outside of the Pydantic AI agent run in which it was called, because it depends on an upstream service (or user) or could take longer to generate than it's reasonable to keep the agent process running. See the [tools documentation](../../deferred-tools/#deferred-tools) for more info.
- `'unapproved'`: a tool that requires human-in-the-loop approval. See the [tools documentation](../../deferred-tools/#human-in-the-loop-tool-approval) for more info.

#### metadata

```python
metadata: dict[str, Any] | None = None

```

Tool metadata that can be set by the toolset this tool came from. It is not sent to the model, but can be used for filtering and tool behavior customization.

For MCP tools, this contains the `meta`, `annotations`, and `output_schema` fields from the tool definition.

#### defer

```python
defer: bool

```

Whether calls to this tool will be deferred.

See the [tools documentation](../../deferred-tools/#deferred-tools) for more info.
