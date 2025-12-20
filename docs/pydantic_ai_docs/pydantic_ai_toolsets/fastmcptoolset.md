### FastMCPToolset

Bases: `AbstractToolset[AgentDepsT]`

A FastMCP Toolset that uses the FastMCP Client to call tools from a local or remote MCP Server.

The Toolset can accept a FastMCP Client, a FastMCP Transport, or any other object which a FastMCP Transport can be created from.

See https://gofastmcp.com/clients/transports for a full list of transports available.

Source code in `pydantic_ai_slim/pydantic_ai/toolsets/fastmcp.py`

```python
@dataclass(init=False)
class FastMCPToolset(AbstractToolset[AgentDepsT]):
    """A FastMCP Toolset that uses the FastMCP Client to call tools from a local or remote MCP Server.

    The Toolset can accept a FastMCP Client, a FastMCP Transport, or any other object which a FastMCP Transport can be created from.

    See https://gofastmcp.com/clients/transports for a full list of transports available.
    """

    client: Client[Any]
    """The FastMCP client to use."""

    _: KW_ONLY

    tool_error_behavior: Literal['model_retry', 'error']
    """The behavior to take when a tool error occurs."""

    max_retries: int
    """The maximum number of retries to attempt if a tool call fails."""

    _id: str | None

    def __init__(
        self,
        client: Client[Any]
        | ClientTransport
        | FastMCP
        | FastMCP1Server
        | AnyUrl
        | Path
        | MCPConfig
        | dict[str, Any]
        | str,
        *,
        max_retries: int = 1,
        tool_error_behavior: Literal['model_retry', 'error'] = 'model_retry',
        id: str | None = None,
    ) -> None:
        if isinstance(client, Client):
            self.client = client
        else:
            self.client = Client[Any](transport=client)

        self._id = id
        self.max_retries = max_retries
        self.tool_error_behavior = tool_error_behavior

        self._enter_lock: Lock = Lock()
        self._running_count: int = 0
        self._exit_stack: AsyncExitStack | None = None

    @property
    def id(self) -> str | None:
        return self._id

    async def __aenter__(self) -> Self:
        async with self._enter_lock:
            if self._running_count == 0:
                self._exit_stack = AsyncExitStack()
                await self._exit_stack.enter_async_context(self.client)

            self._running_count += 1

        return self

    async def __aexit__(self, *args: Any) -> bool | None:
        async with self._enter_lock:
            self._running_count -= 1
            if self._running_count == 0 and self._exit_stack:
                await self._exit_stack.aclose()
                self._exit_stack = None

        return None

    async def get_tools(self, ctx: RunContext[AgentDepsT]) -> dict[str, ToolsetTool[AgentDepsT]]:
        async with self:
            return {
                mcp_tool.name: self.tool_for_tool_def(
                    ToolDefinition(
                        name=mcp_tool.name,
                        description=mcp_tool.description,
                        parameters_json_schema=mcp_tool.inputSchema,
                        metadata={
                            'meta': mcp_tool.meta,
                            'annotations': mcp_tool.annotations.model_dump() if mcp_tool.annotations else None,
                            'output_schema': mcp_tool.outputSchema or None,
                        },
                    )
                )
                for mcp_tool in await self.client.list_tools()
            }

    async def call_tool(
        self, name: str, tool_args: dict[str, Any], ctx: RunContext[AgentDepsT], tool: ToolsetTool[AgentDepsT]
    ) -> Any:
        async with self:
            try:
                call_tool_result: CallToolResult = await self.client.call_tool(name=name, arguments=tool_args)
            except ToolError as e:
                if self.tool_error_behavior == 'model_retry':
                    raise ModelRetry(message=str(e)) from e
                else:
                    raise e

        # If we have structured content, return that
        if call_tool_result.structured_content:
            return call_tool_result.structured_content

        # Otherwise, return the content
        return _map_fastmcp_tool_results(parts=call_tool_result.content)

    def tool_for_tool_def(self, tool_def: ToolDefinition) -> ToolsetTool[AgentDepsT]:
        return ToolsetTool[AgentDepsT](
            tool_def=tool_def,
            toolset=self,
            max_retries=self.max_retries,
            args_validator=TOOL_SCHEMA_VALIDATOR,
        )

```

#### client

```python
client: Client[Any]

```

The FastMCP client to use.

#### max_retries

```python
max_retries: int = max_retries

```

The maximum number of retries to attempt if a tool call fails.

#### tool_error_behavior

```python
tool_error_behavior: Literal["model_retry", "error"] = (
    tool_error_behavior
)

```

The behavior to take when a tool error occurs.
