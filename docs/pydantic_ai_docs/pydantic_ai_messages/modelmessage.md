### ModelMessage

```python
ModelMessage = Annotated[
    ModelRequest | ModelResponse, Discriminator("kind")
]

```

Any message sent to or returned by a model.
