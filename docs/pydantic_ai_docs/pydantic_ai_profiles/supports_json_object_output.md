### supports_json_object_output

```python
supports_json_object_output: bool = False

```

Whether the model supports a dedicated mode to enforce JSON output, without necessarily sending a schema.

E.g. [OpenAI's JSON mode](https://platform.openai.com/docs/guides/structured-outputs#json-mode) Relates to the `PromptedOutput` output type.
