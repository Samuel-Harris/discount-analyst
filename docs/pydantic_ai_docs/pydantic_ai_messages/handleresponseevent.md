### HandleResponseEvent

```python
HandleResponseEvent = Annotated[
    FunctionToolCallEvent
    | FunctionToolResultEvent
    | BuiltinToolCallEvent
    | BuiltinToolResultEvent,
    Discriminator("event_kind"),
]

```

An event yielded when handling a model response, indicating tool calls and results.
