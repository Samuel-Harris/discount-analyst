### model_request_stream

```python
model_request_stream(
    model: Model | KnownModelName | str,
    messages: Sequence[ModelMessage],
    *,
    model_settings: ModelSettings | None = None,
    model_request_parameters: (
        ModelRequestParameters | None
    ) = None,
    instrument: InstrumentationSettings | bool | None = None
) -> AbstractAsyncContextManager[StreamedResponse]

```

Make a streamed async request to a model.

model_request_stream_example.py

```py
from pydantic_ai import ModelRequest
from pydantic_ai.direct import model_request_stream


async def main():
    messages = [ModelRequest.user_text_prompt('Who was Albert Einstein?')]  # (1)!
    async with model_request_stream('openai:gpt-4.1-mini', messages) as stream:
        chunks = []
        async for chunk in stream:
            chunks.append(chunk)
        print(chunks)
        '''
        [
            PartStartEvent(index=0, part=TextPart(content='Albert Einstein was ')),
            FinalResultEvent(tool_name=None, tool_call_id=None),
            PartDeltaEvent(
                index=0, delta=TextPartDelta(content_delta='a German-born theoretical ')
            ),
            PartDeltaEvent(index=0, delta=TextPartDelta(content_delta='physicist.')),
            PartEndEvent(
                index=0,
                part=TextPart(
                    content='Albert Einstein was a German-born theoretical physicist.'
                ),
            ),
        ]
        '''

```

1. See ModelRequest.user_text_prompt for details.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `model` | `Model | KnownModelName | str` | The model to make a request to. We allow str here since the actual list of allowed models changes frequently. | _required_ | | `messages` | `Sequence[ModelMessage]` | Messages to send to the model | _required_ | | `model_settings` | `ModelSettings | None` | optional model settings | `None` | | `model_request_parameters` | `ModelRequestParameters | None` | optional model request parameters | `None` | | `instrument` | `InstrumentationSettings | bool | None` | Whether to instrument the request with OpenTelemetry/Logfire, if None the value from logfire.instrument_pydantic_ai is used. | `None` |

Returns:

| Type | Description | | --- | --- | | `AbstractAsyncContextManager[StreamedResponse]` | A stream response async context manager. |

Source code in `pydantic_ai_slim/pydantic_ai/direct.py`

````python
def model_request_stream(
    model: models.Model | models.KnownModelName | str,
    messages: Sequence[messages.ModelMessage],
    *,
    model_settings: settings.ModelSettings | None = None,
    model_request_parameters: models.ModelRequestParameters | None = None,
    instrument: instrumented_models.InstrumentationSettings | bool | None = None,
) -> AbstractAsyncContextManager[models.StreamedResponse]:
    """Make a streamed async request to a model.

    ```py {title="model_request_stream_example.py"}

    from pydantic_ai import ModelRequest
    from pydantic_ai.direct import model_request_stream


    async def main():
        messages = [ModelRequest.user_text_prompt('Who was Albert Einstein?')]  # (1)!
        async with model_request_stream('openai:gpt-4.1-mini', messages) as stream:
            chunks = []
            async for chunk in stream:
                chunks.append(chunk)
            print(chunks)
            '''
            [
                PartStartEvent(index=0, part=TextPart(content='Albert Einstein was ')),
                FinalResultEvent(tool_name=None, tool_call_id=None),
                PartDeltaEvent(
                    index=0, delta=TextPartDelta(content_delta='a German-born theoretical ')
                ),
                PartDeltaEvent(index=0, delta=TextPartDelta(content_delta='physicist.')),
                PartEndEvent(
                    index=0,
                    part=TextPart(
                        content='Albert Einstein was a German-born theoretical physicist.'
                    ),
                ),
            ]
            '''
    ```

    1. See [`ModelRequest.user_text_prompt`][pydantic_ai.messages.ModelRequest.user_text_prompt] for details.

    Args:
        model: The model to make a request to. We allow `str` here since the actual list of allowed models changes frequently.
        messages: Messages to send to the model
        model_settings: optional model settings
        model_request_parameters: optional model request parameters
        instrument: Whether to instrument the request with OpenTelemetry/Logfire, if `None` the value from
            [`logfire.instrument_pydantic_ai`][logfire.Logfire.instrument_pydantic_ai] is used.

    Returns:
        A [stream response][pydantic_ai.models.StreamedResponse] async context manager.
    """
    model_instance = _prepare_model(model, instrument)
    return model_instance.request_stream(
        list(messages),
        model_settings,
        model_request_parameters or models.ModelRequestParameters(),
    )

````
