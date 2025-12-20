### OpenAIResponsesModel

Bases: `Model`

A model that uses the OpenAI Responses API.

The [OpenAI Responses API](https://platform.openai.com/docs/api-reference/responses) is the new API for OpenAI models.

If you are interested in the differences between the Responses API and the Chat Completions API, see the [OpenAI API docs](https://platform.openai.com/docs/guides/responses-vs-chat-completions).

Source code in `pydantic_ai_slim/pydantic_ai/models/openai.py`

```python
@dataclass(init=False)
class OpenAIResponsesModel(Model):
    """A model that uses the OpenAI Responses API.

    The [OpenAI Responses API](https://platform.openai.com/docs/api-reference/responses) is the
    new API for OpenAI models.

    If you are interested in the differences between the Responses API and the Chat Completions API,
    see the [OpenAI API docs](https://platform.openai.com/docs/guides/responses-vs-chat-completions).
    """

    client: AsyncOpenAI = field(repr=False)

    _model_name: OpenAIModelName = field(repr=False)
    _provider: Provider[AsyncOpenAI] = field(repr=False)

    def __init__(
        self,
        model_name: OpenAIModelName,
        *,
        provider: Literal[
            'openai',
            'deepseek',
            'azure',
            'openrouter',
            'grok',
            'fireworks',
            'together',
            'nebius',
            'ovhcloud',
            'gateway',
        ]
        | Provider[AsyncOpenAI] = 'openai',
        profile: ModelProfileSpec | None = None,
        settings: ModelSettings | None = None,
    ):
        """Initialize an OpenAI Responses model.

        Args:
            model_name: The name of the OpenAI model to use.
            provider: The provider to use. Defaults to `'openai'`.
            profile: The model profile to use. Defaults to a profile picked by the provider based on the model name.
            settings: Default model settings for this model instance.
        """
        self._model_name = model_name

        if isinstance(provider, str):
            provider = infer_provider('gateway/openai' if provider == 'gateway' else provider)
        self._provider = provider
        self.client = provider.client

        super().__init__(settings=settings, profile=profile or provider.model_profile)

    @property
    def base_url(self) -> str:
        return str(self.client.base_url)

    @property
    def model_name(self) -> OpenAIModelName:
        """The model name."""
        return self._model_name

    @property
    def system(self) -> str:
        """The model provider."""
        return self._provider.name

    async def request(
        self,
        messages: list[ModelRequest | ModelResponse],
        model_settings: ModelSettings | None,
        model_request_parameters: ModelRequestParameters,
    ) -> ModelResponse:
        check_allow_model_requests()
        model_settings, model_request_parameters = self.prepare_request(
            model_settings,
            model_request_parameters,
        )
        response = await self._responses_create(
            messages, False, cast(OpenAIResponsesModelSettings, model_settings or {}), model_request_parameters
        )
        return self._process_response(response, model_request_parameters)

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
        response = await self._responses_create(
            messages, True, cast(OpenAIResponsesModelSettings, model_settings or {}), model_request_parameters
        )
        async with response:
            yield await self._process_streamed_response(response, model_request_parameters)

    def _process_response(  # noqa: C901
        self, response: responses.Response, model_request_parameters: ModelRequestParameters
    ) -> ModelResponse:
        """Process a non-streamed response, and prepare a message to return."""
        timestamp = number_to_datetime(response.created_at)
        items: list[ModelResponsePart] = []
        for item in response.output:
            if isinstance(item, responses.ResponseReasoningItem):
                signature = item.encrypted_content
                # Handle raw CoT content from gpt-oss models
                raw_content: list[str] | None = [c.text for c in item.content] if item.content else None
                provider_details: dict[str, Any] | None = {'raw_content': raw_content} if raw_content else None

                if item.summary:
                    for summary in item.summary:
                        # We use the same id for all summaries so that we can merge them on the round trip.
                        items.append(
                            ThinkingPart(
                                content=summary.text,
                                id=item.id,
                                signature=signature,
                                provider_name=self.system if (signature or provider_details) else None,
                                provider_details=provider_details,
                            )
                        )
                        # We only need to store the signature and raw_content once.
                        signature = None
                        provider_details = None
                elif signature or provider_details:
                    items.append(
                        ThinkingPart(
                            content='',
                            id=item.id,
                            signature=signature,
                            provider_name=self.system if (signature or provider_details) else None,
                            provider_details=provider_details,
                        )
                    )
            elif isinstance(item, responses.ResponseOutputMessage):
                for content in item.content:
                    if isinstance(content, responses.ResponseOutputText):  # pragma: no branch
                        part_provider_details: dict[str, Any] | None = None
                        if content.logprobs:
                            part_provider_details = {'logprobs': _map_logprobs(content.logprobs)}
                        items.append(TextPart(content.text, id=item.id, provider_details=part_provider_details))
            elif isinstance(item, responses.ResponseFunctionToolCall):
                items.append(
                    ToolCallPart(
                        item.name,
                        item.arguments,
                        tool_call_id=item.call_id,
                        id=item.id,
                    )
                )
            elif isinstance(item, responses.ResponseCodeInterpreterToolCall):
                call_part, return_part, file_parts = _map_code_interpreter_tool_call(item, self.system)
                items.append(call_part)
                if file_parts:
                    items.extend(file_parts)
                items.append(return_part)
            elif isinstance(item, responses.ResponseFunctionWebSearch):
                call_part, return_part = _map_web_search_tool_call(item, self.system)
                items.append(call_part)
                items.append(return_part)
            elif isinstance(item, responses.response_output_item.ImageGenerationCall):
                call_part, return_part, file_part = _map_image_generation_tool_call(item, self.system)
                items.append(call_part)
                if file_part:  # pragma: no branch
                    items.append(file_part)
                items.append(return_part)
            elif isinstance(item, responses.ResponseComputerToolCall):  # pragma: no cover
                # Pydantic AI doesn't yet support the ComputerUse built-in tool
                pass
            elif isinstance(item, responses.ResponseCustomToolCall):  # pragma: no cover
                # Support is being implemented in https://github.com/pydantic/pydantic-ai/pull/2572
                pass
            elif isinstance(item, responses.response_output_item.LocalShellCall):  # pragma: no cover
                # Pydantic AI doesn't yet support the `codex-mini-latest` LocalShell built-in tool
                pass
            elif isinstance(item, responses.ResponseFileSearchToolCall):  # pragma: no cover
                # Pydantic AI doesn't yet support the FileSearch built-in tool
                pass
            elif isinstance(item, responses.response_output_item.McpCall):
                call_part, return_part = _map_mcp_call(item, self.system)
                items.append(call_part)
                items.append(return_part)
            elif isinstance(item, responses.response_output_item.McpListTools):
                call_part, return_part = _map_mcp_list_tools(item, self.system)
                items.append(call_part)
                items.append(return_part)
            elif isinstance(item, responses.response_output_item.McpApprovalRequest):  # pragma: no cover
                # Pydantic AI doesn't yet support McpApprovalRequest (explicit tool usage approval)
                pass

        finish_reason: FinishReason | None = None
        provider_details: dict[str, Any] | None = None
        raw_finish_reason = details.reason if (details := response.incomplete_details) else response.status
        if raw_finish_reason:
            provider_details = {'finish_reason': raw_finish_reason}
            finish_reason = _RESPONSES_FINISH_REASON_MAP.get(raw_finish_reason)

        return ModelResponse(
            parts=items,
            usage=_map_usage(response, self._provider.name, self._provider.base_url, self.model_name),
            model_name=response.model,
            provider_response_id=response.id,
            timestamp=timestamp,
            provider_name=self._provider.name,
            finish_reason=finish_reason,
            provider_details=provider_details,
        )

    async def _process_streamed_response(
        self,
        response: AsyncStream[responses.ResponseStreamEvent],
        model_request_parameters: ModelRequestParameters,
    ) -> OpenAIResponsesStreamedResponse:
        """Process a streamed response, and prepare a streaming response to return."""
        peekable_response = _utils.PeekableAsyncStream(response)
        first_chunk = await peekable_response.peek()
        if isinstance(first_chunk, _utils.Unset):  # pragma: no cover
            raise UnexpectedModelBehavior('Streamed response ended without content or tool calls')

        assert isinstance(first_chunk, responses.ResponseCreatedEvent)
        return OpenAIResponsesStreamedResponse(
            model_request_parameters=model_request_parameters,
            _model_name=first_chunk.response.model,
            _response=peekable_response,
            _timestamp=number_to_datetime(first_chunk.response.created_at),
            _provider_name=self._provider.name,
            _provider_url=self._provider.base_url,
        )

    @overload
    async def _responses_create(
        self,
        messages: list[ModelRequest | ModelResponse],
        stream: Literal[False],
        model_settings: OpenAIResponsesModelSettings,
        model_request_parameters: ModelRequestParameters,
    ) -> responses.Response: ...

    @overload
    async def _responses_create(
        self,
        messages: list[ModelRequest | ModelResponse],
        stream: Literal[True],
        model_settings: OpenAIResponsesModelSettings,
        model_request_parameters: ModelRequestParameters,
    ) -> AsyncStream[responses.ResponseStreamEvent]: ...

    async def _responses_create(  # noqa: C901
        self,
        messages: list[ModelRequest | ModelResponse],
        stream: bool,
        model_settings: OpenAIResponsesModelSettings,
        model_request_parameters: ModelRequestParameters,
    ) -> responses.Response | AsyncStream[responses.ResponseStreamEvent]:
        tools = (
            self._get_builtin_tools(model_request_parameters)
            + list(model_settings.get('openai_builtin_tools', []))
            + self._get_tools(model_request_parameters)
        )
        profile = OpenAIModelProfile.from_profile(self.profile)
        if not tools:
            tool_choice: Literal['none', 'required', 'auto'] | None = None
        elif not model_request_parameters.allow_text_output and profile.openai_supports_tool_choice_required:
            tool_choice = 'required'
        else:
            tool_choice = 'auto'

        previous_response_id = model_settings.get('openai_previous_response_id')
        if previous_response_id == 'auto':
            previous_response_id, messages = self._get_previous_response_id_and_new_messages(messages)

        instructions, openai_messages = await self._map_messages(messages, model_settings, model_request_parameters)
        reasoning = self._get_reasoning(model_settings)

        text: responses.ResponseTextConfigParam | None = None
        if model_request_parameters.output_mode == 'native':
            output_object = model_request_parameters.output_object
            assert output_object is not None
            text = {'format': self._map_json_schema(output_object)}
        elif (
            model_request_parameters.output_mode == 'prompted' and self.profile.supports_json_object_output
        ):  # pragma: no branch
            text = {'format': {'type': 'json_object'}}

            # Without this trick, we'd hit this error:
            # > Response input messages must contain the word 'json' in some form to use 'text.format' of type 'json_object'.
            # Apparently they're only checking input messages for "JSON", not instructions.
            assert isinstance(instructions, str)
            openai_messages.insert(0, responses.EasyInputMessageParam(role='system', content=instructions))
            instructions = OMIT

        if verbosity := model_settings.get('openai_text_verbosity'):
            text = text or {}
            text['verbosity'] = verbosity

        unsupported_model_settings = profile.openai_unsupported_model_settings
        for setting in unsupported_model_settings:
            model_settings.pop(setting, None)

        include: list[responses.ResponseIncludable] = []
        if profile.openai_supports_encrypted_reasoning_content:
            include.append('reasoning.encrypted_content')
        if model_settings.get('openai_include_code_execution_outputs'):
            include.append('code_interpreter_call.outputs')
        if model_settings.get('openai_include_web_search_sources'):
            include.append('web_search_call.action.sources')
        if model_settings.get('openai_logprobs'):
            include.append('message.output_text.logprobs')

        # When there are no input messages and we're not reusing a previous response,
        # the OpenAI API will reject a request without any input,
        # even if there are instructions.
        # To avoid this provide an explicit empty user message.
        if not openai_messages and not previous_response_id:
            openai_messages.append(
                responses.EasyInputMessageParam(
                    role='user',
                    content='',
                )
            )

        try:
            extra_headers = model_settings.get('extra_headers', {})
            extra_headers.setdefault('User-Agent', get_user_agent())
            return await self.client.responses.create(
                input=openai_messages,
                model=self.model_name,
                instructions=instructions,
                parallel_tool_calls=model_settings.get('parallel_tool_calls', OMIT),
                tools=tools or OMIT,
                tool_choice=tool_choice or OMIT,
                max_output_tokens=model_settings.get('max_tokens', OMIT),
                stream=stream,
                temperature=model_settings.get('temperature', OMIT),
                top_p=model_settings.get('top_p', OMIT),
                truncation=model_settings.get('openai_truncation', OMIT),
                timeout=model_settings.get('timeout', NOT_GIVEN),
                service_tier=model_settings.get('openai_service_tier', OMIT),
                previous_response_id=previous_response_id or OMIT,
                top_logprobs=model_settings.get('openai_top_logprobs', OMIT),
                reasoning=reasoning,
                user=model_settings.get('openai_user', OMIT),
                text=text or OMIT,
                include=include or OMIT,
                extra_headers=extra_headers,
                extra_body=model_settings.get('extra_body'),
            )
        except APIStatusError as e:
            if (status_code := e.status_code) >= 400:
                raise ModelHTTPError(status_code=status_code, model_name=self.model_name, body=e.body) from e
            raise  # pragma: lax no cover
        except APIConnectionError as e:
            raise ModelAPIError(model_name=self.model_name, message=e.message) from e

    def _get_reasoning(self, model_settings: OpenAIResponsesModelSettings) -> Reasoning | Omit:
        reasoning_effort = model_settings.get('openai_reasoning_effort', None)
        reasoning_summary = model_settings.get('openai_reasoning_summary', None)
        reasoning_generate_summary = model_settings.get('openai_reasoning_generate_summary', None)

        if reasoning_summary and reasoning_generate_summary:  # pragma: no cover
            raise ValueError('`openai_reasoning_summary` and `openai_reasoning_generate_summary` cannot both be set.')

        if reasoning_generate_summary is not None:  # pragma: no cover
            warnings.warn(
                '`openai_reasoning_generate_summary` is deprecated, use `openai_reasoning_summary` instead',
                DeprecationWarning,
            )
            reasoning_summary = reasoning_generate_summary

        if reasoning_effort is None and reasoning_summary is None:
            return OMIT
        return Reasoning(effort=reasoning_effort, summary=reasoning_summary)

    def _get_tools(self, model_request_parameters: ModelRequestParameters) -> list[responses.FunctionToolParam]:
        return [self._map_tool_definition(r) for r in model_request_parameters.tool_defs.values()]

    def _get_builtin_tools(self, model_request_parameters: ModelRequestParameters) -> list[responses.ToolParam]:
        tools: list[responses.ToolParam] = []
        has_image_generating_tool = False
        for tool in model_request_parameters.builtin_tools:
            if isinstance(tool, WebSearchTool):
                web_search_tool = responses.WebSearchToolParam(
                    type='web_search', search_context_size=tool.search_context_size
                )
                if tool.user_location:
                    web_search_tool['user_location'] = responses.web_search_tool_param.UserLocation(
                        type='approximate', **tool.user_location
                    )
                tools.append(web_search_tool)
            elif isinstance(tool, CodeExecutionTool):
                has_image_generating_tool = True
                tools.append({'type': 'code_interpreter', 'container': {'type': 'auto'}})
            elif isinstance(tool, MCPServerTool):
                mcp_tool = responses.tool_param.Mcp(
                    type='mcp',
                    server_label=tool.id,
                    require_approval='never',
                )

                if tool.authorization_token:  # pragma: no branch
                    mcp_tool['authorization'] = tool.authorization_token

                if tool.allowed_tools is not None:  # pragma: no branch
                    mcp_tool['allowed_tools'] = tool.allowed_tools

                if tool.description:  # pragma: no branch
                    mcp_tool['server_description'] = tool.description

                if tool.headers:  # pragma: no branch
                    mcp_tool['headers'] = tool.headers

                if tool.url.startswith(MCP_SERVER_TOOL_CONNECTOR_URI_SCHEME + ':'):
                    _, connector_id = tool.url.split(':', maxsplit=1)
                    mcp_tool['connector_id'] = connector_id  # pyright: ignore[reportGeneralTypeIssues]
                else:
                    mcp_tool['server_url'] = tool.url

                tools.append(mcp_tool)
            elif isinstance(tool, ImageGenerationTool):  # pragma: no branch
                has_image_generating_tool = True
                tools.append(
                    responses.tool_param.ImageGeneration(
                        type='image_generation',
                        background=tool.background,
                        input_fidelity=tool.input_fidelity,
                        moderation=tool.moderation,
                        output_compression=tool.output_compression,
                        output_format=tool.output_format or 'png',
                        partial_images=tool.partial_images,
                        quality=tool.quality,
                        size=tool.size,
                    )
                )
            else:
                raise UserError(  # pragma: no cover
                    f'`{tool.__class__.__name__}` is not supported by `OpenAIResponsesModel`. If it should be, please file an issue.'
                )

        if model_request_parameters.allow_image_output and not has_image_generating_tool:
            tools.append({'type': 'image_generation'})
        return tools

    def _map_tool_definition(self, f: ToolDefinition) -> responses.FunctionToolParam:
        return {
            'name': f.name,
            'parameters': f.parameters_json_schema,
            'type': 'function',
            'description': f.description,
            'strict': bool(
                f.strict and OpenAIModelProfile.from_profile(self.profile).openai_supports_strict_tool_definition
            ),
        }

    def _get_previous_response_id_and_new_messages(
        self, messages: list[ModelMessage]
    ) -> tuple[str | None, list[ModelMessage]]:
        # When `openai_previous_response_id` is set to 'auto', the most recent
        # `provider_response_id` from the message history is selected and all
        # earlier messages are omitted. This allows the OpenAI SDK to reuse
        # server-side history for efficiency. The returned tuple contains the
        # `previous_response_id` (if found) and the trimmed list of messages.
        previous_response_id = None
        trimmed_messages: list[ModelMessage] = []
        for m in reversed(messages):
            if isinstance(m, ModelResponse) and m.provider_name == self.system:
                previous_response_id = m.provider_response_id
                break
            else:
                trimmed_messages.append(m)

        if previous_response_id and trimmed_messages:
            return previous_response_id, list(reversed(trimmed_messages))
        else:
            return None, messages

    async def _map_messages(  # noqa: C901
        self,
        messages: list[ModelMessage],
        model_settings: OpenAIResponsesModelSettings,
        model_request_parameters: ModelRequestParameters,
    ) -> tuple[str | Omit, list[responses.ResponseInputItemParam]]:
        """Maps a `pydantic_ai.Message` to a `openai.types.responses.ResponseInputParam` i.e. the OpenAI Responses API input format.

        For `ThinkingParts`, this method:
        - Sends `signature` back as `encrypted_content` (for official OpenAI reasoning)
        - Sends `content` back as `summary` text
        - Sends `provider_details['raw_content']` back as `content` items (for gpt-oss raw CoT)

        Raw CoT is sent back to improve model performance in multi-turn conversations.
        """
        profile = OpenAIModelProfile.from_profile(self.profile)
        send_item_ids = model_settings.get(
            'openai_send_reasoning_ids', profile.openai_supports_encrypted_reasoning_content
        )

        openai_messages: list[responses.ResponseInputItemParam] = []
        for message in messages:
            if isinstance(message, ModelRequest):
                for part in message.parts:
                    if isinstance(part, SystemPromptPart):
                        openai_messages.append(responses.EasyInputMessageParam(role='system', content=part.content))
                    elif isinstance(part, UserPromptPart):
                        openai_messages.append(await self._map_user_prompt(part))
                    elif isinstance(part, ToolReturnPart):
                        call_id = _guard_tool_call_id(t=part)
                        call_id, _ = _split_combined_tool_call_id(call_id)
                        item = FunctionCallOutput(
                            type='function_call_output',
                            call_id=call_id,
                            output=part.model_response_str(),
                        )
                        openai_messages.append(item)
                    elif isinstance(part, RetryPromptPart):
                        if part.tool_name is None:
                            openai_messages.append(
                                Message(role='user', content=[{'type': 'input_text', 'text': part.model_response()}])
                            )
                        else:
                            call_id = _guard_tool_call_id(t=part)
                            call_id, _ = _split_combined_tool_call_id(call_id)
                            item = FunctionCallOutput(
                                type='function_call_output',
                                call_id=call_id,
                                output=part.model_response(),
                            )
                            openai_messages.append(item)
                    else:
                        assert_never(part)
            elif isinstance(message, ModelResponse):
                send_item_ids = send_item_ids and message.provider_name == self.system

                message_item: responses.ResponseOutputMessageParam | None = None
                reasoning_item: responses.ResponseReasoningItemParam | None = None
                web_search_item: responses.ResponseFunctionWebSearchParam | None = None
                code_interpreter_item: responses.ResponseCodeInterpreterToolCallParam | None = None
                for item in message.parts:
                    if isinstance(item, TextPart):
                        if item.id and send_item_ids:
                            if message_item is None or message_item['id'] != item.id:  # pragma: no branch
                                message_item = responses.ResponseOutputMessageParam(
                                    role='assistant',
                                    id=item.id,
                                    content=[],
                                    type='message',
                                    status='completed',
                                )
                                openai_messages.append(message_item)

                            message_item['content'] = [
                                *message_item['content'],
                                responses.ResponseOutputTextParam(
                                    text=item.content, type='output_text', annotations=[]
                                ),
                            ]
                        else:
                            openai_messages.append(
                                responses.EasyInputMessageParam(role='assistant', content=item.content)
                            )
                    elif isinstance(item, ToolCallPart):
                        call_id = _guard_tool_call_id(t=item)
                        call_id, id = _split_combined_tool_call_id(call_id)
                        id = id or item.id

                        param = responses.ResponseFunctionToolCallParam(
                            name=item.tool_name,
                            arguments=item.args_as_json_str(),
                            call_id=call_id,
                            type='function_call',
                        )
                        if profile.openai_responses_requires_function_call_status_none:
                            param['status'] = None  # type: ignore[reportGeneralTypeIssues]
                        if id and send_item_ids:  # pragma: no branch
                            param['id'] = id
                        openai_messages.append(param)
                    elif isinstance(item, BuiltinToolCallPart):
                        if item.provider_name == self.system and send_item_ids:  # pragma: no branch
                            if (
                                item.tool_name == CodeExecutionTool.kind
                                and item.tool_call_id
                                and (args := item.args_as_dict())
                                and (container_id := args.get('container_id'))
                            ):
                                code_interpreter_item = responses.ResponseCodeInterpreterToolCallParam(
                                    id=item.tool_call_id,
                                    code=args.get('code'),
                                    container_id=container_id,
                                    outputs=None,  # These can be read server-side
                                    status='completed',
                                    type='code_interpreter_call',
                                )
                                openai_messages.append(code_interpreter_item)
                            elif (
                                item.tool_name == WebSearchTool.kind
                                and item.tool_call_id
                                and (args := item.args_as_dict())
                            ):
                                web_search_item = responses.ResponseFunctionWebSearchParam(
                                    id=item.tool_call_id,
                                    action=cast(responses.response_function_web_search_param.Action, args),
                                    status='completed',
                                    type='web_search_call',
                                )
                                openai_messages.append(web_search_item)
                            elif item.tool_name == ImageGenerationTool.kind and item.tool_call_id:
                                # The cast is necessary because of https://github.com/openai/openai-python/issues/2648
                                image_generation_item = cast(
                                    responses.response_input_item_param.ImageGenerationCall,
                                    {
                                        'id': item.tool_call_id,
                                        'type': 'image_generation_call',
                                    },
                                )
                                openai_messages.append(image_generation_item)
                            elif (  # pragma: no branch
                                item.tool_name.startswith(MCPServerTool.kind)
                                and item.tool_call_id
                                and (server_id := item.tool_name.split(':', 1)[1])
                                and (args := item.args_as_dict())
                                and (action := args.get('action'))
                            ):
                                if action == 'list_tools':
                                    mcp_list_tools_item = responses.response_input_item_param.McpListTools(
                                        id=item.tool_call_id,
                                        type='mcp_list_tools',
                                        server_label=server_id,
                                        tools=[],  # These can be read server-side
                                    )
                                    openai_messages.append(mcp_list_tools_item)
                                elif (  # pragma: no branch
                                    action == 'call_tool'
                                    and (tool_name := args.get('tool_name'))
                                    and (tool_args := args.get('tool_args'))
                                ):
                                    mcp_call_item = responses.response_input_item_param.McpCall(
                                        id=item.tool_call_id,
                                        server_label=server_id,
                                        name=tool_name,
                                        arguments=to_json(tool_args).decode(),
                                        error=None,  # These can be read server-side
                                        output=None,  # These can be read server-side
                                        type='mcp_call',
                                    )
                                    openai_messages.append(mcp_call_item)

                    elif isinstance(item, BuiltinToolReturnPart):
                        if item.provider_name == self.system and send_item_ids:  # pragma: no branch
                            if (
                                item.tool_name == CodeExecutionTool.kind
                                and code_interpreter_item is not None
                                and isinstance(item.content, dict)
                                and (content := cast(dict[str, Any], item.content))  # pyright: ignore[reportUnknownMemberType]
                                and (status := content.get('status'))
                            ):
                                code_interpreter_item['status'] = status
                            elif (
                                item.tool_name == WebSearchTool.kind
                                and web_search_item is not None
                                and isinstance(item.content, dict)  # pyright: ignore[reportUnknownMemberType]
                                and (content := cast(dict[str, Any], item.content))  # pyright: ignore[reportUnknownMemberType]
                                and (status := content.get('status'))
                            ):
                                web_search_item['status'] = status
                            elif item.tool_name == ImageGenerationTool.kind:
                                # Image generation result does not need to be sent back, just the `id` off of `BuiltinToolCallPart`.
                                pass
                            elif item.tool_name.startswith(MCPServerTool.kind):  # pragma: no branch
                                # MCP call result does not need to be sent back, just the fields off of `BuiltinToolCallPart`.
                                pass
                    elif isinstance(item, FilePart):
                        # This was generated by the `ImageGenerationTool` or `CodeExecutionTool`,
                        # and does not need to be sent back separately from the corresponding `BuiltinToolReturnPart`.
                        # If `send_item_ids` is false, we won't send the `BuiltinToolReturnPart`, but OpenAI does not have a type for files from the assistant.
                        pass
                    elif isinstance(item, ThinkingPart):
                        # Get raw CoT content from provider_details if present and from this provider
                        raw_content: list[str] | None = None
                        if item.provider_name == self.system:
                            raw_content = (item.provider_details or {}).get('raw_content')

                        if item.id and (send_item_ids or raw_content):
                            signature: str | None = None
                            if (
                                item.signature
                                and item.provider_name == self.system
                                and profile.openai_supports_encrypted_reasoning_content
                            ):
                                signature = item.signature

                            if (reasoning_item is None or reasoning_item['id'] != item.id) and (
                                signature or item.content or raw_content
                            ):  # pragma: no branch
                                reasoning_item = responses.ResponseReasoningItemParam(
                                    id=item.id,
                                    summary=[],
                                    encrypted_content=signature,
                                    type='reasoning',
                                )
                                openai_messages.append(reasoning_item)

                            if item.content:
                                # The check above guarantees that `reasoning_item` is not None
                                assert reasoning_item is not None
                                reasoning_item['summary'] = [
                                    *reasoning_item['summary'],
                                    ReasoningSummary(text=item.content, type='summary_text'),
                                ]

                            if raw_content:
                                # Send raw CoT back
                                assert reasoning_item is not None
                                reasoning_item['content'] = [
                                    ReasoningContent(text=text, type='reasoning_text') for text in raw_content
                                ]
                        else:
                            start_tag, end_tag = profile.thinking_tags
                            openai_messages.append(
                                responses.EasyInputMessageParam(
                                    role='assistant', content='\n'.join([start_tag, item.content, end_tag])
                                )
                            )
                    else:
                        assert_never(item)
            else:
                assert_never(message)
        instructions = self._get_instructions(messages, model_request_parameters) or OMIT
        return instructions, openai_messages

    def _map_json_schema(self, o: OutputObjectDefinition) -> responses.ResponseFormatTextJSONSchemaConfigParam:
        response_format_param: responses.ResponseFormatTextJSONSchemaConfigParam = {
            'type': 'json_schema',
            'name': o.name or DEFAULT_OUTPUT_TOOL_NAME,
            'schema': o.json_schema,
        }
        if o.description:
            response_format_param['description'] = o.description
        if OpenAIModelProfile.from_profile(self.profile).openai_supports_strict_tool_definition:  # pragma: no branch
            response_format_param['strict'] = o.strict
        return response_format_param

    @staticmethod
    async def _map_user_prompt(part: UserPromptPart) -> responses.EasyInputMessageParam:  # noqa: C901
        content: str | list[responses.ResponseInputContentParam]
        if isinstance(part.content, str):
            content = part.content
        else:
            content = []
            for item in part.content:
                if isinstance(item, str):
                    content.append(responses.ResponseInputTextParam(text=item, type='input_text'))
                elif isinstance(item, BinaryContent):
                    if item.is_image:
                        detail: Literal['auto', 'low', 'high'] = 'auto'
                        if metadata := item.vendor_metadata:
                            detail = cast(
                                Literal['auto', 'low', 'high'],
                                metadata.get('detail', 'auto'),
                            )
                        content.append(
                            responses.ResponseInputImageParam(
                                image_url=item.data_uri,
                                type='input_image',
                                detail=detail,
                            )
                        )
                    elif item.is_document:
                        content.append(
                            responses.ResponseInputFileParam(
                                type='input_file',
                                file_data=item.data_uri,
                                # NOTE: Type wise it's not necessary to include the filename, but it's required by the
                                # API itself. If we add empty string, the server sends a 500 error - which OpenAI needs
                                # to fix. In any case, we add a placeholder name.
                                filename=f'filename.{item.format}',
                            )
                        )
                    elif item.is_audio:
                        raise NotImplementedError('Audio as binary content is not supported for OpenAI Responses API.')
                    else:  # pragma: no cover
                        raise RuntimeError(f'Unsupported binary content type: {item.media_type}')
                elif isinstance(item, ImageUrl):
                    detail: Literal['auto', 'low', 'high'] = 'auto'
                    image_url = item.url
                    if metadata := item.vendor_metadata:
                        detail = cast(Literal['auto', 'low', 'high'], metadata.get('detail', 'auto'))
                    if item.force_download:
                        downloaded_item = await download_item(item, data_format='base64_uri', type_format='extension')
                        image_url = downloaded_item['data']

                    content.append(
                        responses.ResponseInputImageParam(
                            image_url=image_url,
                            type='input_image',
                            detail=detail,
                        )
                    )
                elif isinstance(item, AudioUrl):  # pragma: no cover
                    downloaded_item = await download_item(item, data_format='base64_uri', type_format='extension')
                    content.append(
                        responses.ResponseInputFileParam(
                            type='input_file',
                            file_data=downloaded_item['data'],
                            filename=f'filename.{downloaded_item["data_type"]}',
                        )
                    )
                elif isinstance(item, DocumentUrl):
                    downloaded_item = await download_item(item, data_format='base64_uri', type_format='extension')
                    content.append(
                        responses.ResponseInputFileParam(
                            type='input_file',
                            file_data=downloaded_item['data'],
                            filename=f'filename.{downloaded_item["data_type"]}',
                        )
                    )
                elif isinstance(item, VideoUrl):  # pragma: no cover
                    raise NotImplementedError('VideoUrl is not supported for OpenAI.')
                elif isinstance(item, CachePoint):
                    # OpenAI doesn't support prompt caching via CachePoint, so we filter it out
                    pass
                else:
                    assert_never(item)
        return responses.EasyInputMessageParam(role='user', content=content)

```

#### **init**

```python
__init__(
    model_name: OpenAIModelName,
    *,
    provider: (
        Literal[
            "openai",
            "deepseek",
            "azure",
            "openrouter",
            "grok",
            "fireworks",
            "together",
            "nebius",
            "ovhcloud",
            "gateway",
        ]
        | Provider[AsyncOpenAI]
    ) = "openai",
    profile: ModelProfileSpec | None = None,
    settings: ModelSettings | None = None
)

```

Initialize an OpenAI Responses model.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `model_name` | `OpenAIModelName` | The name of the OpenAI model to use. | _required_ | | `provider` | `Literal['openai', 'deepseek', 'azure', 'openrouter', 'grok', 'fireworks', 'together', 'nebius', 'ovhcloud', 'gateway'] | Provider[AsyncOpenAI]` | The provider to use. Defaults to 'openai'. | `'openai'` | | `profile` | `ModelProfileSpec | None` | The model profile to use. Defaults to a profile picked by the provider based on the model name. | `None` | | `settings` | `ModelSettings | None` | Default model settings for this model instance. | `None` |

Source code in `pydantic_ai_slim/pydantic_ai/models/openai.py`

```python
def __init__(
    self,
    model_name: OpenAIModelName,
    *,
    provider: Literal[
        'openai',
        'deepseek',
        'azure',
        'openrouter',
        'grok',
        'fireworks',
        'together',
        'nebius',
        'ovhcloud',
        'gateway',
    ]
    | Provider[AsyncOpenAI] = 'openai',
    profile: ModelProfileSpec | None = None,
    settings: ModelSettings | None = None,
):
    """Initialize an OpenAI Responses model.

    Args:
        model_name: The name of the OpenAI model to use.
        provider: The provider to use. Defaults to `'openai'`.
        profile: The model profile to use. Defaults to a profile picked by the provider based on the model name.
        settings: Default model settings for this model instance.
    """
    self._model_name = model_name

    if isinstance(provider, str):
        provider = infer_provider('gateway/openai' if provider == 'gateway' else provider)
    self._provider = provider
    self.client = provider.client

    super().__init__(settings=settings, profile=profile or provider.model_profile)

```

#### model_name

```python
model_name: OpenAIModelName

```

The model name.

#### system

```python
system: str

```

The model provider.
