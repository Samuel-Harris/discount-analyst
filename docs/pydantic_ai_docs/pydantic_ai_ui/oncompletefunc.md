### OnCompleteFunc

```python
OnCompleteFunc: TypeAlias = (
    Callable[[AgentRunResult[Any]], None]
    | Callable[[AgentRunResult[Any]], Awaitable[None]]
    | Callable[[AgentRunResult[Any]], AsyncIterator[EventT]]
)

```

Callback function type that receives the `AgentRunResult` of the completed run. Can be sync, async, or an async generator of protocol-specific events.
