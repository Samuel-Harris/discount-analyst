### ModelResponsePart

```python
ModelResponsePart = Annotated[
    TextPart
    | ToolCallPart
    | BuiltinToolCallPart
    | BuiltinToolReturnPart
    | ThinkingPart
    | FilePart,
    Discriminator("part_kind"),
]

```

A message part returned by a model.
