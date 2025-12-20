### RunContext

Bases: `Generic[RunContextAgentDepsT]`

Information about the current call.

Source code in `pydantic_ai_slim/pydantic_ai/_run_context.py`

```python
@dataclasses.dataclass(repr=False, kw_only=True)
class RunContext(Generic[RunContextAgentDepsT]):
    """Information about the current call."""

    deps: RunContextAgentDepsT
    """Dependencies for the agent."""
    model: Model
    """The model used in this run."""
    usage: RunUsage
    """LLM usage associated with the run."""
    prompt: str | Sequence[_messages.UserContent] | None = None
    """The original user prompt passed to the run."""
    messages: list[_messages.ModelMessage] = field(default_factory=list)
    """Messages exchanged in the conversation so far."""
    validation_context: Any = None
    """Pydantic [validation context](https://docs.pydantic.dev/latest/concepts/validators/#validation-context) for tool args and run outputs."""
    tracer: Tracer = field(default_factory=NoOpTracer)
    """The tracer to use for tracing the run."""
    trace_include_content: bool = False
    """Whether to include the content of the messages in the trace."""
    instrumentation_version: int = DEFAULT_INSTRUMENTATION_VERSION
    """Instrumentation settings version, if instrumentation is enabled."""
    retries: dict[str, int] = field(default_factory=dict)
    """Number of retries for each tool so far."""
    tool_call_id: str | None = None
    """The ID of the tool call."""
    tool_name: str | None = None
    """Name of the tool being called."""
    retry: int = 0
    """Number of retries of this tool so far."""
    max_retries: int = 0
    """The maximum number of retries of this tool."""
    run_step: int = 0
    """The current step in the run."""
    tool_call_approved: bool = False
    """Whether a tool call that required approval has now been approved."""
    partial_output: bool = False
    """Whether the output passed to an output validator is partial."""
    run_id: str | None = None
    """"Unique identifier for the agent run."""

    @property
    def last_attempt(self) -> bool:
        """Whether this is the last attempt at running this tool before an error is raised."""
        return self.retry == self.max_retries

    __repr__ = _utils.dataclasses_no_defaults_repr

```

#### deps

```python
deps: RunContextAgentDepsT

```

Dependencies for the agent.

#### model

```python
model: Model

```

The model used in this run.

#### usage

```python
usage: RunUsage

```

LLM usage associated with the run.

#### prompt

```python
prompt: str | Sequence[UserContent] | None = None

```

The original user prompt passed to the run.

#### messages

```python
messages: list[ModelMessage] = field(default_factory=list)

```

Messages exchanged in the conversation so far.

#### validation_context

```python
validation_context: Any = None

```

Pydantic [validation context](https://docs.pydantic.dev/latest/concepts/validators/#validation-context) for tool args and run outputs.

#### tracer

```python
tracer: Tracer = field(default_factory=NoOpTracer)

```

The tracer to use for tracing the run.

#### trace_include_content

```python
trace_include_content: bool = False

```

Whether to include the content of the messages in the trace.

#### instrumentation_version

```python
instrumentation_version: int = (
    DEFAULT_INSTRUMENTATION_VERSION
)

```

Instrumentation settings version, if instrumentation is enabled.

#### retries

```python
retries: dict[str, int] = field(default_factory=dict)

```

Number of retries for each tool so far.

#### tool_call_id

```python
tool_call_id: str | None = None

```

The ID of the tool call.

#### tool_name

```python
tool_name: str | None = None

```

Name of the tool being called.

#### retry

```python
retry: int = 0

```

Number of retries of this tool so far.

#### max_retries

```python
max_retries: int = 0

```

The maximum number of retries of this tool.

#### run_step

```python
run_step: int = 0

```

The current step in the run.

#### tool_call_approved

```python
tool_call_approved: bool = False

```

Whether a tool call that required approval has now been approved.

#### partial_output

```python
partial_output: bool = False

```

Whether the output passed to an output validator is partial.

#### run_id

```python
run_id: str | None = None

```

"Unique identifier for the agent run.

#### last_attempt

```python
last_attempt: bool

```

Whether this is the last attempt at running this tool before an error is raised.
