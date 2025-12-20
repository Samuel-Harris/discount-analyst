### ToolFuncEither

```python
ToolFuncEither: TypeAlias = (
    ToolFuncContext[AgentDepsT, ToolParams]
    | ToolFuncPlain[ToolParams]
)

```

Either kind of tool function.

This is just a union of ToolFuncContext and ToolFuncPlain.

Usage `ToolFuncEither[AgentDepsT, ToolParams]`.
