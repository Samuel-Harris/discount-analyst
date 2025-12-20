### OpenRouterModel

Bases: `OpenAIChatModel`

Extends OpenAIModel to capture extra metadata for Openrouter.

Source code in `pydantic_ai_slim/pydantic_ai/models/openrouter.py`

```python
class OpenRouterModel(OpenAIChatModel):
    """Extends OpenAIModel to capture extra metadata for Openrouter."""

    def __init__(
        self,
        model_name: str,
        *,
        provider: Literal['openrouter'] | Provider[AsyncOpenAI] = 'openrouter',
        profile: ModelProfileSpec | None = None,
        settings: ModelSettings | None = None,
    ):
        """Initialize an OpenRouter model.

        Args:
            model_name: The name of the model to use.
            provider: The provider to use for authentication and API access. If not provided, a new provider will be created with the default settings.
            profile: The model profile to use. Defaults to a profile picked by the provider based on the model name.
            settings: Model-specific settings that will be used as defaults for this model.
        """
        super().__init__(model_name, provider=provider or OpenRouterProvider(), profile=profile, settings=settings)

    @override
    def prepare_request(
        self,
        model_settings: ModelSettings | None,
        model_request_parameters: ModelRequestParameters,
    ) -> tuple[ModelSettings | None, ModelRequestParameters]:
        merged_settings, customized_parameters = super().prepare_request(model_settings, model_request_parameters)
        new_settings = _openrouter_settings_to_openai_settings(cast(OpenRouterModelSettings, merged_settings or {}))
        return new_settings, customized_parameters

    @override
    def _validate_completion(self, response: chat.ChatCompletion) -> _OpenRouterChatCompletion:
        response = _OpenRouterChatCompletion.model_validate(response.model_dump())

        if error := response.error:
            raise ModelHTTPError(status_code=error.code, model_name=response.model, body=error.message)

        return response

    @override
    def _process_thinking(self, message: chat.ChatCompletionMessage) -> list[ThinkingPart] | None:
        assert isinstance(message, _OpenRouterCompletionMessage)

        if reasoning_details := message.reasoning_details:
            return [_from_reasoning_detail(detail) for detail in reasoning_details]
        else:
            return super()._process_thinking(message)

    @override
    def _process_provider_details(self, response: chat.ChatCompletion) -> dict[str, Any]:
        assert isinstance(response, _OpenRouterChatCompletion)

        provider_details = super()._process_provider_details(response)
        provider_details.update(_map_openrouter_provider_details(response))
        return provider_details

    @dataclass
    class _MapModelResponseContext(OpenAIChatModel._MapModelResponseContext):  # type: ignore[reportPrivateUsage]
        reasoning_details: list[dict[str, Any]] = field(default_factory=list)

        def _into_message_param(self) -> chat.ChatCompletionAssistantMessageParam:
            message_param = super()._into_message_param()
            if self.reasoning_details:
                message_param['reasoning_details'] = self.reasoning_details  # type: ignore[reportGeneralTypeIssues]
            return message_param

        @override
        def _map_response_thinking_part(self, item: ThinkingPart) -> None:
            assert isinstance(self._model, OpenRouterModel)
            if item.provider_name == self._model.system:
                if reasoning_detail := _into_reasoning_detail(item):  # pragma: lax no cover
                    self.reasoning_details.append(reasoning_detail.model_dump())
            else:  # pragma: lax no cover
                super()._map_response_thinking_part(item)

    @property
    @override
    def _streamed_response_cls(self):
        return OpenRouterStreamedResponse

    @override
    def _map_finish_reason(  # type: ignore[reportIncompatibleMethodOverride]
        self, key: Literal['stop', 'length', 'tool_calls', 'content_filter', 'error']
    ) -> FinishReason | None:
        return _CHAT_FINISH_REASON_MAP.get(key)

```

#### **init**

```python
__init__(
    model_name: str,
    *,
    provider: (
        Literal["openrouter"] | Provider[AsyncOpenAI]
    ) = "openrouter",
    profile: ModelProfileSpec | None = None,
    settings: ModelSettings | None = None
)

```

Initialize an OpenRouter model.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `model_name` | `str` | The name of the model to use. | _required_ | | `provider` | `Literal['openrouter'] | Provider[AsyncOpenAI]` | The provider to use for authentication and API access. If not provided, a new provider will be created with the default settings. | `'openrouter'` | | `profile` | `ModelProfileSpec | None` | The model profile to use. Defaults to a profile picked by the provider based on the model name. | `None` | | `settings` | `ModelSettings | None` | Model-specific settings that will be used as defaults for this model. | `None` |

Source code in `pydantic_ai_slim/pydantic_ai/models/openrouter.py`

```python
def __init__(
    self,
    model_name: str,
    *,
    provider: Literal['openrouter'] | Provider[AsyncOpenAI] = 'openrouter',
    profile: ModelProfileSpec | None = None,
    settings: ModelSettings | None = None,
):
    """Initialize an OpenRouter model.

    Args:
        model_name: The name of the model to use.
        provider: The provider to use for authentication and API access. If not provided, a new provider will be created with the default settings.
        profile: The model profile to use. Defaults to a profile picked by the provider based on the model name.
        settings: Model-specific settings that will be used as defaults for this model.
    """
    super().__init__(model_name, provider=provider or OpenRouterProvider(), profile=profile, settings=settings)

```
