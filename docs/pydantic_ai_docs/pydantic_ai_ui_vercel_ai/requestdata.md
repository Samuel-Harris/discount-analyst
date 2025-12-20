### RequestData

```python
RequestData = Annotated[
    SubmitMessage | RegenerateMessage,
    Discriminator("trigger"),
]

```

Union of all request data types.

Vercel AI response types (SSE chunks).

Converted to Python from: https://github.com/vercel/ai/blob/ai%405.0.59/packages/ai/src/ui-message-stream/ui-message-chunks.ts
