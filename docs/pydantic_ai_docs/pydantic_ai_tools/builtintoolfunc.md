### BuiltinToolFunc

```python
BuiltinToolFunc: TypeAlias = Callable[
    [RunContext[AgentDepsT]],
    Awaitable[AbstractBuiltinTool | None]
    | AbstractBuiltinTool
    | None,
]

```

Definition of a function that can prepare a builtin tool at call time.

This is useful if you want to customize the builtin tool based on the run context (e.g. user dependencies), or omit it completely from a step.
