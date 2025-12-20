### Tool

Bases: `Generic[ToolAgentDepsT]`

A tool function for an agent.

Source code in `pydantic_ai_slim/pydantic_ai/tools.py`

````python
@dataclass(init=False)
class Tool(Generic[ToolAgentDepsT]):
    """A tool function for an agent."""

    function: ToolFuncEither[ToolAgentDepsT]
    takes_ctx: bool
    max_retries: int | None
    name: str
    description: str | None
    prepare: ToolPrepareFunc[ToolAgentDepsT] | None
    docstring_format: DocstringFormat
    require_parameter_descriptions: bool
    strict: bool | None
    sequential: bool
    requires_approval: bool
    metadata: dict[str, Any] | None
    function_schema: _function_schema.FunctionSchema
    """
    The base JSON schema for the tool's parameters.

    This schema may be modified by the `prepare` function or by the Model class prior to including it in an API request.
    """

    def __init__(
        self,
        function: ToolFuncEither[ToolAgentDepsT],
        *,
        takes_ctx: bool | None = None,
        max_retries: int | None = None,
        name: str | None = None,
        description: str | None = None,
        prepare: ToolPrepareFunc[ToolAgentDepsT] | None = None,
        docstring_format: DocstringFormat = 'auto',
        require_parameter_descriptions: bool = False,
        schema_generator: type[GenerateJsonSchema] = GenerateToolJsonSchema,
        strict: bool | None = None,
        sequential: bool = False,
        requires_approval: bool = False,
        metadata: dict[str, Any] | None = None,
        function_schema: _function_schema.FunctionSchema | None = None,
    ):
        """Create a new tool instance.

        Example usage:

        ```python {noqa="I001"}
        from pydantic_ai import Agent, RunContext, Tool

        async def my_tool(ctx: RunContext[int], x: int, y: int) -> str:
            return f'{ctx.deps} {x} {y}'

        agent = Agent('test', tools=[Tool(my_tool)])
        ```

        or with a custom prepare method:

        ```python {noqa="I001"}

        from pydantic_ai import Agent, RunContext, Tool
        from pydantic_ai.tools import ToolDefinition

        async def my_tool(ctx: RunContext[int], x: int, y: int) -> str:
            return f'{ctx.deps} {x} {y}'

        async def prep_my_tool(
            ctx: RunContext[int], tool_def: ToolDefinition
        ) -> ToolDefinition | None:
            # only register the tool if `deps == 42`
            if ctx.deps == 42:
                return tool_def

        agent = Agent('test', tools=[Tool(my_tool, prepare=prep_my_tool)])
        ```


        Args:
            function: The Python function to call as the tool.
            takes_ctx: Whether the function takes a [`RunContext`][pydantic_ai.tools.RunContext] first argument,
                this is inferred if unset.
            max_retries: Maximum number of retries allowed for this tool, set to the agent default if `None`.
            name: Name of the tool, inferred from the function if `None`.
            description: Description of the tool, inferred from the function if `None`.
            prepare: custom method to prepare the tool definition for each step, return `None` to omit this
                tool from a given step. This is useful if you want to customise a tool at call time,
                or omit it completely from a step. See [`ToolPrepareFunc`][pydantic_ai.tools.ToolPrepareFunc].
            docstring_format: The format of the docstring, see [`DocstringFormat`][pydantic_ai.tools.DocstringFormat].
                Defaults to `'auto'`, such that the format is inferred from the structure of the docstring.
            require_parameter_descriptions: If True, raise an error if a parameter description is missing. Defaults to False.
            schema_generator: The JSON schema generator class to use. Defaults to `GenerateToolJsonSchema`.
            strict: Whether to enforce JSON schema compliance (only affects OpenAI).
                See [`ToolDefinition`][pydantic_ai.tools.ToolDefinition] for more info.
            sequential: Whether the function requires a sequential/serial execution environment. Defaults to False.
            requires_approval: Whether this tool requires human-in-the-loop approval. Defaults to False.
                See the [tools documentation](../deferred-tools.md#human-in-the-loop-tool-approval) for more info.
            metadata: Optional metadata for the tool. This is not sent to the model but can be used for filtering and tool behavior customization.
            function_schema: The function schema to use for the tool. If not provided, it will be generated.
        """
        self.function = function
        self.function_schema = function_schema or _function_schema.function_schema(
            function,
            schema_generator,
            takes_ctx=takes_ctx,
            docstring_format=docstring_format,
            require_parameter_descriptions=require_parameter_descriptions,
        )
        self.takes_ctx = self.function_schema.takes_ctx
        self.max_retries = max_retries
        self.name = name or function.__name__
        self.description = description or self.function_schema.description
        self.prepare = prepare
        self.docstring_format = docstring_format
        self.require_parameter_descriptions = require_parameter_descriptions
        self.strict = strict
        self.sequential = sequential
        self.requires_approval = requires_approval
        self.metadata = metadata

    @classmethod
    def from_schema(
        cls,
        function: Callable[..., Any],
        name: str,
        description: str | None,
        json_schema: JsonSchemaValue,
        takes_ctx: bool = False,
        sequential: bool = False,
    ) -> Self:
        """Creates a Pydantic tool from a function and a JSON schema.

        Args:
            function: The function to call.
                This will be called with keywords only, and no validation of
                the arguments will be performed.
            name: The unique name of the tool that clearly communicates its purpose
            description: Used to tell the model how/when/why to use the tool.
                You can provide few-shot examples as a part of the description.
            json_schema: The schema for the function arguments
            takes_ctx: An optional boolean parameter indicating whether the function
                accepts the context object as an argument.
            sequential: Whether the function requires a sequential/serial execution environment. Defaults to False.

        Returns:
            A Pydantic tool that calls the function
        """
        function_schema = _function_schema.FunctionSchema(
            function=function,
            description=description,
            validator=SchemaValidator(schema=core_schema.any_schema()),
            json_schema=json_schema,
            takes_ctx=takes_ctx,
            is_async=_utils.is_async_callable(function),
        )

        return cls(
            function,
            takes_ctx=takes_ctx,
            name=name,
            description=description,
            function_schema=function_schema,
            sequential=sequential,
        )

    @property
    def tool_def(self):
        return ToolDefinition(
            name=self.name,
            description=self.description,
            parameters_json_schema=self.function_schema.json_schema,
            strict=self.strict,
            sequential=self.sequential,
            metadata=self.metadata,
            kind='unapproved' if self.requires_approval else 'function',
        )

    async def prepare_tool_def(self, ctx: RunContext[ToolAgentDepsT]) -> ToolDefinition | None:
        """Get the tool definition.

        By default, this method creates a tool definition, then either returns it, or calls `self.prepare`
        if it's set.

        Returns:
            return a `ToolDefinition` or `None` if the tools should not be registered for this run.
        """
        base_tool_def = self.tool_def

        if self.prepare is not None:
            return await self.prepare(ctx, base_tool_def)
        else:
            return base_tool_def

````

#### **init**

```python
__init__(
    function: ToolFuncEither[ToolAgentDepsT],
    *,
    takes_ctx: bool | None = None,
    max_retries: int | None = None,
    name: str | None = None,
    description: str | None = None,
    prepare: ToolPrepareFunc[ToolAgentDepsT] | None = None,
    docstring_format: DocstringFormat = "auto",
    require_parameter_descriptions: bool = False,
    schema_generator: type[
        GenerateJsonSchema
    ] = GenerateToolJsonSchema,
    strict: bool | None = None,
    sequential: bool = False,
    requires_approval: bool = False,
    metadata: dict[str, Any] | None = None,
    function_schema: FunctionSchema | None = None
)

```

Create a new tool instance.

Example usage:

```python
from pydantic_ai import Agent, RunContext, Tool

async def my_tool(ctx: RunContext[int], x: int, y: int) -> str:
    return f'{ctx.deps} {x} {y}'

agent = Agent('test', tools=[Tool(my_tool)])

```

or with a custom prepare method:

```python
from pydantic_ai import Agent, RunContext, Tool
from pydantic_ai.tools import ToolDefinition

async def my_tool(ctx: RunContext[int], x: int, y: int) -> str:
    return f'{ctx.deps} {x} {y}'

async def prep_my_tool(
    ctx: RunContext[int], tool_def: ToolDefinition
) -> ToolDefinition | None:
    # only register the tool if `deps == 42`
    if ctx.deps == 42:
        return tool_def

agent = Agent('test', tools=[Tool(my_tool, prepare=prep_my_tool)])

```

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `function` | `ToolFuncEither[ToolAgentDepsT]` | The Python function to call as the tool. | _required_ | | `takes_ctx` | `bool | None` | Whether the function takes a RunContext first argument, this is inferred if unset. | `None` | | `max_retries` | `int | None` | Maximum number of retries allowed for this tool, set to the agent default if None. | `None` | | `name` | `str | None` | Name of the tool, inferred from the function if None. | `None` | | `description` | `str | None` | Description of the tool, inferred from the function if None. | `None` | | `prepare` | `ToolPrepareFunc[ToolAgentDepsT] | None` | custom method to prepare the tool definition for each step, return None to omit this tool from a given step. This is useful if you want to customise a tool at call time, or omit it completely from a step. See ToolPrepareFunc. | `None` | | `docstring_format` | `DocstringFormat` | The format of the docstring, see DocstringFormat. Defaults to 'auto', such that the format is inferred from the structure of the docstring. | `'auto'` | | `require_parameter_descriptions` | `bool` | If True, raise an error if a parameter description is missing. Defaults to False. | `False` | | `schema_generator` | `type[GenerateJsonSchema]` | The JSON schema generator class to use. Defaults to GenerateToolJsonSchema. | `GenerateToolJsonSchema` | | `strict` | `bool | None` | Whether to enforce JSON schema compliance (only affects OpenAI). See ToolDefinition for more info. | `None` | | `sequential` | `bool` | Whether the function requires a sequential/serial execution environment. Defaults to False. | `False` | | `requires_approval` | `bool` | Whether this tool requires human-in-the-loop approval. Defaults to False. See the tools documentation for more info. | `False` | | `metadata` | `dict[str, Any] | None` | Optional metadata for the tool. This is not sent to the model but can be used for filtering and tool behavior customization. | `None` | | `function_schema` | `FunctionSchema | None` | The function schema to use for the tool. If not provided, it will be generated. | `None` |

Source code in `pydantic_ai_slim/pydantic_ai/tools.py`

````python
def __init__(
    self,
    function: ToolFuncEither[ToolAgentDepsT],
    *,
    takes_ctx: bool | None = None,
    max_retries: int | None = None,
    name: str | None = None,
    description: str | None = None,
    prepare: ToolPrepareFunc[ToolAgentDepsT] | None = None,
    docstring_format: DocstringFormat = 'auto',
    require_parameter_descriptions: bool = False,
    schema_generator: type[GenerateJsonSchema] = GenerateToolJsonSchema,
    strict: bool | None = None,
    sequential: bool = False,
    requires_approval: bool = False,
    metadata: dict[str, Any] | None = None,
    function_schema: _function_schema.FunctionSchema | None = None,
):
    """Create a new tool instance.

    Example usage:

    ```python {noqa="I001"}
    from pydantic_ai import Agent, RunContext, Tool

    async def my_tool(ctx: RunContext[int], x: int, y: int) -> str:
        return f'{ctx.deps} {x} {y}'

    agent = Agent('test', tools=[Tool(my_tool)])
    ```

    or with a custom prepare method:

    ```python {noqa="I001"}

    from pydantic_ai import Agent, RunContext, Tool
    from pydantic_ai.tools import ToolDefinition

    async def my_tool(ctx: RunContext[int], x: int, y: int) -> str:
        return f'{ctx.deps} {x} {y}'

    async def prep_my_tool(
        ctx: RunContext[int], tool_def: ToolDefinition
    ) -> ToolDefinition | None:
        # only register the tool if `deps == 42`
        if ctx.deps == 42:
            return tool_def

    agent = Agent('test', tools=[Tool(my_tool, prepare=prep_my_tool)])
    ```


    Args:
        function: The Python function to call as the tool.
        takes_ctx: Whether the function takes a [`RunContext`][pydantic_ai.tools.RunContext] first argument,
            this is inferred if unset.
        max_retries: Maximum number of retries allowed for this tool, set to the agent default if `None`.
        name: Name of the tool, inferred from the function if `None`.
        description: Description of the tool, inferred from the function if `None`.
        prepare: custom method to prepare the tool definition for each step, return `None` to omit this
            tool from a given step. This is useful if you want to customise a tool at call time,
            or omit it completely from a step. See [`ToolPrepareFunc`][pydantic_ai.tools.ToolPrepareFunc].
        docstring_format: The format of the docstring, see [`DocstringFormat`][pydantic_ai.tools.DocstringFormat].
            Defaults to `'auto'`, such that the format is inferred from the structure of the docstring.
        require_parameter_descriptions: If True, raise an error if a parameter description is missing. Defaults to False.
        schema_generator: The JSON schema generator class to use. Defaults to `GenerateToolJsonSchema`.
        strict: Whether to enforce JSON schema compliance (only affects OpenAI).
            See [`ToolDefinition`][pydantic_ai.tools.ToolDefinition] for more info.
        sequential: Whether the function requires a sequential/serial execution environment. Defaults to False.
        requires_approval: Whether this tool requires human-in-the-loop approval. Defaults to False.
            See the [tools documentation](../deferred-tools.md#human-in-the-loop-tool-approval) for more info.
        metadata: Optional metadata for the tool. This is not sent to the model but can be used for filtering and tool behavior customization.
        function_schema: The function schema to use for the tool. If not provided, it will be generated.
    """
    self.function = function
    self.function_schema = function_schema or _function_schema.function_schema(
        function,
        schema_generator,
        takes_ctx=takes_ctx,
        docstring_format=docstring_format,
        require_parameter_descriptions=require_parameter_descriptions,
    )
    self.takes_ctx = self.function_schema.takes_ctx
    self.max_retries = max_retries
    self.name = name or function.__name__
    self.description = description or self.function_schema.description
    self.prepare = prepare
    self.docstring_format = docstring_format
    self.require_parameter_descriptions = require_parameter_descriptions
    self.strict = strict
    self.sequential = sequential
    self.requires_approval = requires_approval
    self.metadata = metadata

````

#### function_schema

```python
function_schema: FunctionSchema = (
    function_schema
    or function_schema(
        function,
        schema_generator,
        takes_ctx=takes_ctx,
        docstring_format=docstring_format,
        require_parameter_descriptions=require_parameter_descriptions,
    )
)

```

The base JSON schema for the tool's parameters.

This schema may be modified by the `prepare` function or by the Model class prior to including it in an API request.

#### from_schema

```python
from_schema(
    function: Callable[..., Any],
    name: str,
    description: str | None,
    json_schema: JsonSchemaValue,
    takes_ctx: bool = False,
    sequential: bool = False,
) -> Self

```

Creates a Pydantic tool from a function and a JSON schema.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `function` | `Callable[..., Any]` | The function to call. This will be called with keywords only, and no validation of the arguments will be performed. | _required_ | | `name` | `str` | The unique name of the tool that clearly communicates its purpose | _required_ | | `description` | `str | None` | Used to tell the model how/when/why to use the tool. You can provide few-shot examples as a part of the description. | _required_ | | `json_schema` | `JsonSchemaValue` | The schema for the function arguments | _required_ | | `takes_ctx` | `bool` | An optional boolean parameter indicating whether the function accepts the context object as an argument. | `False` | | `sequential` | `bool` | Whether the function requires a sequential/serial execution environment. Defaults to False. | `False` |

Returns:

| Type | Description | | --- | --- | | `Self` | A Pydantic tool that calls the function |

Source code in `pydantic_ai_slim/pydantic_ai/tools.py`

```python
@classmethod
def from_schema(
    cls,
    function: Callable[..., Any],
    name: str,
    description: str | None,
    json_schema: JsonSchemaValue,
    takes_ctx: bool = False,
    sequential: bool = False,
) -> Self:
    """Creates a Pydantic tool from a function and a JSON schema.

    Args:
        function: The function to call.
            This will be called with keywords only, and no validation of
            the arguments will be performed.
        name: The unique name of the tool that clearly communicates its purpose
        description: Used to tell the model how/when/why to use the tool.
            You can provide few-shot examples as a part of the description.
        json_schema: The schema for the function arguments
        takes_ctx: An optional boolean parameter indicating whether the function
            accepts the context object as an argument.
        sequential: Whether the function requires a sequential/serial execution environment. Defaults to False.

    Returns:
        A Pydantic tool that calls the function
    """
    function_schema = _function_schema.FunctionSchema(
        function=function,
        description=description,
        validator=SchemaValidator(schema=core_schema.any_schema()),
        json_schema=json_schema,
        takes_ctx=takes_ctx,
        is_async=_utils.is_async_callable(function),
    )

    return cls(
        function,
        takes_ctx=takes_ctx,
        name=name,
        description=description,
        function_schema=function_schema,
        sequential=sequential,
    )

```

#### prepare_tool_def

```python
prepare_tool_def(
    ctx: RunContext[ToolAgentDepsT],
) -> ToolDefinition | None

```

Get the tool definition.

By default, this method creates a tool definition, then either returns it, or calls `self.prepare` if it's set.

Returns:

| Type | Description | | --- | --- | | `ToolDefinition | None` | return a ToolDefinition or None if the tools should not be registered for this run. |

Source code in `pydantic_ai_slim/pydantic_ai/tools.py`

```python
async def prepare_tool_def(self, ctx: RunContext[ToolAgentDepsT]) -> ToolDefinition | None:
    """Get the tool definition.

    By default, this method creates a tool definition, then either returns it, or calls `self.prepare`
    if it's set.

    Returns:
        return a `ToolDefinition` or `None` if the tools should not be registered for this run.
    """
    base_tool_def = self.tool_def

    if self.prepare is not None:
        return await self.prepare(ctx, base_tool_def)
    else:
        return base_tool_def

```
