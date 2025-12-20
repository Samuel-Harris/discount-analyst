### Model

Bases: `ABC`

Abstract class for a model.

Source code in `pydantic_ai_slim/pydantic_ai/models/__init__.py`

```python
class Model(ABC):
    """Abstract class for a model."""

    _profile: ModelProfileSpec | None = None
    _settings: ModelSettings | None = None

    def __init__(
        self,
        *,
        settings: ModelSettings | None = None,
        profile: ModelProfileSpec | None = None,
    ) -> None:
        """Initialize the model with optional settings and profile.

        Args:
            settings: Model-specific settings that will be used as defaults for this model.
            profile: The model profile to use.
        """
        self._settings = settings
        self._profile = profile

    @property
    def settings(self) -> ModelSettings | None:
        """Get the model settings."""
        return self._settings

    @abstractmethod
    async def request(
        self,
        messages: list[ModelMessage],
        model_settings: ModelSettings | None,
        model_request_parameters: ModelRequestParameters,
    ) -> ModelResponse:
        """Make a request to the model.

        This is ultimately called by `pydantic_ai._agent_graph.ModelRequestNode._make_request(...)`.
        """
        raise NotImplementedError()

    async def count_tokens(
        self,
        messages: list[ModelMessage],
        model_settings: ModelSettings | None,
        model_request_parameters: ModelRequestParameters,
    ) -> RequestUsage:
        """Make a request to the model for counting tokens."""
        # This method is not required, but you need to implement it if you want to support `UsageLimits.count_tokens_before_request`.
        raise NotImplementedError(f'Token counting ahead of the request is not supported by {self.__class__.__name__}')

    @asynccontextmanager
    async def request_stream(
        self,
        messages: list[ModelMessage],
        model_settings: ModelSettings | None,
        model_request_parameters: ModelRequestParameters,
        run_context: RunContext[Any] | None = None,
    ) -> AsyncIterator[StreamedResponse]:
        """Make a request to the model and return a streaming response."""
        # This method is not required, but you need to implement it if you want to support streamed responses
        raise NotImplementedError(f'Streamed requests not supported by this {self.__class__.__name__}')
        # yield is required to make this a generator for type checking
        # noinspection PyUnreachableCode
        yield  # pragma: no cover

    def customize_request_parameters(self, model_request_parameters: ModelRequestParameters) -> ModelRequestParameters:
        """Customize the request parameters for the model.

        This method can be overridden by subclasses to modify the request parameters before sending them to the model.
        In particular, this method can be used to make modifications to the generated tool JSON schemas if necessary
        for vendor/model-specific reasons.
        """
        if transformer := self.profile.json_schema_transformer:
            model_request_parameters = replace(
                model_request_parameters,
                function_tools=[_customize_tool_def(transformer, t) for t in model_request_parameters.function_tools],
                output_tools=[_customize_tool_def(transformer, t) for t in model_request_parameters.output_tools],
            )
            if output_object := model_request_parameters.output_object:
                model_request_parameters = replace(
                    model_request_parameters,
                    output_object=_customize_output_object(transformer, output_object),
                )

        return model_request_parameters

    def prepare_request(
        self,
        model_settings: ModelSettings | None,
        model_request_parameters: ModelRequestParameters,
    ) -> tuple[ModelSettings | None, ModelRequestParameters]:
        """Prepare request inputs before they are passed to the provider.

        This merges the given `model_settings` with the model's own `settings` attribute and ensures
        `customize_request_parameters` is applied to the resolved
        [`ModelRequestParameters`][pydantic_ai.models.ModelRequestParameters]. Subclasses can override this method if
        they need to customize the preparation flow further, but most implementations should simply call
        `self.prepare_request(...)` at the start of their `request` (and related) methods.
        """
        model_settings = merge_model_settings(self.settings, model_settings)

        params = self.customize_request_parameters(model_request_parameters)

        if builtin_tools := params.builtin_tools:
            # Deduplicate builtin tools
            params = replace(
                params,
                builtin_tools=list({tool.unique_id: tool for tool in builtin_tools}.values()),
            )

        if params.output_mode == 'auto':
            output_mode = self.profile.default_structured_output_mode
            params = replace(
                params,
                output_mode=output_mode,
                allow_text_output=output_mode in ('native', 'prompted'),
            )

        # Reset irrelevant fields
        if params.output_tools and params.output_mode != 'tool':
            params = replace(params, output_tools=[])
        if params.output_object and params.output_mode not in ('native', 'prompted'):
            params = replace(params, output_object=None)
        if params.prompted_output_template and params.output_mode != 'prompted':
            params = replace(params, prompted_output_template=None)  # pragma: no cover

        # Set default prompted output template
        if params.output_mode == 'prompted' and not params.prompted_output_template:
            params = replace(params, prompted_output_template=self.profile.prompted_output_template)

        # Check if output mode is supported
        if params.output_mode == 'native' and not self.profile.supports_json_schema_output:
            raise UserError('Native structured output is not supported by this model.')
        if params.output_mode == 'tool' and not self.profile.supports_tools:
            raise UserError('Tool output is not supported by this model.')
        if params.allow_image_output and not self.profile.supports_image_output:
            raise UserError('Image output is not supported by this model.')

        return model_settings, params

    @property
    @abstractmethod
    def model_name(self) -> str:
        """The model name."""
        raise NotImplementedError()

    @cached_property
    def profile(self) -> ModelProfile:
        """The model profile."""
        _profile = self._profile
        if callable(_profile):
            _profile = _profile(self.model_name)

        if _profile is None:
            return DEFAULT_PROFILE

        return _profile

    @property
    @abstractmethod
    def system(self) -> str:
        """The model provider, ex: openai.

        Use to populate the `gen_ai.system` OpenTelemetry semantic convention attribute,
        so should use well-known values listed in
        https://opentelemetry.io/docs/specs/semconv/attributes-registry/gen-ai/#gen-ai-system
        when applicable.
        """
        raise NotImplementedError()

    @property
    def base_url(self) -> str | None:
        """The base URL for the provider API, if available."""
        return None

    @staticmethod
    def _get_instructions(
        messages: list[ModelMessage], model_request_parameters: ModelRequestParameters | None = None
    ) -> str | None:
        """Get instructions from the first ModelRequest found when iterating messages in reverse.

        In the case that a "mock" request was generated to include a tool-return part for a result tool,
        we want to use the instructions from the second-to-most-recent request (which should correspond to the
        original request that generated the response that resulted in the tool-return part).
        """
        instructions = None

        last_two_requests: list[ModelRequest] = []
        for message in reversed(messages):
            if isinstance(message, ModelRequest):
                last_two_requests.append(message)
                if len(last_two_requests) == 2:
                    break
                if message.instructions is not None:
                    instructions = message.instructions
                    break

        # If we don't have two requests, and we didn't already return instructions, there are definitely not any:
        if instructions is None and len(last_two_requests) == 2:
            most_recent_request = last_two_requests[0]
            second_most_recent_request = last_two_requests[1]

            # If we've gotten this far and the most recent request consists of only tool-return parts or retry-prompt parts,
            # we use the instructions from the second-to-most-recent request. This is necessary because when handling
            # result tools, we generate a "mock" ModelRequest with a tool-return part for it, and that ModelRequest will not
            # have the relevant instructions from the agent.

            # While it's possible that you could have a message history where the most recent request has only tool returns,
            # I believe there is no way to achieve that would _change_ the instructions without manually crafting the most
            # recent message. That might make sense in principle for some usage pattern, but it's enough of an edge case
            # that I think it's not worth worrying about, since you can work around this by inserting another ModelRequest
            # with no parts at all immediately before the request that has the tool calls (that works because we only look
            # at the two most recent ModelRequests here).

            # If you have a use case where this causes pain, please open a GitHub issue and we can discuss alternatives.

            if all(p.part_kind == 'tool-return' or p.part_kind == 'retry-prompt' for p in most_recent_request.parts):
                instructions = second_most_recent_request.instructions

        if model_request_parameters and (output_instructions := model_request_parameters.prompted_output_instructions):
            if instructions:
                instructions = '\n\n'.join([instructions, output_instructions])
            else:
                instructions = output_instructions

        return instructions

```

#### **init**

```python
__init__(
    *,
    settings: ModelSettings | None = None,
    profile: ModelProfileSpec | None = None
) -> None

```

Initialize the model with optional settings and profile.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `settings` | `ModelSettings | None` | Model-specific settings that will be used as defaults for this model. | `None` | | `profile` | `ModelProfileSpec | None` | The model profile to use. | `None` |

Source code in `pydantic_ai_slim/pydantic_ai/models/__init__.py`

```python
def __init__(
    self,
    *,
    settings: ModelSettings | None = None,
    profile: ModelProfileSpec | None = None,
) -> None:
    """Initialize the model with optional settings and profile.

    Args:
        settings: Model-specific settings that will be used as defaults for this model.
        profile: The model profile to use.
    """
    self._settings = settings
    self._profile = profile

```

#### settings

```python
settings: ModelSettings | None

```

Get the model settings.

#### request

```python
request(
    messages: list[ModelMessage],
    model_settings: ModelSettings | None,
    model_request_parameters: ModelRequestParameters,
) -> ModelResponse

```

Make a request to the model.

This is ultimately called by `pydantic_ai._agent_graph.ModelRequestNode._make_request(...)`.

Source code in `pydantic_ai_slim/pydantic_ai/models/__init__.py`

```python
@abstractmethod
async def request(
    self,
    messages: list[ModelMessage],
    model_settings: ModelSettings | None,
    model_request_parameters: ModelRequestParameters,
) -> ModelResponse:
    """Make a request to the model.

    This is ultimately called by `pydantic_ai._agent_graph.ModelRequestNode._make_request(...)`.
    """
    raise NotImplementedError()

```

#### count_tokens

```python
count_tokens(
    messages: list[ModelMessage],
    model_settings: ModelSettings | None,
    model_request_parameters: ModelRequestParameters,
) -> RequestUsage

```

Make a request to the model for counting tokens.

Source code in `pydantic_ai_slim/pydantic_ai/models/__init__.py`

```python
async def count_tokens(
    self,
    messages: list[ModelMessage],
    model_settings: ModelSettings | None,
    model_request_parameters: ModelRequestParameters,
) -> RequestUsage:
    """Make a request to the model for counting tokens."""
    # This method is not required, but you need to implement it if you want to support `UsageLimits.count_tokens_before_request`.
    raise NotImplementedError(f'Token counting ahead of the request is not supported by {self.__class__.__name__}')

```

#### request_stream

```python
request_stream(
    messages: list[ModelMessage],
    model_settings: ModelSettings | None,
    model_request_parameters: ModelRequestParameters,
    run_context: RunContext[Any] | None = None,
) -> AsyncIterator[StreamedResponse]

```

Make a request to the model and return a streaming response.

Source code in `pydantic_ai_slim/pydantic_ai/models/__init__.py`

```python
@asynccontextmanager
async def request_stream(
    self,
    messages: list[ModelMessage],
    model_settings: ModelSettings | None,
    model_request_parameters: ModelRequestParameters,
    run_context: RunContext[Any] | None = None,
) -> AsyncIterator[StreamedResponse]:
    """Make a request to the model and return a streaming response."""
    # This method is not required, but you need to implement it if you want to support streamed responses
    raise NotImplementedError(f'Streamed requests not supported by this {self.__class__.__name__}')
    # yield is required to make this a generator for type checking
    # noinspection PyUnreachableCode
    yield  # pragma: no cover

```

#### customize_request_parameters

```python
customize_request_parameters(
    model_request_parameters: ModelRequestParameters,
) -> ModelRequestParameters

```

Customize the request parameters for the model.

This method can be overridden by subclasses to modify the request parameters before sending them to the model. In particular, this method can be used to make modifications to the generated tool JSON schemas if necessary for vendor/model-specific reasons.

Source code in `pydantic_ai_slim/pydantic_ai/models/__init__.py`

```python
def customize_request_parameters(self, model_request_parameters: ModelRequestParameters) -> ModelRequestParameters:
    """Customize the request parameters for the model.

    This method can be overridden by subclasses to modify the request parameters before sending them to the model.
    In particular, this method can be used to make modifications to the generated tool JSON schemas if necessary
    for vendor/model-specific reasons.
    """
    if transformer := self.profile.json_schema_transformer:
        model_request_parameters = replace(
            model_request_parameters,
            function_tools=[_customize_tool_def(transformer, t) for t in model_request_parameters.function_tools],
            output_tools=[_customize_tool_def(transformer, t) for t in model_request_parameters.output_tools],
        )
        if output_object := model_request_parameters.output_object:
            model_request_parameters = replace(
                model_request_parameters,
                output_object=_customize_output_object(transformer, output_object),
            )

    return model_request_parameters

```

#### prepare_request

```python
prepare_request(
    model_settings: ModelSettings | None,
    model_request_parameters: ModelRequestParameters,
) -> tuple[ModelSettings | None, ModelRequestParameters]

```

Prepare request inputs before they are passed to the provider.

This merges the given `model_settings` with the model's own `settings` attribute and ensures `customize_request_parameters` is applied to the resolved ModelRequestParameters. Subclasses can override this method if they need to customize the preparation flow further, but most implementations should simply call `self.prepare_request(...)` at the start of their `request` (and related) methods.

Source code in `pydantic_ai_slim/pydantic_ai/models/__init__.py`

```python
def prepare_request(
    self,
    model_settings: ModelSettings | None,
    model_request_parameters: ModelRequestParameters,
) -> tuple[ModelSettings | None, ModelRequestParameters]:
    """Prepare request inputs before they are passed to the provider.

    This merges the given `model_settings` with the model's own `settings` attribute and ensures
    `customize_request_parameters` is applied to the resolved
    [`ModelRequestParameters`][pydantic_ai.models.ModelRequestParameters]. Subclasses can override this method if
    they need to customize the preparation flow further, but most implementations should simply call
    `self.prepare_request(...)` at the start of their `request` (and related) methods.
    """
    model_settings = merge_model_settings(self.settings, model_settings)

    params = self.customize_request_parameters(model_request_parameters)

    if builtin_tools := params.builtin_tools:
        # Deduplicate builtin tools
        params = replace(
            params,
            builtin_tools=list({tool.unique_id: tool for tool in builtin_tools}.values()),
        )

    if params.output_mode == 'auto':
        output_mode = self.profile.default_structured_output_mode
        params = replace(
            params,
            output_mode=output_mode,
            allow_text_output=output_mode in ('native', 'prompted'),
        )

    # Reset irrelevant fields
    if params.output_tools and params.output_mode != 'tool':
        params = replace(params, output_tools=[])
    if params.output_object and params.output_mode not in ('native', 'prompted'):
        params = replace(params, output_object=None)
    if params.prompted_output_template and params.output_mode != 'prompted':
        params = replace(params, prompted_output_template=None)  # pragma: no cover

    # Set default prompted output template
    if params.output_mode == 'prompted' and not params.prompted_output_template:
        params = replace(params, prompted_output_template=self.profile.prompted_output_template)

    # Check if output mode is supported
    if params.output_mode == 'native' and not self.profile.supports_json_schema_output:
        raise UserError('Native structured output is not supported by this model.')
    if params.output_mode == 'tool' and not self.profile.supports_tools:
        raise UserError('Tool output is not supported by this model.')
    if params.allow_image_output and not self.profile.supports_image_output:
        raise UserError('Image output is not supported by this model.')

    return model_settings, params

```

#### model_name

```python
model_name: str

```

The model name.

#### profile

```python
profile: ModelProfile

```

The model profile.

#### system

```python
system: str

```

The model provider, ex: openai.

Use to populate the `gen_ai.system` OpenTelemetry semantic convention attribute, so should use well-known values listed in https://opentelemetry.io/docs/specs/semconv/attributes-registry/gen-ai/#gen-ai-system when applicable.

#### base_url

```python
base_url: str | None

```

The base URL for the provider API, if available.
