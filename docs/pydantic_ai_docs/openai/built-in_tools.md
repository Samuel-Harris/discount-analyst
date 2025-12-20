### Built-in tools

The Responses API has built-in tools that you can use instead of building your own:

- [Web search](https://platform.openai.com/docs/guides/tools-web-search): allow models to search the web for the latest information before generating a response.
- [Code interpreter](https://platform.openai.com/docs/guides/tools-code-interpreter): allow models to write and run Python code in a sandboxed environment before generating a response.
- [Image generation](https://platform.openai.com/docs/guides/tools-image-generation): allow models to generate images based on a text prompt.
- [File search](https://platform.openai.com/docs/guides/tools-file-search): allow models to search your files for relevant information before generating a response.
- [Computer use](https://platform.openai.com/docs/guides/tools-computer-use): allow models to use a computer to perform tasks on your behalf.

Web search, Code interpreter, and Image generation are natively supported through the [Built-in tools](../../builtin-tools/) feature.

File search and Computer use can be enabled by passing an [`openai.types.responses.FileSearchToolParam`](https://github.com/openai/openai-python/blob/main/src/openai/types/responses/file_search_tool_param.py) or [`openai.types.responses.ComputerToolParam`](https://github.com/openai/openai-python/blob/main/src/openai/types/responses/computer_tool_param.py) in the `openai_builtin_tools` setting on OpenAIResponsesModelSettings. They don't currently generate BuiltinToolCallPart or BuiltinToolReturnPart parts in the message history, or streamed events; please submit an issue if you need native support for these built-in tools.

file_search_tool.py

```python
from openai.types.responses import FileSearchToolParam

from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIResponsesModel, OpenAIResponsesModelSettings

model_settings = OpenAIResponsesModelSettings(
    openai_builtin_tools=[
        FileSearchToolParam(
            type='file_search',
            vector_store_ids=['your-history-book-vector-store-id']
        )
    ],
)
model = OpenAIResponsesModel('gpt-5')
agent = Agent(model=model, model_settings=model_settings)

result = agent.run_sync('Who was Albert Einstein?')
print(result.output)
#> Albert Einstein was a German-born theoretical physicist.

```

#### Referencing earlier responses

The Responses API supports referencing earlier model responses in a new request using a `previous_response_id` parameter, to ensure the full [conversation state](https://platform.openai.com/docs/guides/conversation-state?api-mode=responses#passing-context-from-the-previous-response) including [reasoning items](https://platform.openai.com/docs/guides/reasoning#keeping-reasoning-items-in-context) are kept in context. This is available through the `openai_previous_response_id` field in OpenAIResponsesModelSettings.

```python
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIResponsesModel, OpenAIResponsesModelSettings

model = OpenAIResponsesModel('gpt-5')
agent = Agent(model=model)

result = agent.run_sync('The secret is 1234')
model_settings = OpenAIResponsesModelSettings(
    openai_previous_response_id=result.all_messages()[-1].provider_response_id
)
result = agent.run_sync('What is the secret code?', model_settings=model_settings)
print(result.output)
#> 1234

```

By passing the `provider_response_id` from an earlier run, you can allow the model to build on its own prior reasoning without needing to resend the full message history.

##### Automatically referencing earlier responses

When the `openai_previous_response_id` field is set to `'auto'`, Pydantic AI will automatically select the most recent `provider_response_id` from message history and omit messages that came before it, letting the OpenAI API leverage server-side history instead for improved efficiency.

```python
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIResponsesModel, OpenAIResponsesModelSettings

model = OpenAIResponsesModel('gpt-5')
agent = Agent(model=model)

result1 = agent.run_sync('Tell me a joke.')
print(result1.output)
#> Did you hear about the toothpaste scandal? They called it Colgate.
