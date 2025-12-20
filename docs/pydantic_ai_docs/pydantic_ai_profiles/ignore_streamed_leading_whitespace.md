### ignore_streamed_leading_whitespace

```python
ignore_streamed_leading_whitespace: bool = False

```

Whether to ignore leading whitespace when streaming a response.

```text
This is a workaround for models that emit `<think>

```

`or an empty text part ahead of tool calls (e.g. Ollama + Qwen3), which we don't want to end up treating as a final result when using`run_stream`with`str`a valid`output_type\`.

```text
This is currently only used by `OpenAIChatModel`, `HuggingFaceModel`, and `GroqModel`.

```
