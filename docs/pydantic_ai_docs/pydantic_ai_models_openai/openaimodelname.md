### OpenAIModelName

```python
OpenAIModelName = str | AllModels

```

Possible OpenAI model names.

Since OpenAI supports a variety of date-stamped models, we explicitly list the latest models but allow any name in the type hints. See [the OpenAI docs](https://platform.openai.com/docs/models) for a full list.

Using this more broad type for the model name instead of the ChatModel definition allows this model to be used more easily with other model types (ie, Ollama, Deepseek).
