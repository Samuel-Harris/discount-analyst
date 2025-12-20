### model_request

```python
model_request(
    model: Model | KnownModelName | str,
    messages: Sequence[ModelMessage],
    *,
    model_settings: ModelSettings | None = None,
    model_request_parameters: (
        ModelRequestParameters | None
    ) = None,
    instrument: InstrumentationSettings | bool | None = None
) -> ModelResponse

```

Make a non-streamed request to a model.

model_request_example.py

```py
from pydantic_ai import ModelRequest
from pydantic_ai.direct import model_request


async def main():
    model_response = await model_request(
        'anthropic:claude-haiku-4-5',
        [ModelRequest.user_text_prompt('What is the capital of France?')]  # (1)!
    )
    print(model_response)
    '''
    ModelResponse(
        parts=[TextPart(content='The capital of France is Paris.')],
        usage=RequestUsage(input_tokens=56, output_tokens=7),
        model_name='claude-haiku-4-5',
        timestamp=datetime.datetime(...),
    )
    '''

```

1. See ModelRequest.user_text_prompt for details.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `model` | `Model | KnownModelName | str` | The model to make a request to. We allow str here since the actual list of allowed models changes frequently. | _required_ | | `messages` | `Sequence[ModelMessage]` | Messages to send to the model | _required_ | | `model_settings` | `ModelSettings | None` | optional model settings | `None` | | `model_request_parameters` | `ModelRequestParameters | None` | optional model request parameters | `None` | | `instrument` | `InstrumentationSettings | bool | None` | Whether to instrument the request with OpenTelemetry/Logfire, if None the value from logfire.instrument_pydantic_ai is used. | `None` |

Returns:

| Type | Description | | --- | --- | | `ModelResponse` | The model response and token usage associated with the request. |

Source code in `pydantic_ai_slim/pydantic_ai/direct.py`

````python
async def model_request(
    model: models.Model | models.KnownModelName | str,
    messages: Sequence[messages.ModelMessage],
    *,
    model_settings: settings.ModelSettings | None = None,
    model_request_parameters: models.ModelRequestParameters | None = None,
    instrument: instrumented_models.InstrumentationSettings | bool | None = None,
) -> messages.ModelResponse:
    """Make a non-streamed request to a model.

    ```py title="model_request_example.py"
    from pydantic_ai import ModelRequest
    from pydantic_ai.direct import model_request


    async def main():
        model_response = await model_request(
            'anthropic:claude-haiku-4-5',
            [ModelRequest.user_text_prompt('What is the capital of France?')]  # (1)!
        )
        print(model_response)
        '''
        ModelResponse(
            parts=[TextPart(content='The capital of France is Paris.')],
            usage=RequestUsage(input_tokens=56, output_tokens=7),
            model_name='claude-haiku-4-5',
            timestamp=datetime.datetime(...),
        )
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
        The model response and token usage associated with the request.
    """
    model_instance = _prepare_model(model, instrument)
    return await model_instance.request(
        list(messages),
        model_settings,
        model_request_parameters or models.ModelRequestParameters(),
    )

````
