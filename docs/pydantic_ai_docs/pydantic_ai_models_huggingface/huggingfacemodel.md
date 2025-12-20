### HuggingFaceModel

Bases: `Model`

A model that uses Hugging Face Inference Providers.

Internally, this uses the [HF Python client](https://github.com/huggingface/huggingface_hub) to interact with the API.

Apart from `__init__`, all methods are private or match those of the base class.

Source code in `pydantic_ai_slim/pydantic_ai/models/huggingface.py`

```python
@dataclass(init=False)
class HuggingFaceModel(Model):
    """A model that uses Hugging Face Inference Providers.

    Internally, this uses the [HF Python client](https://github.com/huggingface/huggingface_hub) to interact with the API.

    Apart from `__init__`, all methods are private or match those of the base class.
    """

    client: AsyncInferenceClient = field(repr=False)

    _model_name: str = field(repr=False)
    _provider: Provider[AsyncInferenceClient] = field(repr=False)

    def __init__(
        self,
        model_name: str,
        *,
        provider: Literal['huggingface'] | Provider[AsyncInferenceClient] = 'huggingface',
        profile: ModelProfileSpec | None = None,
        settings: ModelSettings | None = None,
    ):
        """Initialize a Hugging Face model.

        Args:
            model_name: The name of the Model to use. You can browse available models [here](https://huggingface.co/models?pipeline_tag=text-generation&inference_provider=all&sort=trending).
            provider: The provider to use for Hugging Face Inference Providers. Can be either the string 'huggingface' or an
                instance of `Provider[AsyncInferenceClient]`. If not provided, the other parameters will be used.
            profile: The model profile to use. Defaults to a profile picked by the provider based on the model name.
            settings: Model-specific settings that will be used as defaults for this model.
        """
        self._model_name = model_name
        if isinstance(provider, str):
            provider = infer_provider(provider)
        self._provider = provider
        self.client = provider.client

        super().__init__(settings=settings, profile=profile or provider.model_profile)

    @property
    def model_name(self) -> HuggingFaceModelName:
        """The model name."""
        return self._model_name

    @property
    def system(self) -> str:
        """The system / model provider."""
        return self._provider.name

    async def request(
        self,
        messages: list[ModelMessage],
        model_settings: ModelSettings | None,
        model_request_parameters: ModelRequestParameters,
    ) -> ModelResponse:
        check_allow_model_requests()
        model_settings, model_request_parameters = self.prepare_request(
            model_settings,
            model_request_parameters,
        )
        response = await self._completions_create(
            messages, False, cast(HuggingFaceModelSettings, model_settings or {}), model_request_parameters
        )
        model_response = self._process_response(response)
        return model_response

    @asynccontextmanager
    async def request_stream(
        self,
        messages: list[ModelMessage],
        model_settings: ModelSettings | None,
        model_request_parameters: ModelRequestParameters,
        run_context: RunContext[Any] | None = None,
    ) -> AsyncIterator[StreamedResponse]:
        check_allow_model_requests()
        model_settings, model_request_parameters = self.prepare_request(
            model_settings,
            model_request_parameters,
        )
        response = await self._completions_create(
            messages, True, cast(HuggingFaceModelSettings, model_settings or {}), model_request_parameters
        )
        yield await self._process_streamed_response(response, model_request_parameters)

    @overload
    async def _completions_create(
        self,
        messages: list[ModelMessage],
        stream: Literal[True],
        model_settings: HuggingFaceModelSettings,
        model_request_parameters: ModelRequestParameters,
    ) -> AsyncIterable[ChatCompletionStreamOutput]: ...

    @overload
    async def _completions_create(
        self,
        messages: list[ModelMessage],
        stream: Literal[False],
        model_settings: HuggingFaceModelSettings,
        model_request_parameters: ModelRequestParameters,
    ) -> ChatCompletionOutput: ...

    async def _completions_create(
        self,
        messages: list[ModelMessage],
        stream: bool,
        model_settings: HuggingFaceModelSettings,
        model_request_parameters: ModelRequestParameters,
    ) -> ChatCompletionOutput | AsyncIterable[ChatCompletionStreamOutput]:
        tools = self._get_tools(model_request_parameters)

        if not tools:
            tool_choice: Literal['none', 'required', 'auto'] | None = None
        elif not model_request_parameters.allow_text_output:
            tool_choice = 'required'
        else:
            tool_choice = 'auto'

        if model_request_parameters.builtin_tools:
            raise UserError('HuggingFace does not support built-in tools')

        hf_messages = await self._map_messages(messages, model_request_parameters)

        try:
            return await self.client.chat.completions.create(  # type: ignore
                model=self._model_name,
                messages=hf_messages,  # type: ignore
                tools=tools,
                tool_choice=tool_choice or None,
                stream=stream,
                stop=model_settings.get('stop_sequences', None),
                temperature=model_settings.get('temperature', None),
                top_p=model_settings.get('top_p', None),
                seed=model_settings.get('seed', None),
                presence_penalty=model_settings.get('presence_penalty', None),
                frequency_penalty=model_settings.get('frequency_penalty', None),
                logit_bias=model_settings.get('logit_bias', None),  # type: ignore
                logprobs=model_settings.get('logprobs', None),
                top_logprobs=model_settings.get('top_logprobs', None),
                extra_body=model_settings.get('extra_body'),  # type: ignore
            )
        except aiohttp.ClientResponseError as e:
            raise ModelHTTPError(
                status_code=e.status,
                model_name=self.model_name,
                body=e.message,
            ) from e
        except HfHubHTTPError as e:
            raise ModelHTTPError(
                status_code=e.response.status_code,
                model_name=self.model_name,
                body=e.response.content,
            ) from e

    def _process_response(self, response: ChatCompletionOutput) -> ModelResponse:
        """Process a non-streamed response, and prepare a message to return."""
        if response.created:
            timestamp = datetime.fromtimestamp(response.created, tz=timezone.utc)
        else:
            timestamp = _now_utc()

        choice = response.choices[0]
        content = choice.message.content
        tool_calls = choice.message.tool_calls

        items: list[ModelResponsePart] = []

        if content:
            items.extend(split_content_into_text_and_thinking(content, self.profile.thinking_tags))
        if tool_calls is not None:
            for c in tool_calls:
                items.append(ToolCallPart(c.function.name, c.function.arguments, tool_call_id=c.id))

        raw_finish_reason = choice.finish_reason
        provider_details = {'finish_reason': raw_finish_reason}
        finish_reason = _FINISH_REASON_MAP.get(cast(TextGenerationOutputFinishReason, raw_finish_reason), None)

        return ModelResponse(
            parts=items,
            usage=_map_usage(response),
            model_name=response.model,
            timestamp=timestamp,
            provider_response_id=response.id,
            provider_name=self._provider.name,
            finish_reason=finish_reason,
            provider_details=provider_details,
        )

    async def _process_streamed_response(
        self, response: AsyncIterable[ChatCompletionStreamOutput], model_request_parameters: ModelRequestParameters
    ) -> StreamedResponse:
        """Process a streamed response, and prepare a streaming response to return."""
        peekable_response = _utils.PeekableAsyncStream(response)
        first_chunk = await peekable_response.peek()
        if isinstance(first_chunk, _utils.Unset):
            raise UnexpectedModelBehavior(  # pragma: no cover
                'Streamed response ended without content or tool calls'
            )

        return HuggingFaceStreamedResponse(
            model_request_parameters=model_request_parameters,
            _model_name=first_chunk.model,
            _model_profile=self.profile,
            _response=peekable_response,
            _timestamp=datetime.fromtimestamp(first_chunk.created, tz=timezone.utc),
            _provider_name=self._provider.name,
        )

    def _get_tools(self, model_request_parameters: ModelRequestParameters) -> list[ChatCompletionInputTool]:
        return [self._map_tool_definition(r) for r in model_request_parameters.tool_defs.values()]

    async def _map_messages(
        self, messages: list[ModelMessage], model_request_parameters: ModelRequestParameters
    ) -> list[ChatCompletionInputMessage | ChatCompletionOutputMessage]:
        """Just maps a `pydantic_ai.Message` to a `huggingface_hub.ChatCompletionInputMessage`."""
        hf_messages: list[ChatCompletionInputMessage | ChatCompletionOutputMessage] = []
        for message in messages:
            if isinstance(message, ModelRequest):
                async for item in self._map_user_message(message):
                    hf_messages.append(item)
            elif isinstance(message, ModelResponse):
                texts: list[str] = []
                tool_calls: list[ChatCompletionInputToolCall] = []
                for item in message.parts:
                    if isinstance(item, TextPart):
                        texts.append(item.content)
                    elif isinstance(item, ToolCallPart):
                        tool_calls.append(self._map_tool_call(item))
                    elif isinstance(item, ThinkingPart):
                        start_tag, end_tag = self.profile.thinking_tags
                        texts.append('\n'.join([start_tag, item.content, end_tag]))
                    elif isinstance(item, BuiltinToolCallPart | BuiltinToolReturnPart):  # pragma: no cover
                        # This is currently never returned from huggingface
                        pass
                    elif isinstance(item, FilePart):  # pragma: no cover
                        # Files generated by models are not sent back to models that don't themselves generate files.
                        pass
                    else:
                        assert_never(item)
                message_param = ChatCompletionInputMessage(role='assistant')  # type: ignore
                if texts:
                    # Note: model responses from this model should only have one text item, so the following
                    # shouldn't merge multiple texts into one unless you switch models between runs:
                    message_param['content'] = '\n\n'.join(texts)
                if tool_calls:
                    message_param['tool_calls'] = tool_calls
                hf_messages.append(message_param)
            else:
                assert_never(message)
        if instructions := self._get_instructions(messages, model_request_parameters):
            hf_messages.insert(0, ChatCompletionInputMessage(content=instructions, role='system'))  # type: ignore
        return hf_messages

    @staticmethod
    def _map_tool_call(t: ToolCallPart) -> ChatCompletionInputToolCall:
        return ChatCompletionInputToolCall.parse_obj_as_instance(  # type: ignore
            {
                'id': _guard_tool_call_id(t=t),
                'type': 'function',
                'function': {
                    'name': t.tool_name,
                    'arguments': t.args_as_json_str(),
                },
            }
        )

    @staticmethod
    def _map_tool_definition(f: ToolDefinition) -> ChatCompletionInputTool:
        tool_param: ChatCompletionInputTool = ChatCompletionInputTool.parse_obj_as_instance(  # type: ignore
            {
                'type': 'function',
                'function': {
                    'name': f.name,
                    'description': f.description,
                    'parameters': f.parameters_json_schema,
                },
            }
        )
        return tool_param

    async def _map_user_message(
        self, message: ModelRequest
    ) -> AsyncIterable[ChatCompletionInputMessage | ChatCompletionOutputMessage]:
        for part in message.parts:
            if isinstance(part, SystemPromptPart):
                yield ChatCompletionInputMessage.parse_obj_as_instance({'role': 'system', 'content': part.content})  # type: ignore
            elif isinstance(part, UserPromptPart):
                yield await self._map_user_prompt(part)
            elif isinstance(part, ToolReturnPart):
                yield ChatCompletionOutputMessage.parse_obj_as_instance(  # type: ignore
                    {
                        'role': 'tool',
                        'tool_call_id': _guard_tool_call_id(t=part),
                        'content': part.model_response_str(),
                    }
                )
            elif isinstance(part, RetryPromptPart):
                if part.tool_name is None:
                    yield ChatCompletionInputMessage.parse_obj_as_instance(  # type: ignore
                        {'role': 'user', 'content': part.model_response()}
                    )
                else:
                    yield ChatCompletionInputMessage.parse_obj_as_instance(  # type: ignore
                        {
                            'role': 'tool',
                            'tool_call_id': _guard_tool_call_id(t=part),
                            'content': part.model_response(),
                        }
                    )
            else:
                assert_never(part)

    @staticmethod
    async def _map_user_prompt(part: UserPromptPart) -> ChatCompletionInputMessage:
        content: str | list[ChatCompletionInputMessage]
        if isinstance(part.content, str):
            content = part.content
        else:
            content = []
            for item in part.content:
                if isinstance(item, str):
                    content.append(ChatCompletionInputMessageChunk(type='text', text=item))  # type: ignore
                elif isinstance(item, ImageUrl):
                    url = ChatCompletionInputURL(url=item.url)  # type: ignore
                    content.append(ChatCompletionInputMessageChunk(type='image_url', image_url=url))  # type: ignore
                elif isinstance(item, BinaryContent):
                    if item.is_image:
                        url = ChatCompletionInputURL(url=item.data_uri)  # type: ignore
                        content.append(ChatCompletionInputMessageChunk(type='image_url', image_url=url))  # type: ignore
                    else:  # pragma: no cover
                        raise RuntimeError(f'Unsupported binary content type: {item.media_type}')
                elif isinstance(item, AudioUrl):
                    raise NotImplementedError('AudioUrl is not supported for Hugging Face')
                elif isinstance(item, DocumentUrl):
                    raise NotImplementedError('DocumentUrl is not supported for Hugging Face')
                elif isinstance(item, VideoUrl):
                    raise NotImplementedError('VideoUrl is not supported for Hugging Face')
                elif isinstance(item, CachePoint):
                    # Hugging Face doesn't support prompt caching via CachePoint
                    pass
                else:
                    assert_never(item)
        return ChatCompletionInputMessage(role='user', content=content)  # type: ignore

```

#### **init**

```python
__init__(
    model_name: str,
    *,
    provider: (
        Literal["huggingface"]
        | Provider[AsyncInferenceClient]
    ) = "huggingface",
    profile: ModelProfileSpec | None = None,
    settings: ModelSettings | None = None
)

```

Initialize a Hugging Face model.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `model_name` | `str` | The name of the Model to use. You can browse available models here. | _required_ | | `provider` | `Literal['huggingface'] | Provider[AsyncInferenceClient]` | The provider to use for Hugging Face Inference Providers. Can be either the string 'huggingface' or an instance of Provider[AsyncInferenceClient]. If not provided, the other parameters will be used. | `'huggingface'` | | `profile` | `ModelProfileSpec | None` | The model profile to use. Defaults to a profile picked by the provider based on the model name. | `None` | | `settings` | `ModelSettings | None` | Model-specific settings that will be used as defaults for this model. | `None` |

Source code in `pydantic_ai_slim/pydantic_ai/models/huggingface.py`

```python
def __init__(
    self,
    model_name: str,
    *,
    provider: Literal['huggingface'] | Provider[AsyncInferenceClient] = 'huggingface',
    profile: ModelProfileSpec | None = None,
    settings: ModelSettings | None = None,
):
    """Initialize a Hugging Face model.

    Args:
        model_name: The name of the Model to use. You can browse available models [here](https://huggingface.co/models?pipeline_tag=text-generation&inference_provider=all&sort=trending).
        provider: The provider to use for Hugging Face Inference Providers. Can be either the string 'huggingface' or an
            instance of `Provider[AsyncInferenceClient]`. If not provided, the other parameters will be used.
        profile: The model profile to use. Defaults to a profile picked by the provider based on the model name.
        settings: Model-specific settings that will be used as defaults for this model.
    """
    self._model_name = model_name
    if isinstance(provider, str):
        provider = infer_provider(provider)
    self._provider = provider
    self.client = provider.client

    super().__init__(settings=settings, profile=profile or provider.model_profile)

```

#### model_name

```python
model_name: HuggingFaceModelName

```

The model name.

#### system

```python
system: str

```

The system / model provider.
