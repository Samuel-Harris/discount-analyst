### FunctionDef

```python
FunctionDef: TypeAlias = Callable[
    [list[ModelMessage], AgentInfo],
    ModelResponse | Awaitable[ModelResponse],
]

```

A function used to generate a non-streamed response.
