### ModelResponsePartDelta

```python
ModelResponsePartDelta = Annotated[
    TextPartDelta | ThinkingPartDelta | ToolCallPartDelta,
    Discriminator("part_delta_kind"),
]

```

A partial update (delta) for any model response part.
