### MCPServerStdio

Bases: `MCPServer`

Runs an MCP server in a subprocess and communicates with it over stdin/stdout.

This class implements the stdio transport from the MCP specification. See <https://spec.modelcontextprotocol.io/specification/2024-11-05/basic/transports/#stdio> for more information.

Note

Using this class as an async context manager will start the server as a subprocess when entering the context, and stop it when exiting the context.

Example:

```python
from pydantic_ai import Agent
from pydantic_ai.mcp import MCPServerStdio

server = MCPServerStdio(  # (1)!
    'uv', args=['run', 'mcp-run-python', 'stdio'], timeout=10
)
agent = Agent('openai:gpt-4o', toolsets=[server])

```

1. See [MCP Run Python](https://github.com/pydantic/mcp-run-python) for more information.

Source code in `pydantic_ai_slim/pydantic_ai/mcp.py`

````python
class MCPServerStdio(MCPServer):
    """Runs an MCP server in a subprocess and communicates with it over stdin/stdout.

    This class implements the stdio transport from the MCP specification.
    See <https://spec.modelcontextprotocol.io/specification/2024-11-05/basic/transports/#stdio> for more information.

    !!! note
        Using this class as an async context manager will start the server as a subprocess when entering the context,
        and stop it when exiting the context.

    Example:
    ```python {py="3.10"}
    from pydantic_ai import Agent
    from pydantic_ai.mcp import MCPServerStdio

    server = MCPServerStdio(  # (1)!
        'uv', args=['run', 'mcp-run-python', 'stdio'], timeout=10
    )
    agent = Agent('openai:gpt-4o', toolsets=[server])
    ```

    1. See [MCP Run Python](https://github.com/pydantic/mcp-run-python) for more information.
    """

    command: str
    """The command to run."""

    args: Sequence[str]
    """The arguments to pass to the command."""

    env: dict[str, str] | None
    """The environment variables the CLI server will have access to.

    By default the subprocess will not inherit any environment variables from the parent process.
    If you want to inherit the environment variables from the parent process, use `env=os.environ`.
    """

    cwd: str | Path | None
    """The working directory to use when spawning the process."""

    # last fields are re-defined from the parent class so they appear as fields
    tool_prefix: str | None
    log_level: mcp_types.LoggingLevel | None
    log_handler: LoggingFnT | None
    timeout: float
    read_timeout: float
    process_tool_call: ProcessToolCallback | None
    allow_sampling: bool
    sampling_model: models.Model | None
    max_retries: int
    elicitation_callback: ElicitationFnT | None = None
    cache_tools: bool
    cache_resources: bool

    def __init__(
        self,
        command: str,
        args: Sequence[str],
        *,
        env: dict[str, str] | None = None,
        cwd: str | Path | None = None,
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
        id: str | None = None,
    ):
        """Build a new MCP server.

        Args:
            command: The command to run.
            args: The arguments to pass to the command.
            env: The environment variables to set in the subprocess.
            cwd: The working directory to use when spawning the process.
            tool_prefix: A prefix to add to all tools that are registered with the server.
            log_level: The log level to set when connecting to the server, if any.
            log_handler: A handler for logging messages from the server.
            timeout: The timeout in seconds to wait for the client to initialize.
            read_timeout: Maximum time in seconds to wait for new messages before timing out.
            process_tool_call: Hook to customize tool calling and optionally pass extra metadata.
            allow_sampling: Whether to allow MCP sampling through this client.
            sampling_model: The model to use for sampling.
            max_retries: The maximum number of times to retry a tool call.
            elicitation_callback: Callback function to handle elicitation requests from the server.
            cache_tools: Whether to cache the list of tools.
                See [`MCPServer.cache_tools`][pydantic_ai.mcp.MCPServer.cache_tools].
            cache_resources: Whether to cache the list of resources.
                See [`MCPServer.cache_resources`][pydantic_ai.mcp.MCPServer.cache_resources].
            id: An optional unique ID for the MCP server. An MCP server needs to have an ID in order to be used in a durable execution environment like Temporal, in which case the ID will be used to identify the server's activities within the workflow.
        """
        self.command = command
        self.args = args
        self.env = env
        self.cwd = cwd

        super().__init__(
            tool_prefix,
            log_level,
            log_handler,
            timeout,
            read_timeout,
            process_tool_call,
            allow_sampling,
            sampling_model,
            max_retries,
            elicitation_callback,
            cache_tools,
            cache_resources,
            id=id,
        )

    @classmethod
    def __get_pydantic_core_schema__(cls, _: Any, __: Any) -> CoreSchema:
        return core_schema.no_info_after_validator_function(
            lambda dct: MCPServerStdio(**dct),
            core_schema.typed_dict_schema(
                {
                    'command': core_schema.typed_dict_field(core_schema.str_schema()),
                    'args': core_schema.typed_dict_field(core_schema.list_schema(core_schema.str_schema())),
                    'env': core_schema.typed_dict_field(
                        core_schema.dict_schema(core_schema.str_schema(), core_schema.str_schema()),
                        required=False,
                    ),
                }
            ),
        )

    @asynccontextmanager
    async def client_streams(
        self,
    ) -> AsyncIterator[
        tuple[
            MemoryObjectReceiveStream[SessionMessage | Exception],
            MemoryObjectSendStream[SessionMessage],
        ]
    ]:
        server = StdioServerParameters(command=self.command, args=list(self.args), env=self.env, cwd=self.cwd)
        async with stdio_client(server=server) as (read_stream, write_stream):
            yield read_stream, write_stream

    def __repr__(self) -> str:
        repr_args = [
            f'command={self.command!r}',
            f'args={self.args!r}',
        ]
        if self.id:
            repr_args.append(f'id={self.id!r}')  # pragma: lax no cover
        return f'{self.__class__.__name__}({", ".join(repr_args)})'

    def __eq__(self, value: object, /) -> bool:
        return (
            super().__eq__(value)
            and isinstance(value, MCPServerStdio)
            and self.command == value.command
            and self.args == value.args
            and self.env == value.env
            and self.cwd == value.cwd
        )

````

#### **init**

```python
__init__(
    command: str,
    args: Sequence[str],
    *,
    env: dict[str, str] | None = None,
    cwd: str | Path | None = None,
    tool_prefix: str | None = None,
    log_level: LoggingLevel | None = None,
    log_handler: LoggingFnT | None = None,
    timeout: float = 5,
    read_timeout: float = 5 * 60,
    process_tool_call: ProcessToolCallback | None = None,
    allow_sampling: bool = True,
    sampling_model: Model | None = None,
    max_retries: int = 1,
    elicitation_callback: ElicitationFnT | None = None,
    cache_tools: bool = True,
    cache_resources: bool = True,
    id: str | None = None
)

```

Build a new MCP server.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `command` | `str` | The command to run. | _required_ | | `args` | `Sequence[str]` | The arguments to pass to the command. | _required_ | | `env` | `dict[str, str] | None` | The environment variables to set in the subprocess. | `None` | | `cwd` | `str | Path | None` | The working directory to use when spawning the process. | `None` | | `tool_prefix` | `str | None` | A prefix to add to all tools that are registered with the server. | `None` | | `log_level` | `LoggingLevel | None` | The log level to set when connecting to the server, if any. | `None` | | `log_handler` | `LoggingFnT | None` | A handler for logging messages from the server. | `None` | | `timeout` | `float` | The timeout in seconds to wait for the client to initialize. | `5` | | `read_timeout` | `float` | Maximum time in seconds to wait for new messages before timing out. | `5 * 60` | | `process_tool_call` | `ProcessToolCallback | None` | Hook to customize tool calling and optionally pass extra metadata. | `None` | | `allow_sampling` | `bool` | Whether to allow MCP sampling through this client. | `True` | | `sampling_model` | `Model | None` | The model to use for sampling. | `None` | | `max_retries` | `int` | The maximum number of times to retry a tool call. | `1` | | `elicitation_callback` | `ElicitationFnT | None` | Callback function to handle elicitation requests from the server. | `None` | | `cache_tools` | `bool` | Whether to cache the list of tools. See MCPServer.cache_tools. | `True` | | `cache_resources` | `bool` | Whether to cache the list of resources. See MCPServer.cache_resources. | `True` | | `id` | `str | None` | An optional unique ID for the MCP server. An MCP server needs to have an ID in order to be used in a durable execution environment like Temporal, in which case the ID will be used to identify the server's activities within the workflow. | `None` |

Source code in `pydantic_ai_slim/pydantic_ai/mcp.py`

```python
def __init__(
    self,
    command: str,
    args: Sequence[str],
    *,
    env: dict[str, str] | None = None,
    cwd: str | Path | None = None,
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
    id: str | None = None,
):
    """Build a new MCP server.

    Args:
        command: The command to run.
        args: The arguments to pass to the command.
        env: The environment variables to set in the subprocess.
        cwd: The working directory to use when spawning the process.
        tool_prefix: A prefix to add to all tools that are registered with the server.
        log_level: The log level to set when connecting to the server, if any.
        log_handler: A handler for logging messages from the server.
        timeout: The timeout in seconds to wait for the client to initialize.
        read_timeout: Maximum time in seconds to wait for new messages before timing out.
        process_tool_call: Hook to customize tool calling and optionally pass extra metadata.
        allow_sampling: Whether to allow MCP sampling through this client.
        sampling_model: The model to use for sampling.
        max_retries: The maximum number of times to retry a tool call.
        elicitation_callback: Callback function to handle elicitation requests from the server.
        cache_tools: Whether to cache the list of tools.
            See [`MCPServer.cache_tools`][pydantic_ai.mcp.MCPServer.cache_tools].
        cache_resources: Whether to cache the list of resources.
            See [`MCPServer.cache_resources`][pydantic_ai.mcp.MCPServer.cache_resources].
        id: An optional unique ID for the MCP server. An MCP server needs to have an ID in order to be used in a durable execution environment like Temporal, in which case the ID will be used to identify the server's activities within the workflow.
    """
    self.command = command
    self.args = args
    self.env = env
    self.cwd = cwd

    super().__init__(
        tool_prefix,
        log_level,
        log_handler,
        timeout,
        read_timeout,
        process_tool_call,
        allow_sampling,
        sampling_model,
        max_retries,
        elicitation_callback,
        cache_tools,
        cache_resources,
        id=id,
    )

```

#### command

```python
command: str = command

```

The command to run.

#### args

```python
args: Sequence[str] = args

```

The arguments to pass to the command.

#### env

```python
env: dict[str, str] | None = env

```

The environment variables the CLI server will have access to.

By default the subprocess will not inherit any environment variables from the parent process. If you want to inherit the environment variables from the parent process, use `env=os.environ`.

#### cwd

```python
cwd: str | Path | None = cwd

```

The working directory to use when spawning the process.
