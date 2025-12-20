### ModelResponseStreamEvent

```python
ModelResponseStreamEvent = Annotated[
    PartStartEvent
    | PartDeltaEvent
    | PartEndEvent
    | FinalResultEvent,
    Discriminator("event_kind"),
]

```

An event in the model response stream, starting a new part, applying a delta to an existing one, indicating a part is complete, or indicating the final result.
