### OpenAIResponsesModelSettings

Bases: `OpenAIChatModelSettings`

Settings used for an OpenAI Responses model request.

ALL FIELDS MUST BE `openai_` PREFIXED SO YOU CAN MERGE THEM WITH OTHER MODELS.

Source code in `pydantic_ai_slim/pydantic_ai/models/openai.py`

```python
class OpenAIResponsesModelSettings(OpenAIChatModelSettings, total=False):
    """Settings used for an OpenAI Responses model request.

    ALL FIELDS MUST BE `openai_` PREFIXED SO YOU CAN MERGE THEM WITH OTHER MODELS.
    """

    openai_builtin_tools: Sequence[FileSearchToolParam | WebSearchToolParam | ComputerToolParam]
    """The provided OpenAI built-in tools to use.

    See [OpenAI's built-in tools](https://platform.openai.com/docs/guides/tools?api-mode=responses) for more details.
    """

    openai_reasoning_generate_summary: Literal['detailed', 'concise']
    """Deprecated alias for `openai_reasoning_summary`."""

    openai_reasoning_summary: Literal['detailed', 'concise']
    """A summary of the reasoning performed by the model.

    This can be useful for debugging and understanding the model's reasoning process.
    One of `concise` or `detailed`.

    Check the [OpenAI Reasoning documentation](https://platform.openai.com/docs/guides/reasoning?api-mode=responses#reasoning-summaries)
    for more details.
    """

    openai_send_reasoning_ids: bool
    """Whether to send the unique IDs of reasoning, text, and function call parts from the message history to the model. Enabled by default for reasoning models.

    This can result in errors like `"Item 'rs_123' of type 'reasoning' was provided without its required following item."`
    if the message history you're sending does not match exactly what was received from the Responses API in a previous response,
    for example if you're using a [history processor](../../message-history.md#processing-message-history).
    In that case, you'll want to disable this.
    """

    openai_truncation: Literal['disabled', 'auto']
    """The truncation strategy to use for the model response.

    It can be either:
    - `disabled` (default): If a model response will exceed the context window size for a model, the
        request will fail with a 400 error.
    - `auto`: If the context of this response and previous ones exceeds the model's context window size,
        the model will truncate the response to fit the context window by dropping input items in the
        middle of the conversation.
    """

    openai_text_verbosity: Literal['low', 'medium', 'high']
    """Constrains the verbosity of the model's text response.

    Lower values will result in more concise responses, while higher values will
    result in more verbose responses. Currently supported values are `low`,
    `medium`, and `high`.
    """

    openai_previous_response_id: Literal['auto'] | str
    """The ID of a previous response from the model to use as the starting point for a continued conversation.

    When set to `'auto'`, the request automatically uses the most recent
    `provider_response_id` from the message history and omits earlier messages.

    This enables the model to use server-side conversation state and faithfully reference previous reasoning.
    See the [OpenAI Responses API documentation](https://platform.openai.com/docs/guides/reasoning#keeping-reasoning-items-in-context)
    for more information.
    """

    openai_include_code_execution_outputs: bool
    """Whether to include the code execution results in the response.

    Corresponds to the `code_interpreter_call.outputs` value of the `include` parameter in the Responses API.
    """

    openai_include_web_search_sources: bool
    """Whether to include the web search results in the response.

    Corresponds to the `web_search_call.action.sources` value of the `include` parameter in the Responses API.
    """

```

#### openai_builtin_tools

```python
openai_builtin_tools: Sequence[
    FileSearchToolParam
    | WebSearchToolParam
    | ComputerToolParam
]

```

The provided OpenAI built-in tools to use.

See [OpenAI's built-in tools](https://platform.openai.com/docs/guides/tools?api-mode=responses) for more details.

#### openai_reasoning_generate_summary

```python
openai_reasoning_generate_summary: Literal[
    "detailed", "concise"
]

```

Deprecated alias for `openai_reasoning_summary`.

#### openai_reasoning_summary

```python
openai_reasoning_summary: Literal['detailed', 'concise']

```

A summary of the reasoning performed by the model.

This can be useful for debugging and understanding the model's reasoning process. One of `concise` or `detailed`.

Check the [OpenAI Reasoning documentation](https://platform.openai.com/docs/guides/reasoning?api-mode=responses#reasoning-summaries) for more details.

#### openai_send_reasoning_ids

```python
openai_send_reasoning_ids: bool

```

Whether to send the unique IDs of reasoning, text, and function call parts from the message history to the model. Enabled by default for reasoning models.

This can result in errors like `"Item 'rs_123' of type 'reasoning' was provided without its required following item."` if the message history you're sending does not match exactly what was received from the Responses API in a previous response, for example if you're using a [history processor](../../../message-history/#processing-message-history). In that case, you'll want to disable this.

#### openai_truncation

```python
openai_truncation: Literal['disabled', 'auto']

```

The truncation strategy to use for the model response.

It can be either:

- `disabled` (default): If a model response will exceed the context window size for a model, the request will fail with a 400 error.
- `auto`: If the context of this response and previous ones exceeds the model's context window size, the model will truncate the response to fit the context window by dropping input items in the middle of the conversation.

#### openai_text_verbosity

```python
openai_text_verbosity: Literal['low', 'medium', 'high']

```

Constrains the verbosity of the model's text response.

Lower values will result in more concise responses, while higher values will result in more verbose responses. Currently supported values are `low`, `medium`, and `high`.

#### openai_previous_response_id

```python
openai_previous_response_id: Literal['auto'] | str

```

The ID of a previous response from the model to use as the starting point for a continued conversation.

When set to `'auto'`, the request automatically uses the most recent `provider_response_id` from the message history and omits earlier messages.

This enables the model to use server-side conversation state and faithfully reference previous reasoning. See the [OpenAI Responses API documentation](https://platform.openai.com/docs/guides/reasoning#keeping-reasoning-items-in-context) for more information.

#### openai_include_code_execution_outputs

```python
openai_include_code_execution_outputs: bool

```

Whether to include the code execution results in the response.

Corresponds to the `code_interpreter_call.outputs` value of the `include` parameter in the Responses API.

#### openai_include_web_search_sources

```python
openai_include_web_search_sources: bool

```

Whether to include the web search results in the response.

Corresponds to the `web_search_call.action.sources` value of the `include` parameter in the Responses API.
