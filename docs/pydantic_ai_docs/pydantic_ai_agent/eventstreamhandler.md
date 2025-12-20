### EventStreamHandler

```python
EventStreamHandler: TypeAlias = Callable[
    [
        RunContext[AgentDepsT],
        AsyncIterable[AgentStreamEvent],
    ],
    Awaitable[None],
]

```

A function that receives agent RunContext and an async iterable of events from the model's streaming response and the agent's execution of tools.
