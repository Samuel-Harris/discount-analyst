### ToolsetFunc

```python
ToolsetFunc: TypeAlias = Callable[
    [RunContext[AgentDepsT]],
    AbstractToolset[AgentDepsT]
    | None
    | Awaitable[AbstractToolset[AgentDepsT] | None],
]

```

A sync/async function which takes a run context and returns a toolset.
