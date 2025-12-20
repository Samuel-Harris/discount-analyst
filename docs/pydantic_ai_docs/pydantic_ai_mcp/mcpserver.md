### MCPServer

Bases: `AbstractToolset[Any]`, `ABC`

Base class for attaching agents to MCP servers.

See <https://modelcontextprotocol.io> for more information.

Source code in `pydantic_ai_slim/pydantic_ai/mcp.py`

```python
class MCPServer(AbstractToolset[Any], ABC):
    """Base class for attaching agents to MCP servers.

    See <https://modelcontextprotocol.io> for more information.
    """

    tool_prefix: str | None
    """A prefix to add to all tools that are registered with the server.

    If not empty, will include a trailing underscore(`_`).

    e.g. if `tool_prefix='foo'`, then a tool named `bar` will be registered as `foo_bar`
    """

    log_level: mcp_types.LoggingLevel | None
    """The log level to set when connecting to the server, if any.

    See <https://modelcontextprotocol.io/specification/2025-03-26/server/utilities/logging#logging> for more details.

    If `None`, no log level will be set.
    """

    log_handler: LoggingFnT | None
    """A handler for logging messages from the server."""

    timeout: float
    """The timeout in seconds to wait for the client to initialize."""

    read_timeout: float
    """Maximum time in seconds to wait for new messages before timing out.

    This timeout applies to the long-lived connection after it's established.
    If no new messages are received within this time, the connection will be considered stale
    and may be closed. Defaults to 5 minutes (300 seconds).
    """

    process_tool_call: ProcessToolCallback | None
    """Hook to customize tool calling and optionally pass extra metadata."""

    allow_sampling: bool
    """Whether to allow MCP sampling through this client."""

    sampling_model: models.Model | None
    """The model to use for sampling."""

    max_retries: int
    """The maximum number of times to retry a tool call."""

    elicitation_callback: ElicitationFnT | None = None
    """Callback function to handle elicitation requests from the server."""

    cache_tools: bool
    """Whether to cache the list of tools.

    When enabled (default), tools are fetched once and cached until either:
    - The server sends a `notifications/tools/list_changed` notification
    - The connection is closed

    Set to `False` for servers that change tools dynamically without sending notifications.
    """

    cache_resources: bool
    """Whether to cache the list of resources.

    When enabled (default), resources are fetched once and cached until either:
    - The server sends a `notifications/resources/list_changed` notification
    - The connection is closed

    Set to `False` for servers that change resources dynamically without sending notifications.
    """

    _id: str | None

    _enter_lock: Lock = field(compare=False)
    _running_count: int
    _exit_stack: AsyncExitStack | None

    _client: ClientSession
    _read_stream: MemoryObjectReceiveStream[SessionMessage | Exception]
    _write_stream: MemoryObjectSendStream[SessionMessage]
    _server_info: mcp_types.Implementation
    _server_capabilities: ServerCapabilities
    _instructions: str | None

    _cached_tools: list[mcp_types.Tool] | None
    _cached_resources: list[Resource] | None

    def __init__(
        self,
        tool_prefix: str | None = None,
        log_level: mcp_types.LoggingLevel | None = None,
        log_handler: LoggingFnT | None = None,
        timeout: float = 5,
        read_timeout: float = 5 * 60,
        process_tool_call: ProcessToolCallback | None = None,
        allow_sampling: bool = True,
        sampling_model: models.Model | None = None,
        max_retries: int = 1,
        elicitation_callback: ElicitationFnT | None = None,
        cache_tools: bool = True,
        cache_resources: bool = True,
        *,
        id: str | None = None,
    ):
        self.tool_prefix = tool_prefix
        self.log_level = log_level
        self.log_handler = log_handler
        self.timeout = timeout
        self.read_timeout = read_timeout
        self.process_tool_call = process_tool_call
        self.allow_sampling = allow_sampling
        self.sampling_model = sampling_model
        self.max_retries = max_retries
        self.elicitation_callback = elicitation_callback
        self.cache_tools = cache_tools
        self.cache_resources = cache_resources

        self._id = id or tool_prefix

        self.__post_init__()

    def __post_init__(self):
        self._enter_lock = Lock()
        self._running_count = 0
        self._exit_stack = None
        self._cached_tools = None
        self._cached_resources = None

    @abstractmethod
    @asynccontextmanager
    async def client_streams(
        self,
    ) -> AsyncIterator[
        tuple[
            MemoryObjectReceiveStream[SessionMessage | Exception],
            MemoryObjectSendStream[SessionMessage],
        ]
    ]:
        """Create the streams for the MCP server."""
        raise NotImplementedError('MCP Server subclasses must implement this method.')
        yield

    @property
    def id(self) -> str | None:
        return self._id

    @id.setter
    def id(self, value: str | None):
        self._id = value

    @property
    def label(self) -> str:
        if self.id:
            return super().label  # pragma: no cover
        else:
            return repr(self)

    @property
    def tool_name_conflict_hint(self) -> str:
        return 'Set the `tool_prefix` attribute to avoid name conflicts.'

    @property
    def server_info(self) -> mcp_types.Implementation:
        """Access the information send by the MCP server during initialization."""
        if getattr(self, '_server_info', None) is None:
            raise AttributeError(
                f'The `{self.__class__.__name__}.server_info` is only instantiated after initialization.'
            )
        return self._server_info

    @property
    def capabilities(self) -> ServerCapabilities:
        """Access the capabilities advertised by the MCP server during initialization."""
        if getattr(self, '_server_capabilities', None) is None:
            raise AttributeError(
                f'The `{self.__class__.__name__}.capabilities` is only instantiated after initialization.'
            )
        return self._server_capabilities

    @property
    def instructions(self) -> str | None:
        """Access the instructions sent by the MCP server during initialization."""
        if not hasattr(self, '_instructions'):
            raise AttributeError(
                f'The `{self.__class__.__name__}.instructions` is only available after initialization.'
            )
        return self._instructions

    async def list_tools(self) -> list[mcp_types.Tool]:
        """Retrieve tools that are currently active on the server.

        Tools are cached by default, with cache invalidation on:
        - `notifications/tools/list_changed` notifications from the server
        - Connection close (cache is cleared in `__aexit__`)

        Set `cache_tools=False` for servers that change tools without sending notifications.
        """
        async with self:
            if self.cache_tools:
                if self._cached_tools is not None:
                    return self._cached_tools
                result = await self._client.list_tools()
                self._cached_tools = result.tools
                return result.tools
            else:
                result = await self._client.list_tools()
                return result.tools

    async def direct_call_tool(
        self,
        name: str,
        args: dict[str, Any],
        metadata: dict[str, Any] | None = None,
    ) -> ToolResult:
        """Call a tool on the server.

        Args:
            name: The name of the tool to call.
            args: The arguments to pass to the tool.
            metadata: Request-level metadata (optional)

        Returns:
            The result of the tool call.

        Raises:
            ModelRetry: If the tool call fails.
        """
        async with self:  # Ensure server is running
            try:
                result = await self._client.send_request(
                    mcp_types.ClientRequest(
                        mcp_types.CallToolRequest(
                            method='tools/call',
                            params=mcp_types.CallToolRequestParams(
                                name=name,
                                arguments=args,
                                _meta=mcp_types.RequestParams.Meta(**metadata) if metadata else None,
                            ),
                        )
                    ),
                    mcp_types.CallToolResult,
                )
            except mcp_exceptions.McpError as e:
                raise exceptions.ModelRetry(e.error.message)

        if result.isError:
            message: str | None = None
            if result.content:  # pragma: no branch
                text_parts = [part.text for part in result.content if isinstance(part, mcp_types.TextContent)]
                message = '\n'.join(text_parts)

            raise exceptions.ModelRetry(message or 'MCP tool call failed')

        # Prefer structured content if there are only text parts, which per the docs would contain the JSON-encoded structured content for backward compatibility.
        # See https://github.com/modelcontextprotocol/python-sdk#structured-output
        if (structured := result.structuredContent) and not any(
            not isinstance(part, mcp_types.TextContent) for part in result.content
        ):
            # The MCP SDK wraps primitives and generic types like list in a `result` key, but we want to use the raw value returned by the tool function.
            # See https://github.com/modelcontextprotocol/python-sdk#structured-output
            if isinstance(structured, dict) and len(structured) == 1 and 'result' in structured:
                return structured['result']
            return structured

        mapped = [await self._map_tool_result_part(part) for part in result.content]
        return mapped[0] if len(mapped) == 1 else mapped

    async def call_tool(
        self,
        name: str,
        tool_args: dict[str, Any],
        ctx: RunContext[Any],
        tool: ToolsetTool[Any],
    ) -> ToolResult:
        if self.tool_prefix:
            name = name.removeprefix(f'{self.tool_prefix}_')
            ctx = replace(ctx, tool_name=name)

        if self.process_tool_call is not None:
            return await self.process_tool_call(ctx, self.direct_call_tool, name, tool_args)
        else:
            return await self.direct_call_tool(name, tool_args)

    async def get_tools(self, ctx: RunContext[Any]) -> dict[str, ToolsetTool[Any]]:
        return {
            name: self.tool_for_tool_def(
                ToolDefinition(
                    name=name,
                    description=mcp_tool.description,
                    parameters_json_schema=mcp_tool.inputSchema,
                    metadata={
                        'meta': mcp_tool.meta,
                        'annotations': mcp_tool.annotations.model_dump() if mcp_tool.annotations else None,
                        'output_schema': mcp_tool.outputSchema or None,
                    },
                ),
            )
            for mcp_tool in await self.list_tools()
            if (name := f'{self.tool_prefix}_{mcp_tool.name}' if self.tool_prefix else mcp_tool.name)
        }

    def tool_for_tool_def(self, tool_def: ToolDefinition) -> ToolsetTool[Any]:
        return ToolsetTool(
            toolset=self,
            tool_def=tool_def,
            max_retries=self.max_retries,
            args_validator=TOOL_SCHEMA_VALIDATOR,
        )

    async def list_resources(self) -> list[Resource]:
        """Retrieve resources that are currently present on the server.

        Resources are cached by default, with cache invalidation on:
        - `notifications/resources/list_changed` notifications from the server
        - Connection close (cache is cleared in `__aexit__`)

        Set `cache_resources=False` for servers that change resources without sending notifications.

        Raises:
            MCPError: If the server returns an error.
        """
        async with self:
            if not self.capabilities.resources:
                return []
            try:
                if self.cache_resources:
                    if self._cached_resources is not None:
                        return self._cached_resources
                    result = await self._client.list_resources()
                    resources = [Resource.from_mcp_sdk(r) for r in result.resources]
                    self._cached_resources = resources
                    return resources
                else:
                    result = await self._client.list_resources()
                    return [Resource.from_mcp_sdk(r) for r in result.resources]
            except mcp_exceptions.McpError as e:
                raise MCPError.from_mcp_sdk(e) from e

    async def list_resource_templates(self) -> list[ResourceTemplate]:
        """Retrieve resource templates that are currently present on the server.

        Raises:
            MCPError: If the server returns an error.
        """
        async with self:  # Ensure server is running
            if not self.capabilities.resources:
                return []
            try:
                result = await self._client.list_resource_templates()
            except mcp_exceptions.McpError as e:
                raise MCPError.from_mcp_sdk(e) from e
        return [ResourceTemplate.from_mcp_sdk(t) for t in result.resourceTemplates]

    @overload
    async def read_resource(self, uri: str) -> str | messages.BinaryContent | list[str | messages.BinaryContent]: ...

    @overload
    async def read_resource(
        self, uri: Resource
    ) -> str | messages.BinaryContent | list[str | messages.BinaryContent]: ...

    async def read_resource(
        self, uri: str | Resource
    ) -> str | messages.BinaryContent | list[str | messages.BinaryContent]:
        """Read the contents of a specific resource by URI.

        Args:
            uri: The URI of the resource to read, or a Resource object.

        Returns:
            The resource contents. If the resource has a single content item, returns that item directly.
            If the resource has multiple content items, returns a list of items.

        Raises:
            MCPError: If the server returns an error.
        """
        resource_uri = uri if isinstance(uri, str) else uri.uri
        async with self:  # Ensure server is running
            try:
                result = await self._client.read_resource(AnyUrl(resource_uri))
            except mcp_exceptions.McpError as e:
                raise MCPError.from_mcp_sdk(e) from e

        return (
            self._get_content(result.contents[0])
            if len(result.contents) == 1
            else [self._get_content(resource) for resource in result.contents]
        )

    async def __aenter__(self) -> Self:
        """Enter the MCP server context.

        This will initialize the connection to the server.
        If this server is an [`MCPServerStdio`][pydantic_ai.mcp.MCPServerStdio], the server will first be started as a subprocess.

        This is a no-op if the MCP server has already been entered.
        """
        async with self._enter_lock:
            if self._running_count == 0:
                async with AsyncExitStack() as exit_stack:
                    self._read_stream, self._write_stream = await exit_stack.enter_async_context(self.client_streams())
                    client = ClientSession(
                        read_stream=self._read_stream,
                        write_stream=self._write_stream,
                        sampling_callback=self._sampling_callback if self.allow_sampling else None,
                        elicitation_callback=self.elicitation_callback,
                        logging_callback=self.log_handler,
                        read_timeout_seconds=timedelta(seconds=self.read_timeout),
                        message_handler=self._handle_notification,
                    )
                    self._client = await exit_stack.enter_async_context(client)

                    with anyio.fail_after(self.timeout):
                        result = await self._client.initialize()
                        self._server_info = result.serverInfo
                        self._server_capabilities = ServerCapabilities.from_mcp_sdk(result.capabilities)
                        self._instructions = result.instructions
                        if log_level := self.log_level:
                            await self._client.set_logging_level(log_level)

                    self._exit_stack = exit_stack.pop_all()
            self._running_count += 1
        return self

    async def __aexit__(self, *args: Any) -> bool | None:
        if self._running_count == 0:
            raise ValueError('MCPServer.__aexit__ called more times than __aenter__')
        async with self._enter_lock:
            self._running_count -= 1
            if self._running_count == 0 and self._exit_stack is not None:
                await self._exit_stack.aclose()
                self._exit_stack = None
                self._cached_tools = None
                self._cached_resources = None

    @property
    def is_running(self) -> bool:
        """Check if the MCP server is running."""
        return bool(self._running_count)

    async def _sampling_callback(
        self, context: RequestContext[ClientSession, Any], params: mcp_types.CreateMessageRequestParams
    ) -> mcp_types.CreateMessageResult | mcp_types.ErrorData:
        """MCP sampling callback."""
        if self.sampling_model is None:
            raise ValueError('Sampling model is not set')  # pragma: no cover

        pai_messages = _mcp.map_from_mcp_params(params)
        model_settings = models.ModelSettings()
        if max_tokens := params.maxTokens:  # pragma: no branch
            model_settings['max_tokens'] = max_tokens
        if temperature := params.temperature:  # pragma: no branch
            model_settings['temperature'] = temperature
        if stop_sequences := params.stopSequences:  # pragma: no branch
            model_settings['stop_sequences'] = stop_sequences

        model_response = await model_request(self.sampling_model, pai_messages, model_settings=model_settings)
        return mcp_types.CreateMessageResult(
            role='assistant',
            content=_mcp.map_from_model_response(model_response),
            model=self.sampling_model.model_name,
        )

    async def _handle_notification(
        self,
        message: RequestResponder[mcp_types.ServerRequest, mcp_types.ClientResult]
        | mcp_types.ServerNotification
        | Exception,
    ) -> None:
        """Handle notifications from the MCP server, invalidating caches as needed."""
        if isinstance(message, mcp_types.ServerNotification):  # pragma: no branch
            if isinstance(message.root, mcp_types.ToolListChangedNotification):
                self._cached_tools = None
            elif isinstance(message.root, mcp_types.ResourceListChangedNotification):
                self._cached_resources = None

    async def _map_tool_result_part(
        self, part: mcp_types.ContentBlock
    ) -> str | messages.BinaryContent | dict[str, Any] | list[Any]:
        # See https://github.com/jlowin/fastmcp/blob/main/docs/servers/tools.mdx#return-values

        if isinstance(part, mcp_types.TextContent):
            text = part.text
            if text.startswith(('[', '{')):
                try:
                    return pydantic_core.from_json(text)
                except ValueError:
                    pass
            return text
        elif isinstance(part, mcp_types.ImageContent):
            return messages.BinaryContent(data=base64.b64decode(part.data), media_type=part.mimeType)
        elif isinstance(part, mcp_types.AudioContent):
            # NOTE: The FastMCP server doesn't support audio content.
            # See <https://github.com/modelcontextprotocol/python-sdk/issues/952> for more details.
            return messages.BinaryContent(
                data=base64.b64decode(part.data), media_type=part.mimeType
            )  # pragma: no cover
        elif isinstance(part, mcp_types.EmbeddedResource):
            resource = part.resource
            return self._get_content(resource)
        elif isinstance(part, mcp_types.ResourceLink):
            return await self.read_resource(str(part.uri))
        else:
            assert_never(part)

    def _get_content(
        self, resource: mcp_types.TextResourceContents | mcp_types.BlobResourceContents
    ) -> str | messages.BinaryContent:
        if isinstance(resource, mcp_types.TextResourceContents):
            return resource.text
        elif isinstance(resource, mcp_types.BlobResourceContents):
            return messages.BinaryContent(
                data=base64.b64decode(resource.blob), media_type=resource.mimeType or 'application/octet-stream'
            )
        else:
            assert_never(resource)

    def __eq__(self, value: object, /) -> bool:
        return isinstance(value, MCPServer) and self.id == value.id and self.tool_prefix == value.tool_prefix

```

#### tool_prefix

```python
tool_prefix: str | None = tool_prefix

```

A prefix to add to all tools that are registered with the server.

If not empty, will include a trailing underscore(`_`).

e.g. if `tool_prefix='foo'`, then a tool named `bar` will be registered as `foo_bar`

#### log_level

```python
log_level: LoggingLevel | None = log_level

```

The log level to set when connecting to the server, if any.

See <https://modelcontextprotocol.io/specification/2025-03-26/server/utilities/logging#logging> for more details.

If `None`, no log level will be set.

#### log_handler

```python
log_handler: LoggingFnT | None = log_handler

```

A handler for logging messages from the server.

#### timeout

```python
timeout: float = timeout

```

The timeout in seconds to wait for the client to initialize.

#### read_timeout

```python
read_timeout: float = read_timeout

```

Maximum time in seconds to wait for new messages before timing out.

This timeout applies to the long-lived connection after it's established. If no new messages are received within this time, the connection will be considered stale and may be closed. Defaults to 5 minutes (300 seconds).

#### process_tool_call

```python
process_tool_call: ProcessToolCallback | None = (
    process_tool_call
)

```

Hook to customize tool calling and optionally pass extra metadata.

#### allow_sampling

```python
allow_sampling: bool = allow_sampling

```

Whether to allow MCP sampling through this client.

#### sampling_model

```python
sampling_model: Model | None = sampling_model

```

The model to use for sampling.

#### max_retries

```python
max_retries: int = max_retries

```

The maximum number of times to retry a tool call.

#### elicitation_callback

```python
elicitation_callback: ElicitationFnT | None = (
    elicitation_callback
)

```

Callback function to handle elicitation requests from the server.

#### cache_tools

```python
cache_tools: bool = cache_tools

```

Whether to cache the list of tools.

When enabled (default), tools are fetched once and cached until either:

- The server sends a `notifications/tools/list_changed` notification
- The connection is closed

Set to `False` for servers that change tools dynamically without sending notifications.

#### cache_resources

```python
cache_resources: bool = cache_resources

```

Whether to cache the list of resources.

When enabled (default), resources are fetched once and cached until either:

- The server sends a `notifications/resources/list_changed` notification
- The connection is closed

Set to `False` for servers that change resources dynamically without sending notifications.

#### client_streams

```python
client_streams() -> AsyncIterator[
    tuple[
        MemoryObjectReceiveStream[
            SessionMessage | Exception
        ],
        MemoryObjectSendStream[SessionMessage],
    ]
]

```

Create the streams for the MCP server.

Source code in `pydantic_ai_slim/pydantic_ai/mcp.py`

```python
@abstractmethod
@asynccontextmanager
async def client_streams(
    self,
) -> AsyncIterator[
    tuple[
        MemoryObjectReceiveStream[SessionMessage | Exception],
        MemoryObjectSendStream[SessionMessage],
    ]
]:
    """Create the streams for the MCP server."""
    raise NotImplementedError('MCP Server subclasses must implement this method.')
    yield

```

#### server_info

```python
server_info: Implementation

```

Access the information send by the MCP server during initialization.

#### capabilities

```python
capabilities: ServerCapabilities

```

Access the capabilities advertised by the MCP server during initialization.

#### instructions

```python
instructions: str | None

```

Access the instructions sent by the MCP server during initialization.

#### list_tools

```python
list_tools() -> list[Tool]

```

Retrieve tools that are currently active on the server.

Tools are cached by default, with cache invalidation on:

- `notifications/tools/list_changed` notifications from the server
- Connection close (cache is cleared in `__aexit__`)

Set `cache_tools=False` for servers that change tools without sending notifications.

Source code in `pydantic_ai_slim/pydantic_ai/mcp.py`

```python
async def list_tools(self) -> list[mcp_types.Tool]:
    """Retrieve tools that are currently active on the server.

    Tools are cached by default, with cache invalidation on:
    - `notifications/tools/list_changed` notifications from the server
    - Connection close (cache is cleared in `__aexit__`)

    Set `cache_tools=False` for servers that change tools without sending notifications.
    """
    async with self:
        if self.cache_tools:
            if self._cached_tools is not None:
                return self._cached_tools
            result = await self._client.list_tools()
            self._cached_tools = result.tools
            return result.tools
        else:
            result = await self._client.list_tools()
            return result.tools

```

#### direct_call_tool

```python
direct_call_tool(
    name: str,
    args: dict[str, Any],
    metadata: dict[str, Any] | None = None,
) -> ToolResult

```

Call a tool on the server.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `name` | `str` | The name of the tool to call. | _required_ | | `args` | `dict[str, Any]` | The arguments to pass to the tool. | _required_ | | `metadata` | `dict[str, Any] | None` | Request-level metadata (optional) | `None` |

Returns:

| Type | Description | | --- | --- | | `ToolResult` | The result of the tool call. |

Raises:

| Type | Description | | --- | --- | | `ModelRetry` | If the tool call fails. |

Source code in `pydantic_ai_slim/pydantic_ai/mcp.py`

```python
async def direct_call_tool(
    self,
    name: str,
    args: dict[str, Any],
    metadata: dict[str, Any] | None = None,
) -> ToolResult:
    """Call a tool on the server.

    Args:
        name: The name of the tool to call.
        args: The arguments to pass to the tool.
        metadata: Request-level metadata (optional)

    Returns:
        The result of the tool call.

    Raises:
        ModelRetry: If the tool call fails.
    """
    async with self:  # Ensure server is running
        try:
            result = await self._client.send_request(
                mcp_types.ClientRequest(
                    mcp_types.CallToolRequest(
                        method='tools/call',
                        params=mcp_types.CallToolRequestParams(
                            name=name,
                            arguments=args,
                            _meta=mcp_types.RequestParams.Meta(**metadata) if metadata else None,
                        ),
                    )
                ),
                mcp_types.CallToolResult,
            )
        except mcp_exceptions.McpError as e:
            raise exceptions.ModelRetry(e.error.message)

    if result.isError:
        message: str | None = None
        if result.content:  # pragma: no branch
            text_parts = [part.text for part in result.content if isinstance(part, mcp_types.TextContent)]
            message = '\n'.join(text_parts)

        raise exceptions.ModelRetry(message or 'MCP tool call failed')

    # Prefer structured content if there are only text parts, which per the docs would contain the JSON-encoded structured content for backward compatibility.
    # See https://github.com/modelcontextprotocol/python-sdk#structured-output
    if (structured := result.structuredContent) and not any(
        not isinstance(part, mcp_types.TextContent) for part in result.content
    ):
        # The MCP SDK wraps primitives and generic types like list in a `result` key, but we want to use the raw value returned by the tool function.
        # See https://github.com/modelcontextprotocol/python-sdk#structured-output
        if isinstance(structured, dict) and len(structured) == 1 and 'result' in structured:
            return structured['result']
        return structured

    mapped = [await self._map_tool_result_part(part) for part in result.content]
    return mapped[0] if len(mapped) == 1 else mapped

```

#### list_resources

```python
list_resources() -> list[Resource]

```

Retrieve resources that are currently present on the server.

Resources are cached by default, with cache invalidation on:

- `notifications/resources/list_changed` notifications from the server
- Connection close (cache is cleared in `__aexit__`)

Set `cache_resources=False` for servers that change resources without sending notifications.

Raises:

| Type | Description | | --- | --- | | `MCPError` | If the server returns an error. |

Source code in `pydantic_ai_slim/pydantic_ai/mcp.py`

```python
async def list_resources(self) -> list[Resource]:
    """Retrieve resources that are currently present on the server.

    Resources are cached by default, with cache invalidation on:
    - `notifications/resources/list_changed` notifications from the server
    - Connection close (cache is cleared in `__aexit__`)

    Set `cache_resources=False` for servers that change resources without sending notifications.

    Raises:
        MCPError: If the server returns an error.
    """
    async with self:
        if not self.capabilities.resources:
            return []
        try:
            if self.cache_resources:
                if self._cached_resources is not None:
                    return self._cached_resources
                result = await self._client.list_resources()
                resources = [Resource.from_mcp_sdk(r) for r in result.resources]
                self._cached_resources = resources
                return resources
            else:
                result = await self._client.list_resources()
                return [Resource.from_mcp_sdk(r) for r in result.resources]
        except mcp_exceptions.McpError as e:
            raise MCPError.from_mcp_sdk(e) from e

```

#### list_resource_templates

```python
list_resource_templates() -> list[ResourceTemplate]

```

Retrieve resource templates that are currently present on the server.

Raises:

| Type | Description | | --- | --- | | `MCPError` | If the server returns an error. |

Source code in `pydantic_ai_slim/pydantic_ai/mcp.py`

```python
async def list_resource_templates(self) -> list[ResourceTemplate]:
    """Retrieve resource templates that are currently present on the server.

    Raises:
        MCPError: If the server returns an error.
    """
    async with self:  # Ensure server is running
        if not self.capabilities.resources:
            return []
        try:
            result = await self._client.list_resource_templates()
        except mcp_exceptions.McpError as e:
            raise MCPError.from_mcp_sdk(e) from e
    return [ResourceTemplate.from_mcp_sdk(t) for t in result.resourceTemplates]

```

#### read_resource

```python
read_resource(
    uri: str,
) -> str | BinaryContent | list[str | BinaryContent]

```

```python
read_resource(
    uri: Resource,
) -> str | BinaryContent | list[str | BinaryContent]

```

```python
read_resource(
    uri: str | Resource,
) -> str | BinaryContent | list[str | BinaryContent]

```

Read the contents of a specific resource by URI.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `uri` | `str | Resource` | The URI of the resource to read, or a Resource object. | _required_ |

Returns:

| Type | Description | | --- | --- | | `str | BinaryContent | list[str | BinaryContent]` | The resource contents. If the resource has a single content item, returns that item directly. | | `str | BinaryContent | list[str | BinaryContent]` | If the resource has multiple content items, returns a list of items. |

Raises:

| Type | Description | | --- | --- | | `MCPError` | If the server returns an error. |

Source code in `pydantic_ai_slim/pydantic_ai/mcp.py`

```python
async def read_resource(
    self, uri: str | Resource
) -> str | messages.BinaryContent | list[str | messages.BinaryContent]:
    """Read the contents of a specific resource by URI.

    Args:
        uri: The URI of the resource to read, or a Resource object.

    Returns:
        The resource contents. If the resource has a single content item, returns that item directly.
        If the resource has multiple content items, returns a list of items.

    Raises:
        MCPError: If the server returns an error.
    """
    resource_uri = uri if isinstance(uri, str) else uri.uri
    async with self:  # Ensure server is running
        try:
            result = await self._client.read_resource(AnyUrl(resource_uri))
        except mcp_exceptions.McpError as e:
            raise MCPError.from_mcp_sdk(e) from e

    return (
        self._get_content(result.contents[0])
        if len(result.contents) == 1
        else [self._get_content(resource) for resource in result.contents]
    )

```

#### **aenter**

```python
__aenter__() -> Self

```

Enter the MCP server context.

This will initialize the connection to the server. If this server is an MCPServerStdio, the server will first be started as a subprocess.

This is a no-op if the MCP server has already been entered.

Source code in `pydantic_ai_slim/pydantic_ai/mcp.py`

```python
async def __aenter__(self) -> Self:
    """Enter the MCP server context.

    This will initialize the connection to the server.
    If this server is an [`MCPServerStdio`][pydantic_ai.mcp.MCPServerStdio], the server will first be started as a subprocess.

    This is a no-op if the MCP server has already been entered.
    """
    async with self._enter_lock:
        if self._running_count == 0:
            async with AsyncExitStack() as exit_stack:
                self._read_stream, self._write_stream = await exit_stack.enter_async_context(self.client_streams())
                client = ClientSession(
                    read_stream=self._read_stream,
                    write_stream=self._write_stream,
                    sampling_callback=self._sampling_callback if self.allow_sampling else None,
                    elicitation_callback=self.elicitation_callback,
                    logging_callback=self.log_handler,
                    read_timeout_seconds=timedelta(seconds=self.read_timeout),
                    message_handler=self._handle_notification,
                )
                self._client = await exit_stack.enter_async_context(client)

                with anyio.fail_after(self.timeout):
                    result = await self._client.initialize()
                    self._server_info = result.serverInfo
                    self._server_capabilities = ServerCapabilities.from_mcp_sdk(result.capabilities)
                    self._instructions = result.instructions
                    if log_level := self.log_level:
                        await self._client.set_logging_level(log_level)

                self._exit_stack = exit_stack.pop_all()
        self._running_count += 1
    return self

```

#### is_running

```python
is_running: bool

```

Check if the MCP server is running.
