### SystemPromptFunc

```python
SystemPromptFunc: TypeAlias = (
    Callable[[RunContext[AgentDepsT]], str]
    | Callable[[RunContext[AgentDepsT]], Awaitable[str]]
    | Callable[[], str]
    | Callable[[], Awaitable[str]]
)

```

A function that may or maybe not take `RunContext` as an argument, and may or may not be async.

Usage `SystemPromptFunc[AgentDepsT]`.
