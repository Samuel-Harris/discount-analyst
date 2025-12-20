### ReducerFunction

```python
ReducerFunction = TypeAliasType(
    "ReducerFunction",
    ContextReducerFunction[StateT, DepsT, InputT, OutputT]
    | PlainReducerFunction[InputT, OutputT],
    type_params=(StateT, DepsT, InputT, OutputT),
)

```

A function used for reducing inputs to a join node.
