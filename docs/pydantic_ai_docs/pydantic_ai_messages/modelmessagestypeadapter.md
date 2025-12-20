### ModelMessagesTypeAdapter

```python
ModelMessagesTypeAdapter = TypeAdapter(
    list[ModelMessage],
    config=ConfigDict(
        defer_build=True,
        ser_json_bytes="base64",
        val_json_bytes="base64",
    ),
)

```

Pydantic TypeAdapter for (de)serializing messages.
