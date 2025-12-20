### model_request_stream_sync

```python
model_request_stream_sync(
    model: Model | KnownModelName | str,
    messages: Sequence[ModelMessage],
    *,
    model_settings: ModelSettings | None = None,
    model_request_parameters: (
        ModelRequestParameters | None
    ) = None,
    instrument: InstrumentationSettings | bool | None = None
) -> StreamedResponseSync

```

Make a streamed synchronous request to a model.

This is the synchronous version of model_request_stream. It uses threading to run the asynchronous stream in the background while providing a synchronous iterator interface.

model_request_stream_sync_example.py

```py
from pydantic_ai import ModelRequest
from pydantic_ai.direct import model_request_stream_sync

messages = [ModelRequest.user_text_prompt('Who was Albert Einstein?')]
with model_request_stream_sync('openai:gpt-4.1-mini', messages) as stream:
    chunks = []
    for chunk in stream:
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

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `model` | `Model | KnownModelName | str` | The model to make a request to. We allow str here since the actual list of allowed models changes frequently. | _required_ | | `messages` | `Sequence[ModelMessage]` | Messages to send to the model | _required_ | | `model_settings` | `ModelSettings | None` | optional model settings | `None` | | `model_request_parameters` | `ModelRequestParameters | None` | optional model request parameters | `None` | | `instrument` | `InstrumentationSettings | bool | None` | Whether to instrument the request with OpenTelemetry/Logfire, if None the value from logfire.instrument_pydantic_ai is used. | `None` |

Returns:

| Type | Description | | --- | --- | | `StreamedResponseSync` | A sync stream response context manager. |

Source code in `pydantic_ai_slim/pydantic_ai/direct.py`

````python
def model_request_stream_sync(
    model: models.Model | models.KnownModelName | str,
    messages: Sequence[messages.ModelMessage],
    *,
    model_settings: settings.ModelSettings | None = None,
    model_request_parameters: models.ModelRequestParameters | None = None,
    instrument: instrumented_models.InstrumentationSettings | bool | None = None,
) -> StreamedResponseSync:
    """Make a streamed synchronous request to a model.

    This is the synchronous version of [`model_request_stream`][pydantic_ai.direct.model_request_stream].
    It uses threading to run the asynchronous stream in the background while providing a synchronous iterator interface.

    ```py {title="model_request_stream_sync_example.py"}

    from pydantic_ai import ModelRequest
    from pydantic_ai.direct import model_request_stream_sync

    messages = [ModelRequest.user_text_prompt('Who was Albert Einstein?')]
    with model_request_stream_sync('openai:gpt-4.1-mini', messages) as stream:
        chunks = []
        for chunk in stream:
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

    Args:
        model: The model to make a request to. We allow `str` here since the actual list of allowed models changes frequently.
        messages: Messages to send to the model
        model_settings: optional model settings
        model_request_parameters: optional model request parameters
        instrument: Whether to instrument the request with OpenTelemetry/Logfire, if `None` the value from
            [`logfire.instrument_pydantic_ai`][logfire.Logfire.instrument_pydantic_ai] is used.

    Returns:
        A [sync stream response][pydantic_ai.direct.StreamedResponseSync] context manager.
    """
    async_stream_cm = model_request_stream(
        model=model,
        messages=list(messages),
        model_settings=model_settings,
        model_request_parameters=model_request_parameters,
        instrument=instrument,
    )

    return StreamedResponseSync(async_stream_cm)

````
