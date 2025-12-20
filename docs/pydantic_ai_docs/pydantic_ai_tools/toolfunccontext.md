### ToolFuncContext

```python
ToolFuncContext: TypeAlias = Callable[
    Concatenate[RunContext[AgentDepsT], ToolParams], Any
]

```

A tool function that takes `RunContext` as the first argument.

Usage `ToolContextFunc[AgentDepsT, ToolParams]`.
