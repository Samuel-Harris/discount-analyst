### OpenAI Responses

The OpenAIResponsesModel can generate native thinking parts. To enable this functionality, you need to set the OpenAIResponsesModelSettings.openai_reasoning_effort and OpenAIResponsesModelSettings.openai_reasoning_summary [model settings](../agents/#model-run-settings).

By default, the unique IDs of reasoning, text, and function call parts from the message history are sent to the model, which can result in errors like `"Item 'rs_123' of type 'reasoning' was provided without its required following item."` if the message history you're sending does not match exactly what was received from the Responses API in a previous response, for example if you're using a [history processor](../message-history/#processing-message-history). To disable this, you can disable the OpenAIResponsesModelSettings.openai_send_reasoning_ids [model setting](../agents/#model-run-settings).

openai_thinking_part.py

```python
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIResponsesModel, OpenAIResponsesModelSettings

model = OpenAIResponsesModel('gpt-5')
settings = OpenAIResponsesModelSettings(
    openai_reasoning_effort='low',
    openai_reasoning_summary='detailed',
)
agent = Agent(model, model_settings=settings)
...

```

Raw reasoning without summaries

Some OpenAI-compatible APIs (such as LM Studio, vLLM, or OpenRouter with gpt-oss models) may return raw reasoning content without reasoning summaries. In this case, ThinkingPart.content will be empty, but the raw reasoning is available in `provider_details['raw_content']`. Following [OpenAI's guidance](https://cookbook.openai.com/examples/responses_api/reasoning_items) that raw reasoning should not be shown directly to users, we store it in `provider_details` rather than in the main `content` field.
