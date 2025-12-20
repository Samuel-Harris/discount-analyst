### FunctionModel

Bases: `Model`

A model controlled by a local function.

Apart from `__init__`, all methods are private or match those of the base class.

Source code in `pydantic_ai_slim/pydantic_ai/models/function.py`

```python
@dataclass(init=False)
class FunctionModel(Model):
    """A model controlled by a local function.

    Apart from `__init__`, all methods are private or match those of the base class.
    """

    function: FunctionDef | None
    stream_function: StreamFunctionDef | None

    _model_name: str = field(repr=False)
    _system: str = field(default='function', repr=False)

    @overload
    def __init__(
        self,
        function: FunctionDef,
        *,
        model_name: str | None = None,
        profile: ModelProfileSpec | None = None,
        settings: ModelSettings | None = None,
    ) -> None: ...

    @overload
    def __init__(
        self,
        *,
        stream_function: StreamFunctionDef,
        model_name: str | None = None,
        profile: ModelProfileSpec | None = None,
        settings: ModelSettings | None = None,
    ) -> None: ...

    @overload
    def __init__(
        self,
        function: FunctionDef,
        *,
        stream_function: StreamFunctionDef,
        model_name: str | None = None,
        profile: ModelProfileSpec | None = None,
        settings: ModelSettings | None = None,
    ) -> None: ...

    def __init__(
        self,
        function: FunctionDef | None = None,
        *,
        stream_function: StreamFunctionDef | None = None,
        model_name: str | None = None,
        profile: ModelProfileSpec | None = None,
        settings: ModelSettings | None = None,
    ):
        """Initialize a `FunctionModel`.

        Either `function` or `stream_function` must be provided, providing both is allowed.

        Args:
            function: The function to call for non-streamed requests.
            stream_function: The function to call for streamed requests.
            model_name: The name of the model. If not provided, a name is generated from the function names.
            profile: The model profile to use.
            settings: Model-specific settings that will be used as defaults for this model.
        """
        if function is None and stream_function is None:
            raise TypeError('Either `function` or `stream_function` must be provided')

        self.function = function
        self.stream_function = stream_function

        function_name = self.function.__name__ if self.function is not None else ''
        stream_function_name = self.stream_function.__name__ if self.stream_function is not None else ''
        self._model_name = model_name or f'function:{function_name}:{stream_function_name}'

        # Use a default profile that supports JSON schema and object output if none provided
        if profile is None:
            profile = ModelProfile(
                supports_json_schema_output=True,
                supports_json_object_output=True,
            )
        super().__init__(settings=settings, profile=profile)

    async def request(
        self,
        messages: list[ModelMessage],
        model_settings: ModelSettings | None,
        model_request_parameters: ModelRequestParameters,
    ) -> ModelResponse:
        model_settings, model_request_parameters = self.prepare_request(
            model_settings,
            model_request_parameters,
        )
        agent_info = AgentInfo(
            function_tools=model_request_parameters.function_tools,
            allow_text_output=model_request_parameters.allow_text_output,
            output_tools=model_request_parameters.output_tools,
            model_settings=model_settings,
            model_request_parameters=model_request_parameters,
            instructions=self._get_instructions(messages, model_request_parameters),
        )

        assert self.function is not None, 'FunctionModel must receive a `function` to support non-streamed requests'

        if inspect.iscoroutinefunction(self.function):
            response = await self.function(messages, agent_info)
        else:
            response_ = await _utils.run_in_executor(self.function, messages, agent_info)
            assert isinstance(response_, ModelResponse), response_
            response = response_
        response.model_name = self._model_name
        # Add usage data if not already present
        if not response.usage.has_values():  # pragma: no branch
            response.usage = _estimate_usage(chain(messages, [response]))
        return response

    @asynccontextmanager
    async def request_stream(
        self,
        messages: list[ModelMessage],
        model_settings: ModelSettings | None,
        model_request_parameters: ModelRequestParameters,
        run_context: RunContext[Any] | None = None,
    ) -> AsyncIterator[StreamedResponse]:
        model_settings, model_request_parameters = self.prepare_request(
            model_settings,
            model_request_parameters,
        )
        agent_info = AgentInfo(
            function_tools=model_request_parameters.function_tools,
            allow_text_output=model_request_parameters.allow_text_output,
            output_tools=model_request_parameters.output_tools,
            model_settings=model_settings,
            model_request_parameters=model_request_parameters,
            instructions=self._get_instructions(messages, model_request_parameters),
        )

        assert self.stream_function is not None, (
            'FunctionModel must receive a `stream_function` to support streamed requests'
        )

        response_stream = PeekableAsyncStream(self.stream_function(messages, agent_info))

        first = await response_stream.peek()
        if isinstance(first, _utils.Unset):
            raise ValueError('Stream function must return at least one item')

        yield FunctionStreamedResponse(
            model_request_parameters=model_request_parameters,
            _model_name=self._model_name,
            _iter=response_stream,
        )

    @property
    def model_name(self) -> str:
        """The model name."""
        return self._model_name

    @property
    def system(self) -> str:
        """The system / model provider."""
        return self._system

```

#### **init**

```python
__init__(
    function: FunctionDef,
    *,
    model_name: str | None = None,
    profile: ModelProfileSpec | None = None,
    settings: ModelSettings | None = None
) -> None

```

```python
__init__(
    *,
    stream_function: StreamFunctionDef,
    model_name: str | None = None,
    profile: ModelProfileSpec | None = None,
    settings: ModelSettings | None = None
) -> None

```

```python
__init__(
    function: FunctionDef,
    *,
    stream_function: StreamFunctionDef,
    model_name: str | None = None,
    profile: ModelProfileSpec | None = None,
    settings: ModelSettings | None = None
) -> None

```

```python
__init__(
    function: FunctionDef | None = None,
    *,
    stream_function: StreamFunctionDef | None = None,
    model_name: str | None = None,
    profile: ModelProfileSpec | None = None,
    settings: ModelSettings | None = None
)

```

Initialize a `FunctionModel`.

Either `function` or `stream_function` must be provided, providing both is allowed.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `function` | `FunctionDef | None` | The function to call for non-streamed requests. | `None` | | `stream_function` | `StreamFunctionDef | None` | The function to call for streamed requests. | `None` | | `model_name` | `str | None` | The name of the model. If not provided, a name is generated from the function names. | `None` | | `profile` | `ModelProfileSpec | None` | The model profile to use. | `None` | | `settings` | `ModelSettings | None` | Model-specific settings that will be used as defaults for this model. | `None` |

Source code in `pydantic_ai_slim/pydantic_ai/models/function.py`

```python
def __init__(
    self,
    function: FunctionDef | None = None,
    *,
    stream_function: StreamFunctionDef | None = None,
    model_name: str | None = None,
    profile: ModelProfileSpec | None = None,
    settings: ModelSettings | None = None,
):
    """Initialize a `FunctionModel`.

    Either `function` or `stream_function` must be provided, providing both is allowed.

    Args:
        function: The function to call for non-streamed requests.
        stream_function: The function to call for streamed requests.
        model_name: The name of the model. If not provided, a name is generated from the function names.
        profile: The model profile to use.
        settings: Model-specific settings that will be used as defaults for this model.
    """
    if function is None and stream_function is None:
        raise TypeError('Either `function` or `stream_function` must be provided')

    self.function = function
    self.stream_function = stream_function

    function_name = self.function.__name__ if self.function is not None else ''
    stream_function_name = self.stream_function.__name__ if self.stream_function is not None else ''
    self._model_name = model_name or f'function:{function_name}:{stream_function_name}'

    # Use a default profile that supports JSON schema and object output if none provided
    if profile is None:
        profile = ModelProfile(
            supports_json_schema_output=True,
            supports_json_object_output=True,
        )
    super().__init__(settings=settings, profile=profile)

```

#### model_name

```python
model_name: str

```

The model name.

#### system

```python
system: str

```

The system / model provider.
