## Custom Models

Note

If a model API is compatible with the OpenAI API, you do not need a custom model class and can provide your own [custom provider](../openai/#openai-compatible-models) instead.

To implement support for a model API that's not already supported, you will need to subclass the Model abstract base class. For streaming, you'll also need to implement the StreamedResponse abstract base class.

The best place to start is to review the source code for existing implementations, e.g. [`OpenAIChatModel`](https://github.com/pydantic/pydantic-ai/blob/main/pydantic_ai_slim/pydantic_ai/models/openai.py).

For details on when we'll accept contributions adding new models to Pydantic AI, see the [contributing guidelines](../../contributing/#new-model-rules).
