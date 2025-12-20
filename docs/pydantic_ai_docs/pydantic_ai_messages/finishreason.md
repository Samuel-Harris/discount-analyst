### FinishReason

```python
FinishReason: TypeAlias = Literal[
    "stop", "length", "content_filter", "tool_call", "error"
]

```

Reason the model finished generating the response, normalized to OpenTelemetry values.
