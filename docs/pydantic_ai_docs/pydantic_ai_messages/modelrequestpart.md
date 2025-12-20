### ModelRequestPart

```python
ModelRequestPart = Annotated[
    SystemPromptPart
    | UserPromptPart
    | ToolReturnPart
    | RetryPromptPart,
    Discriminator("part_kind"),
]

```

A message part sent by Pydantic AI to a model.
