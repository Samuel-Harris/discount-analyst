### AgentStreamEvent

```python
AgentStreamEvent = Annotated[
    ModelResponseStreamEvent | HandleResponseEvent,
    Discriminator("event_kind"),
]

```

An event in the agent stream: model response stream events and response-handling events.
