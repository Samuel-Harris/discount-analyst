### AnthropicModel

Bases: `Model`

A model that uses the Anthropic API.

Internally, this uses the [Anthropic Python client](https://github.com/anthropics/anthropic-sdk-python) to interact with the API.

Apart from `__init__`, all methods are private or match those of the base class.

Source code in `pydantic_ai_slim/pydantic_ai/models/anthropic.py`

```python
@dataclass(init=False)
class AnthropicModel(Model):
    """A model that uses the Anthropic API.

    Internally, this uses the [Anthropic Python client](https://github.com/anthropics/anthropic-sdk-python) to interact with the API.

    Apart from `__init__`, all methods are private or match those of the base class.
    """

    client: AsyncAnthropicClient = field(repr=False)

    _model_name: AnthropicModelName = field(repr=False)
    _provider: Provider[AsyncAnthropicClient] = field(repr=False)

    def __init__(
        self,
        model_name: AnthropicModelName,
        *,
        provider: Literal['anthropic', 'gateway'] | Provider[AsyncAnthropicClient] = 'anthropic',
        profile: ModelProfileSpec | None = None,
        settings: ModelSettings | None = None,
    ):
        """Initialize an Anthropic model.

        Args:
            model_name: The name of the Anthropic model to use. List of model names available
                [here](https://docs.anthropic.com/en/docs/about-claude/models).
            provider: The provider to use for the Anthropic API. Can be either the string 'anthropic' or an
                instance of `Provider[AsyncAnthropicClient]`. Defaults to 'anthropic'.
            profile: The model profile to use. Defaults to a profile picked by the provider based on the model name.
                The default 'anthropic' provider will use the default `..profiles.anthropic.anthropic_model_profile`.
            settings: Default model settings for this model instance.
        """
        self._model_name = model_name

        if isinstance(provider, str):
            provider = infer_provider('gateway/anthropic' if provider == 'gateway' else provider)
        self._provider = provider
        self.client = provider.client

        super().__init__(settings=settings, profile=profile or provider.model_profile)

    @property
    def base_url(self) -> str:
        return str(self.client.base_url)

    @property
    def model_name(self) -> AnthropicModelName:
        """The model name."""
        return self._model_name

    @property
    def system(self) -> str:
        """The model provider."""
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
        response = await self._messages_create(
            messages, False, cast(AnthropicModelSettings, model_settings or {}), model_request_parameters
        )
        model_response = self._process_response(response)
        return model_response

    async def count_tokens(
        self,
        messages: list[ModelMessage],
        model_settings: ModelSettings | None,
        model_request_parameters: ModelRequestParameters,
    ) -> usage.RequestUsage:
        model_settings, model_request_parameters = self.prepare_request(
            model_settings,
            model_request_parameters,
        )

        response = await self._messages_count_tokens(
            messages, cast(AnthropicModelSettings, model_settings or {}), model_request_parameters
        )

        return usage.RequestUsage(input_tokens=response.input_tokens)

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
        response = await self._messages_create(
            messages, True, cast(AnthropicModelSettings, model_settings or {}), model_request_parameters
        )
        async with response:
            yield await self._process_streamed_response(response, model_request_parameters)

    def prepare_request(
        self, model_settings: ModelSettings | None, model_request_parameters: ModelRequestParameters
    ) -> tuple[ModelSettings | None, ModelRequestParameters]:
        settings = merge_model_settings(self.settings, model_settings)
        if (
            model_request_parameters.output_tools
            and settings
            and (thinking := settings.get('anthropic_thinking'))
            and thinking.get('type') == 'enabled'
        ):
            if model_request_parameters.output_mode == 'auto':
                output_mode = 'native' if self.profile.supports_json_schema_output else 'prompted'
                model_request_parameters = replace(model_request_parameters, output_mode=output_mode)
            elif (
                model_request_parameters.output_mode == 'tool' and not model_request_parameters.allow_text_output
            ):  # pragma: no branch
                # This would result in `tool_choice=required`, which Anthropic does not support with thinking.
                suggested_output_type = 'NativeOutput' if self.profile.supports_json_schema_output else 'PromptedOutput'
                raise UserError(
                    f'Anthropic does not support thinking and output tools at the same time. Use `output_type={suggested_output_type}(...)` instead.'
                )

        if model_request_parameters.output_mode == 'native':
            assert model_request_parameters.output_object is not None
            if model_request_parameters.output_object.strict is False:
                raise UserError(
                    'Setting `strict=False` on `output_type=NativeOutput(...)` is not allowed for Anthropic models.'
                )
            model_request_parameters = replace(
                model_request_parameters, output_object=replace(model_request_parameters.output_object, strict=True)
            )
        return super().prepare_request(model_settings, model_request_parameters)

    @overload
    async def _messages_create(
        self,
        messages: list[ModelMessage],
        stream: Literal[True],
        model_settings: AnthropicModelSettings,
        model_request_parameters: ModelRequestParameters,
    ) -> AsyncStream[BetaRawMessageStreamEvent]:
        pass

    @overload
    async def _messages_create(
        self,
        messages: list[ModelMessage],
        stream: Literal[False],
        model_settings: AnthropicModelSettings,
        model_request_parameters: ModelRequestParameters,
    ) -> BetaMessage:
        pass

    async def _messages_create(
        self,
        messages: list[ModelMessage],
        stream: bool,
        model_settings: AnthropicModelSettings,
        model_request_parameters: ModelRequestParameters,
    ) -> BetaMessage | AsyncStream[BetaRawMessageStreamEvent]:
        """Calls the Anthropic API to create a message.

        This is the last step before sending the request to the API.
        Most preprocessing has happened in `prepare_request()`.
        """
        tools = self._get_tools(model_request_parameters, model_settings)
        tools, mcp_servers, builtin_tool_betas = self._add_builtin_tools(tools, model_request_parameters)

        tool_choice = self._infer_tool_choice(tools, model_settings, model_request_parameters)

        system_prompt, anthropic_messages = await self._map_message(messages, model_request_parameters, model_settings)
        self._limit_cache_points(system_prompt, anthropic_messages, tools)
        output_format = self._native_output_format(model_request_parameters)
        betas, extra_headers = self._get_betas_and_extra_headers(tools, model_request_parameters, model_settings)
        betas.update(builtin_tool_betas)
        try:
            return await self.client.beta.messages.create(
                max_tokens=model_settings.get('max_tokens', 4096),
                system=system_prompt or OMIT,
                messages=anthropic_messages,
                model=self._model_name,
                tools=tools or OMIT,
                tool_choice=tool_choice or OMIT,
                mcp_servers=mcp_servers or OMIT,
                output_format=output_format or OMIT,
                betas=sorted(betas) or OMIT,
                stream=stream,
                thinking=model_settings.get('anthropic_thinking', OMIT),
                stop_sequences=model_settings.get('stop_sequences', OMIT),
                temperature=model_settings.get('temperature', OMIT),
                top_p=model_settings.get('top_p', OMIT),
                timeout=model_settings.get('timeout', NOT_GIVEN),
                metadata=model_settings.get('anthropic_metadata', OMIT),
                extra_headers=extra_headers,
                extra_body=model_settings.get('extra_body'),
            )
        except APIStatusError as e:
            if (status_code := e.status_code) >= 400:
                raise ModelHTTPError(status_code=status_code, model_name=self.model_name, body=e.body) from e
            raise ModelAPIError(model_name=self.model_name, message=e.message) from e  # pragma: lax no cover
        except APIConnectionError as e:
            raise ModelAPIError(model_name=self.model_name, message=e.message) from e

    def _get_betas_and_extra_headers(
        self,
        tools: list[BetaToolUnionParam],
        model_request_parameters: ModelRequestParameters,
        model_settings: AnthropicModelSettings,
    ) -> tuple[set[str], dict[str, str]]:
        """Prepare beta features list and extra headers for API request.

        Handles merging custom `anthropic-beta` header from `extra_headers` into betas set
        and ensuring `User-Agent` is set.
        """
        extra_headers = dict(model_settings.get('extra_headers', {}))
        extra_headers.setdefault('User-Agent', get_user_agent())

        betas: set[str] = set()

        has_strict_tools = any(tool.get('strict') for tool in tools)

        if has_strict_tools or model_request_parameters.output_mode == 'native':
            betas.add('structured-outputs-2025-11-13')

        if beta_header := extra_headers.pop('anthropic-beta', None):
            betas.update({stripped_beta for beta in beta_header.split(',') if (stripped_beta := beta.strip())})

        return betas, extra_headers

    async def _messages_count_tokens(
        self,
        messages: list[ModelMessage],
        model_settings: AnthropicModelSettings,
        model_request_parameters: ModelRequestParameters,
    ) -> BetaMessageTokensCount:
        if isinstance(self.client, AsyncAnthropicBedrock):
            raise UserError('AsyncAnthropicBedrock client does not support `count_tokens` api.')

        # standalone function to make it easier to override
        tools = self._get_tools(model_request_parameters, model_settings)
        tools, mcp_servers, builtin_tool_betas = self._add_builtin_tools(tools, model_request_parameters)

        tool_choice = self._infer_tool_choice(tools, model_settings, model_request_parameters)

        system_prompt, anthropic_messages = await self._map_message(messages, model_request_parameters, model_settings)
        self._limit_cache_points(system_prompt, anthropic_messages, tools)
        output_format = self._native_output_format(model_request_parameters)
        betas, extra_headers = self._get_betas_and_extra_headers(tools, model_request_parameters, model_settings)
        betas.update(builtin_tool_betas)
        try:
            return await self.client.beta.messages.count_tokens(
                system=system_prompt or OMIT,
                messages=anthropic_messages,
                model=self._model_name,
                tools=tools or OMIT,
                tool_choice=tool_choice or OMIT,
                mcp_servers=mcp_servers or OMIT,
                betas=sorted(betas) or OMIT,
                output_format=output_format or OMIT,
                thinking=model_settings.get('anthropic_thinking', OMIT),
                timeout=model_settings.get('timeout', NOT_GIVEN),
                extra_headers=extra_headers,
                extra_body=model_settings.get('extra_body'),
            )
        except APIStatusError as e:
            if (status_code := e.status_code) >= 400:
                raise ModelHTTPError(status_code=status_code, model_name=self.model_name, body=e.body) from e
            raise ModelAPIError(model_name=self.model_name, message=e.message) from e  # pragma: lax no cover
        except APIConnectionError as e:
            raise ModelAPIError(model_name=self.model_name, message=e.message) from e

    def _process_response(self, response: BetaMessage) -> ModelResponse:
        """Process a non-streamed response, and prepare a message to return."""
        items: list[ModelResponsePart] = []
        builtin_tool_calls: dict[str, BuiltinToolCallPart] = {}
        for item in response.content:
            if isinstance(item, BetaTextBlock):
                items.append(TextPart(content=item.text))
            elif isinstance(item, BetaServerToolUseBlock):
                call_part = _map_server_tool_use_block(item, self.system)
                builtin_tool_calls[call_part.tool_call_id] = call_part
                items.append(call_part)
            elif isinstance(item, BetaWebSearchToolResultBlock):
                items.append(_map_web_search_tool_result_block(item, self.system))
            elif isinstance(item, BetaCodeExecutionToolResultBlock):
                items.append(_map_code_execution_tool_result_block(item, self.system))
            elif isinstance(item, BetaWebFetchToolResultBlock):
                items.append(_map_web_fetch_tool_result_block(item, self.system))
            elif isinstance(item, BetaRedactedThinkingBlock):
                items.append(
                    ThinkingPart(id='redacted_thinking', content='', signature=item.data, provider_name=self.system)
                )
            elif isinstance(item, BetaThinkingBlock):
                items.append(ThinkingPart(content=item.thinking, signature=item.signature, provider_name=self.system))
            elif isinstance(item, BetaMCPToolUseBlock):
                call_part = _map_mcp_server_use_block(item, self.system)
                builtin_tool_calls[call_part.tool_call_id] = call_part
                items.append(call_part)
            elif isinstance(item, BetaMCPToolResultBlock):
                call_part = builtin_tool_calls.get(item.tool_use_id)
                items.append(_map_mcp_server_result_block(item, call_part, self.system))
            else:
                assert isinstance(item, BetaToolUseBlock), f'unexpected item type {type(item)}'
                items.append(
                    ToolCallPart(
                        tool_name=item.name,
                        args=cast(dict[str, Any], item.input),
                        tool_call_id=item.id,
                    )
                )

        finish_reason: FinishReason | None = None
        provider_details: dict[str, Any] | None = None
        if raw_finish_reason := response.stop_reason:  # pragma: no branch
            provider_details = {'finish_reason': raw_finish_reason}
            finish_reason = _FINISH_REASON_MAP.get(raw_finish_reason)

        return ModelResponse(
            parts=items,
            usage=_map_usage(response, self._provider.name, self._provider.base_url, self._model_name),
            model_name=response.model,
            provider_response_id=response.id,
            provider_name=self._provider.name,
            finish_reason=finish_reason,
            provider_details=provider_details,
        )

    async def _process_streamed_response(
        self, response: AsyncStream[BetaRawMessageStreamEvent], model_request_parameters: ModelRequestParameters
    ) -> StreamedResponse:
        peekable_response = _utils.PeekableAsyncStream(response)
        first_chunk = await peekable_response.peek()
        if isinstance(first_chunk, _utils.Unset):
            raise UnexpectedModelBehavior('Streamed response ended without content or tool calls')  # pragma: no cover

        assert isinstance(first_chunk, BetaRawMessageStartEvent)

        return AnthropicStreamedResponse(
            model_request_parameters=model_request_parameters,
            _model_name=first_chunk.message.model,
            _response=peekable_response,
            _timestamp=_utils.now_utc(),
            _provider_name=self._provider.name,
            _provider_url=self._provider.base_url,
        )

    def _get_tools(
        self, model_request_parameters: ModelRequestParameters, model_settings: AnthropicModelSettings
    ) -> list[BetaToolUnionParam]:
        tools: list[BetaToolUnionParam] = [
            self._map_tool_definition(r) for r in model_request_parameters.tool_defs.values()
        ]

        # Add cache_control to the last tool if enabled
        if tools and (cache_tool_defs := model_settings.get('anthropic_cache_tool_definitions')):
            # If True, use '5m'; otherwise use the specified ttl value
            ttl: Literal['5m', '1h'] = '5m' if cache_tool_defs is True else cache_tool_defs
            last_tool = tools[-1]
            last_tool['cache_control'] = self._build_cache_control(ttl)

        return tools

    def _add_builtin_tools(
        self, tools: list[BetaToolUnionParam], model_request_parameters: ModelRequestParameters
    ) -> tuple[list[BetaToolUnionParam], list[BetaRequestMCPServerURLDefinitionParam], set[str]]:
        beta_features: set[str] = set()
        mcp_servers: list[BetaRequestMCPServerURLDefinitionParam] = []
        for tool in model_request_parameters.builtin_tools:
            if isinstance(tool, WebSearchTool):
                user_location = UserLocation(type='approximate', **tool.user_location) if tool.user_location else None
                tools.append(
                    BetaWebSearchTool20250305Param(
                        name='web_search',
                        type='web_search_20250305',
                        max_uses=tool.max_uses,
                        allowed_domains=tool.allowed_domains,
                        blocked_domains=tool.blocked_domains,
                        user_location=user_location,
                    )
                )
            elif isinstance(tool, CodeExecutionTool):  # pragma: no branch
                tools.append(BetaCodeExecutionTool20250522Param(name='code_execution', type='code_execution_20250522'))
                beta_features.add('code-execution-2025-05-22')
            elif isinstance(tool, WebFetchTool):  # pragma: no branch
                citations = BetaCitationsConfigParam(enabled=tool.enable_citations) if tool.enable_citations else None
                tools.append(
                    BetaWebFetchTool20250910Param(
                        name='web_fetch',
                        type='web_fetch_20250910',
                        max_uses=tool.max_uses,
                        allowed_domains=tool.allowed_domains,
                        blocked_domains=tool.blocked_domains,
                        citations=citations,
                        max_content_tokens=tool.max_content_tokens,
                    )
                )
                beta_features.add('web-fetch-2025-09-10')
            elif isinstance(tool, MemoryTool):  # pragma: no branch
                if 'memory' not in model_request_parameters.tool_defs:
                    raise UserError("Built-in `MemoryTool` requires a 'memory' tool to be defined.")
                # Replace the memory tool definition with the built-in memory tool
                tools = [tool for tool in tools if tool.get('name') != 'memory']
                tools.append(BetaMemoryTool20250818Param(name='memory', type='memory_20250818'))
                beta_features.add('context-management-2025-06-27')
            elif isinstance(tool, MCPServerTool) and tool.url:
                mcp_server_url_definition_param = BetaRequestMCPServerURLDefinitionParam(
                    type='url',
                    name=tool.id,
                    url=tool.url,
                )
                if tool.allowed_tools is not None:  # pragma: no branch
                    mcp_server_url_definition_param['tool_configuration'] = BetaRequestMCPServerToolConfigurationParam(
                        enabled=bool(tool.allowed_tools),
                        allowed_tools=tool.allowed_tools,
                    )
                if tool.authorization_token:  # pragma: no cover
                    mcp_server_url_definition_param['authorization_token'] = tool.authorization_token
                mcp_servers.append(mcp_server_url_definition_param)
                beta_features.add('mcp-client-2025-04-04')
            else:  # pragma: no cover
                raise UserError(
                    f'`{tool.__class__.__name__}` is not supported by `AnthropicModel`. If it should be, please file an issue.'
                )
        return tools, mcp_servers, beta_features

    def _infer_tool_choice(
        self,
        tools: list[BetaToolUnionParam],
        model_settings: AnthropicModelSettings,
        model_request_parameters: ModelRequestParameters,
    ) -> BetaToolChoiceParam | None:
        if not tools:
            return None
        else:
            tool_choice: BetaToolChoiceParam

            if not model_request_parameters.allow_text_output:
                tool_choice = {'type': 'any'}
            else:
                tool_choice = {'type': 'auto'}

            if 'parallel_tool_calls' in model_settings:
                tool_choice['disable_parallel_tool_use'] = not model_settings['parallel_tool_calls']

            return tool_choice

    async def _map_message(  # noqa: C901
        self,
        messages: list[ModelMessage],
        model_request_parameters: ModelRequestParameters,
        model_settings: AnthropicModelSettings,
    ) -> tuple[str | list[BetaTextBlockParam], list[BetaMessageParam]]:
        """Just maps a `pydantic_ai.Message` to a `anthropic.types.MessageParam`."""
        system_prompt_parts: list[str] = []
        anthropic_messages: list[BetaMessageParam] = []
        for m in messages:
            if isinstance(m, ModelRequest):
                user_content_params: list[BetaContentBlockParam] = []
                for request_part in m.parts:
                    if isinstance(request_part, SystemPromptPart):
                        system_prompt_parts.append(request_part.content)
                    elif isinstance(request_part, UserPromptPart):
                        async for content in self._map_user_prompt(request_part):
                            if isinstance(content, CachePoint):
                                self._add_cache_control_to_last_param(user_content_params, ttl=content.ttl)
                            else:
                                user_content_params.append(content)
                    elif isinstance(request_part, ToolReturnPart):
                        tool_result_block_param = BetaToolResultBlockParam(
                            tool_use_id=_guard_tool_call_id(t=request_part),
                            type='tool_result',
                            content=request_part.model_response_str(),
                            is_error=False,
                        )
                        user_content_params.append(tool_result_block_param)
                    elif isinstance(request_part, RetryPromptPart):  # pragma: no branch
                        if request_part.tool_name is None:
                            text = request_part.model_response()  # pragma: no cover
                            retry_param = BetaTextBlockParam(type='text', text=text)  # pragma: no cover
                        else:
                            retry_param = BetaToolResultBlockParam(
                                tool_use_id=_guard_tool_call_id(t=request_part),
                                type='tool_result',
                                content=request_part.model_response(),
                                is_error=True,
                            )
                        user_content_params.append(retry_param)
                if len(user_content_params) > 0:
                    anthropic_messages.append(BetaMessageParam(role='user', content=user_content_params))
            elif isinstance(m, ModelResponse):
                assistant_content_params: list[
                    BetaTextBlockParam
                    | BetaToolUseBlockParam
                    | BetaServerToolUseBlockParam
                    | BetaWebSearchToolResultBlockParam
                    | BetaCodeExecutionToolResultBlockParam
                    | BetaWebFetchToolResultBlockParam
                    | BetaThinkingBlockParam
                    | BetaRedactedThinkingBlockParam
                    | BetaMCPToolUseBlockParam
                    | BetaMCPToolResultBlock
                ] = []
                for response_part in m.parts:
                    if isinstance(response_part, TextPart):
                        if response_part.content:
                            assistant_content_params.append(BetaTextBlockParam(text=response_part.content, type='text'))
                    elif isinstance(response_part, ToolCallPart):
                        tool_use_block_param = BetaToolUseBlockParam(
                            id=_guard_tool_call_id(t=response_part),
                            type='tool_use',
                            name=response_part.tool_name,
                            input=response_part.args_as_dict(),
                        )
                        assistant_content_params.append(tool_use_block_param)
                    elif isinstance(response_part, ThinkingPart):
                        if (
                            response_part.provider_name == self.system and response_part.signature is not None
                        ):  # pragma: no branch
                            if response_part.id == 'redacted_thinking':
                                assistant_content_params.append(
                                    BetaRedactedThinkingBlockParam(
                                        data=response_part.signature,
                                        type='redacted_thinking',
                                    )
                                )
                            else:
                                assistant_content_params.append(
                                    BetaThinkingBlockParam(
                                        thinking=response_part.content,
                                        signature=response_part.signature,
                                        type='thinking',
                                    )
                                )
                        elif response_part.content:  # pragma: no branch
                            start_tag, end_tag = self.profile.thinking_tags
                            assistant_content_params.append(
                                BetaTextBlockParam(
                                    text='\n'.join([start_tag, response_part.content, end_tag]), type='text'
                                )
                            )
                    elif isinstance(response_part, BuiltinToolCallPart):
                        if response_part.provider_name == self.system:
                            tool_use_id = _guard_tool_call_id(t=response_part)
                            if response_part.tool_name == WebSearchTool.kind:
                                server_tool_use_block_param = BetaServerToolUseBlockParam(
                                    id=tool_use_id,
                                    type='server_tool_use',
                                    name='web_search',
                                    input=response_part.args_as_dict(),
                                )
                                assistant_content_params.append(server_tool_use_block_param)
                            elif response_part.tool_name == CodeExecutionTool.kind:
                                server_tool_use_block_param = BetaServerToolUseBlockParam(
                                    id=tool_use_id,
                                    type='server_tool_use',
                                    name='code_execution',
                                    input=response_part.args_as_dict(),
                                )
                                assistant_content_params.append(server_tool_use_block_param)
                            elif response_part.tool_name == WebFetchTool.kind:
                                server_tool_use_block_param = BetaServerToolUseBlockParam(
                                    id=tool_use_id,
                                    type='server_tool_use',
                                    name='web_fetch',
                                    input=response_part.args_as_dict(),
                                )
                                assistant_content_params.append(server_tool_use_block_param)
                            elif (
                                response_part.tool_name.startswith(MCPServerTool.kind)
                                and (server_id := response_part.tool_name.split(':', 1)[1])
                                and (args := response_part.args_as_dict())
                                and (tool_name := args.get('tool_name'))
                                and (tool_args := args.get('tool_args'))
                            ):  # pragma: no branch
                                mcp_tool_use_block_param = BetaMCPToolUseBlockParam(
                                    id=tool_use_id,
                                    type='mcp_tool_use',
                                    server_name=server_id,
                                    name=tool_name,
                                    input=tool_args,
                                )
                                assistant_content_params.append(mcp_tool_use_block_param)
                    elif isinstance(response_part, BuiltinToolReturnPart):
                        if response_part.provider_name == self.system:
                            tool_use_id = _guard_tool_call_id(t=response_part)
                            if response_part.tool_name in (
                                WebSearchTool.kind,
                                'web_search_tool_result',  # Backward compatibility
                            ) and isinstance(response_part.content, dict | list):
                                assistant_content_params.append(
                                    BetaWebSearchToolResultBlockParam(
                                        tool_use_id=tool_use_id,
                                        type='web_search_tool_result',
                                        content=cast(
                                            BetaWebSearchToolResultBlockParamContentParam,
                                            response_part.content,  # pyright: ignore[reportUnknownMemberType]
                                        ),
                                    )
                                )
                            elif response_part.tool_name in (  # pragma: no branch
                                CodeExecutionTool.kind,
                                'code_execution_tool_result',  # Backward compatibility
                            ) and isinstance(response_part.content, dict):
                                assistant_content_params.append(
                                    BetaCodeExecutionToolResultBlockParam(
                                        tool_use_id=tool_use_id,
                                        type='code_execution_tool_result',
                                        content=cast(
                                            BetaCodeExecutionToolResultBlockParamContentParam,
                                            response_part.content,  # pyright: ignore[reportUnknownMemberType]
                                        ),
                                    )
                                )
                            elif response_part.tool_name == WebFetchTool.kind and isinstance(
                                response_part.content, dict
                            ):
                                assistant_content_params.append(
                                    BetaWebFetchToolResultBlockParam(
                                        tool_use_id=tool_use_id,
                                        type='web_fetch_tool_result',
                                        content=cast(
                                            WebFetchToolResultBlockParamContent,
                                            response_part.content,  # pyright: ignore[reportUnknownMemberType]
                                        ),
                                    )
                                )
                            elif response_part.tool_name.startswith(MCPServerTool.kind) and isinstance(
                                response_part.content, dict
                            ):  # pragma: no branch
                                assistant_content_params.append(
                                    BetaMCPToolResultBlock(
                                        tool_use_id=tool_use_id,
                                        type='mcp_tool_result',
                                        **cast(dict[str, Any], response_part.content),  # pyright: ignore[reportUnknownMemberType]
                                    )
                                )
                    elif isinstance(response_part, FilePart):  # pragma: no cover
                        # Files generated by models are not sent back to models that don't themselves generate files.
                        pass
                    else:
                        assert_never(response_part)
                if len(assistant_content_params) > 0:
                    anthropic_messages.append(BetaMessageParam(role='assistant', content=assistant_content_params))
            else:
                assert_never(m)
        if instructions := self._get_instructions(messages, model_request_parameters):
            system_prompt_parts.insert(0, instructions)
        system_prompt = '\n\n'.join(system_prompt_parts)

        # Add cache_control to the last message content if anthropic_cache_messages is enabled
        if anthropic_messages and (cache_messages := model_settings.get('anthropic_cache_messages')):
            ttl: Literal['5m', '1h'] = '5m' if cache_messages is True else cache_messages
            m = anthropic_messages[-1]
            content = m['content']
            if isinstance(content, str):
                # Convert string content to list format with cache_control
                m['content'] = [  # pragma: no cover
                    BetaTextBlockParam(
                        text=content,
                        type='text',
                        cache_control=self._build_cache_control(ttl),
                    )
                ]
            else:
                # Add cache_control to the last content block
                content = cast(list[BetaContentBlockParam], content)
                self._add_cache_control_to_last_param(content, ttl)

        # If anthropic_cache_instructions is enabled, return system prompt as a list with cache_control
        if system_prompt and (cache_instructions := model_settings.get('anthropic_cache_instructions')):
            # If True, use '5m'; otherwise use the specified ttl value
            ttl: Literal['5m', '1h'] = '5m' if cache_instructions is True else cache_instructions
            system_prompt_blocks = [
                BetaTextBlockParam(
                    type='text',
                    text=system_prompt,
                    cache_control=self._build_cache_control(ttl),
                )
            ]
            return system_prompt_blocks, anthropic_messages

        return system_prompt, anthropic_messages

    @staticmethod
    def _limit_cache_points(
        system_prompt: str | list[BetaTextBlockParam],
        anthropic_messages: list[BetaMessageParam],
        tools: list[BetaToolUnionParam],
    ) -> None:
        """Limit the number of cache points in the request to Anthropic's maximum.

        Anthropic enforces a maximum of 4 cache points per request. This method ensures
        compliance by counting existing cache points and removing excess ones from messages.

        Strategy:
        1. Count cache points in system_prompt (can be multiple if list of blocks)
        2. Count cache points in tools (can be in any position, not just last)
        3. Raise UserError if system + tools already exceed MAX_CACHE_POINTS
        4. Calculate remaining budget for message cache points
        5. Traverse messages from newest to oldest, keeping the most recent cache points
           within the remaining budget
        6. Remove excess cache points from older messages to stay within limit

        Cache point priority (always preserved):
        - System prompt cache points
        - Tool definition cache points
        - Message cache points (newest first, oldest removed if needed)

        Raises:
            UserError: If system_prompt and tools combined already exceed MAX_CACHE_POINTS (4).
                      This indicates a configuration error that cannot be auto-fixed.
        """
        MAX_CACHE_POINTS = 4

        # Count existing cache points in system prompt
        used_cache_points = (
            sum(1 for block in system_prompt if 'cache_control' in cast(dict[str, Any], block))
            if isinstance(system_prompt, list)
            else 0
        )

        # Count existing cache points in tools (any tool may have cache_control)
        # Note: cache_control can be in the middle of tools list if builtin tools are added after
        for tool in tools:
            if 'cache_control' in tool:
                used_cache_points += 1

        # Calculate remaining cache points budget for messages
        remaining_budget = MAX_CACHE_POINTS - used_cache_points
        if remaining_budget < 0:  # pragma: no cover
            raise UserError(
                f'Too many cache points for Anthropic request. '
                f'System prompt and tool definitions already use {used_cache_points} cache points, '
                f'which exceeds the maximum of {MAX_CACHE_POINTS}.'
            )
        # Remove excess cache points from messages (newest to oldest)
        for message in reversed(anthropic_messages):
            content = message['content']
            if isinstance(content, str):  # pragma: no cover
                continue

            # Process content blocks in reverse order (newest first)
            for block in reversed(cast(list[BetaContentBlockParam], content)):
                block_dict = cast(dict[str, Any], block)

                if 'cache_control' in block_dict:
                    if remaining_budget > 0:
                        remaining_budget -= 1
                    else:
                        # Exceeded limit, remove this cache point
                        del block_dict['cache_control']

    def _build_cache_control(self, ttl: Literal['5m', '1h'] = '5m') -> BetaCacheControlEphemeralParam:
        """Build cache control dict, automatically omitting TTL for Bedrock clients.

        Args:
            ttl: The cache time-to-live ('5m' or '1h'). Ignored for Bedrock clients.

        Returns:
            A cache control dict suitable for the current client type.
        """
        if isinstance(self.client, AsyncAnthropicBedrock):
            # Bedrock doesn't support TTL, use cast to satisfy type checker
            return cast(BetaCacheControlEphemeralParam, {'type': 'ephemeral'})
        return BetaCacheControlEphemeralParam(type='ephemeral', ttl=ttl)

    def _add_cache_control_to_last_param(
        self, params: list[BetaContentBlockParam], ttl: Literal['5m', '1h'] = '5m'
    ) -> None:
        """Add cache control to the last content block param.

        See https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching for more information.

        Args:
            params: List of content block params to modify.
            ttl: The cache time-to-live ('5m' or '1h'). This is automatically ignored for
                 Bedrock clients, which don't support explicit TTL parameters.
        """
        if not params:
            raise UserError(
                'CachePoint cannot be the first content in a user message - there must be previous content to attach the CachePoint to. '
                'To cache system instructions or tool definitions, use the `anthropic_cache_instructions` or `anthropic_cache_tool_definitions` settings instead.'
            )

        # Only certain types support cache_control
        # See https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching#what-can-be-cached
        cacheable_types = {'text', 'tool_use', 'server_tool_use', 'image', 'tool_result', 'document'}
        # Cast needed because BetaContentBlockParam is a union including response Block types (Pydantic models)
        # that don't support dict operations, even though at runtime we only have request Param types (TypedDicts).
        last_param = cast(dict[str, Any], params[-1])
        if last_param['type'] not in cacheable_types:
            raise UserError(f'Cache control not supported for param type: {last_param["type"]}')

        # Add cache_control to the last param
        last_param['cache_control'] = self._build_cache_control(ttl)

    @staticmethod
    async def _map_user_prompt(
        part: UserPromptPart,
    ) -> AsyncGenerator[BetaContentBlockParam | CachePoint]:
        if isinstance(part.content, str):
            if part.content:  # Only yield non-empty text
                yield BetaTextBlockParam(text=part.content, type='text')
        else:
            for item in part.content:
                if isinstance(item, str):
                    if item:  # Only yield non-empty text
                        yield BetaTextBlockParam(text=item, type='text')
                elif isinstance(item, CachePoint):
                    yield item
                elif isinstance(item, BinaryContent):
                    if item.is_image:
                        yield BetaImageBlockParam(
                            source={'data': io.BytesIO(item.data), 'media_type': item.media_type, 'type': 'base64'},  # type: ignore
                            type='image',
                        )
                    elif item.media_type == 'application/pdf':
                        yield BetaBase64PDFBlockParam(
                            source=BetaBase64PDFSourceParam(
                                data=io.BytesIO(item.data),
                                media_type='application/pdf',
                                type='base64',
                            ),
                            type='document',
                        )
                    else:
                        raise RuntimeError('Only images and PDFs are supported for binary content')
                elif isinstance(item, ImageUrl):
                    yield BetaImageBlockParam(source={'type': 'url', 'url': item.url}, type='image')
                elif isinstance(item, DocumentUrl):
                    if item.media_type == 'application/pdf':
                        yield BetaBase64PDFBlockParam(source={'url': item.url, 'type': 'url'}, type='document')
                    elif item.media_type == 'text/plain':
                        downloaded_item = await download_item(item, data_format='text')
                        yield BetaBase64PDFBlockParam(
                            source=BetaPlainTextSourceParam(
                                data=downloaded_item['data'], media_type=item.media_type, type='text'
                            ),
                            type='document',
                        )
                    else:  # pragma: no cover
                        raise RuntimeError(f'Unsupported media type: {item.media_type}')
                else:
                    raise RuntimeError(f'Unsupported content type: {type(item)}')  # pragma: no cover

    def _map_tool_definition(self, f: ToolDefinition) -> BetaToolParam:
        """Maps a `ToolDefinition` dataclass to an Anthropic `BetaToolParam` dictionary."""
        tool_param: BetaToolParam = {
            'name': f.name,
            'description': f.description or '',
            'input_schema': f.parameters_json_schema,
        }
        if f.strict and self.profile.supports_json_schema_output:
            tool_param['strict'] = f.strict
        return tool_param

    @staticmethod
    def _native_output_format(model_request_parameters: ModelRequestParameters) -> BetaJSONOutputFormatParam | None:
        if model_request_parameters.output_mode != 'native':
            return None
        assert model_request_parameters.output_object is not None
        return {'type': 'json_schema', 'schema': model_request_parameters.output_object.json_schema}

```

#### **init**

```python
__init__(
    model_name: AnthropicModelName,
    *,
    provider: (
        Literal["anthropic", "gateway"]
        | Provider[AsyncAnthropicClient]
    ) = "anthropic",
    profile: ModelProfileSpec | None = None,
    settings: ModelSettings | None = None
)

```

Initialize an Anthropic model.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `model_name` | `AnthropicModelName` | The name of the Anthropic model to use. List of model names available here. | _required_ | | `provider` | `Literal['anthropic', 'gateway'] | Provider[AsyncAnthropicClient]` | The provider to use for the Anthropic API. Can be either the string 'anthropic' or an instance of Provider[AsyncAnthropicClient]. Defaults to 'anthropic'. | `'anthropic'` | | `profile` | `ModelProfileSpec | None` | The model profile to use. Defaults to a profile picked by the provider based on the model name. The default 'anthropic' provider will use the default ..profiles.anthropic.anthropic_model_profile. | `None` | | `settings` | `ModelSettings | None` | Default model settings for this model instance. | `None` |

Source code in `pydantic_ai_slim/pydantic_ai/models/anthropic.py`

```python
def __init__(
    self,
    model_name: AnthropicModelName,
    *,
    provider: Literal['anthropic', 'gateway'] | Provider[AsyncAnthropicClient] = 'anthropic',
    profile: ModelProfileSpec | None = None,
    settings: ModelSettings | None = None,
):
    """Initialize an Anthropic model.

    Args:
        model_name: The name of the Anthropic model to use. List of model names available
            [here](https://docs.anthropic.com/en/docs/about-claude/models).
        provider: The provider to use for the Anthropic API. Can be either the string 'anthropic' or an
            instance of `Provider[AsyncAnthropicClient]`. Defaults to 'anthropic'.
        profile: The model profile to use. Defaults to a profile picked by the provider based on the model name.
            The default 'anthropic' provider will use the default `..profiles.anthropic.anthropic_model_profile`.
        settings: Default model settings for this model instance.
    """
    self._model_name = model_name

    if isinstance(provider, str):
        provider = infer_provider('gateway/anthropic' if provider == 'gateway' else provider)
    self._provider = provider
    self.client = provider.client

    super().__init__(settings=settings, profile=profile or provider.model_profile)

```

#### model_name

```python
model_name: AnthropicModelName

```

The model name.

#### system

```python
system: str

```

The model provider.
