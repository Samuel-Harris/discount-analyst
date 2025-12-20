### AnthropicStreamedResponse

Bases: `StreamedResponse`

Implementation of `StreamedResponse` for Anthropic models.

Source code in `pydantic_ai_slim/pydantic_ai/models/anthropic.py`

```python
@dataclass
class AnthropicStreamedResponse(StreamedResponse):
    """Implementation of `StreamedResponse` for Anthropic models."""

    _model_name: AnthropicModelName
    _response: AsyncIterable[BetaRawMessageStreamEvent]
    _timestamp: datetime
    _provider_name: str
    _provider_url: str

    async def _get_event_iterator(self) -> AsyncIterator[ModelResponseStreamEvent]:  # noqa: C901
        current_block: BetaContentBlock | None = None

        builtin_tool_calls: dict[str, BuiltinToolCallPart] = {}
        async for event in self._response:
            if isinstance(event, BetaRawMessageStartEvent):
                self._usage = _map_usage(event, self._provider_name, self._provider_url, self._model_name)
                self.provider_response_id = event.message.id

            elif isinstance(event, BetaRawContentBlockStartEvent):
                current_block = event.content_block
                if isinstance(current_block, BetaTextBlock) and current_block.text:
                    for event_ in self._parts_manager.handle_text_delta(
                        vendor_part_id=event.index, content=current_block.text
                    ):
                        yield event_
                elif isinstance(current_block, BetaThinkingBlock):
                    for event_ in self._parts_manager.handle_thinking_delta(
                        vendor_part_id=event.index,
                        content=current_block.thinking,
                        signature=current_block.signature,
                        provider_name=self.provider_name,
                    ):
                        yield event_
                elif isinstance(current_block, BetaRedactedThinkingBlock):
                    for event_ in self._parts_manager.handle_thinking_delta(
                        vendor_part_id=event.index,
                        id='redacted_thinking',
                        signature=current_block.data,
                        provider_name=self.provider_name,
                    ):
                        yield event_
                elif isinstance(current_block, BetaToolUseBlock):
                    maybe_event = self._parts_manager.handle_tool_call_delta(
                        vendor_part_id=event.index,
                        tool_name=current_block.name,
                        args=cast(dict[str, Any], current_block.input) or None,
                        tool_call_id=current_block.id,
                    )
                    if maybe_event is not None:  # pragma: no branch
                        yield maybe_event
                elif isinstance(current_block, BetaServerToolUseBlock):
                    call_part = _map_server_tool_use_block(current_block, self.provider_name)
                    builtin_tool_calls[call_part.tool_call_id] = call_part
                    yield self._parts_manager.handle_part(
                        vendor_part_id=event.index,
                        part=call_part,
                    )
                elif isinstance(current_block, BetaWebSearchToolResultBlock):
                    yield self._parts_manager.handle_part(
                        vendor_part_id=event.index,
                        part=_map_web_search_tool_result_block(current_block, self.provider_name),
                    )
                elif isinstance(current_block, BetaCodeExecutionToolResultBlock):
                    yield self._parts_manager.handle_part(
                        vendor_part_id=event.index,
                        part=_map_code_execution_tool_result_block(current_block, self.provider_name),
                    )
                elif isinstance(current_block, BetaWebFetchToolResultBlock):  # pragma: lax no cover
                    yield self._parts_manager.handle_part(
                        vendor_part_id=event.index,
                        part=_map_web_fetch_tool_result_block(current_block, self.provider_name),
                    )
                elif isinstance(current_block, BetaMCPToolUseBlock):
                    call_part = _map_mcp_server_use_block(current_block, self.provider_name)
                    builtin_tool_calls[call_part.tool_call_id] = call_part

                    args_json = call_part.args_as_json_str()
                    # Drop the final `{}}` so that we can add tool args deltas
                    args_json_delta = args_json[:-3]
                    assert args_json_delta.endswith('"tool_args":'), (
                        f'Expected {args_json_delta!r} to end in `"tool_args":`'
                    )

                    yield self._parts_manager.handle_part(
                        vendor_part_id=event.index, part=replace(call_part, args=None)
                    )
                    maybe_event = self._parts_manager.handle_tool_call_delta(
                        vendor_part_id=event.index,
                        args=args_json_delta,
                    )
                    if maybe_event is not None:  # pragma: no branch
                        yield maybe_event
                elif isinstance(current_block, BetaMCPToolResultBlock):
                    call_part = builtin_tool_calls.get(current_block.tool_use_id)
                    yield self._parts_manager.handle_part(
                        vendor_part_id=event.index,
                        part=_map_mcp_server_result_block(current_block, call_part, self.provider_name),
                    )

            elif isinstance(event, BetaRawContentBlockDeltaEvent):
                if isinstance(event.delta, BetaTextDelta):
                    for event_ in self._parts_manager.handle_text_delta(
                        vendor_part_id=event.index, content=event.delta.text
                    ):
                        yield event_
                elif isinstance(event.delta, BetaThinkingDelta):
                    for event_ in self._parts_manager.handle_thinking_delta(
                        vendor_part_id=event.index,
                        content=event.delta.thinking,
                        provider_name=self.provider_name,
                    ):
                        yield event_
                elif isinstance(event.delta, BetaSignatureDelta):
                    for event_ in self._parts_manager.handle_thinking_delta(
                        vendor_part_id=event.index,
                        signature=event.delta.signature,
                        provider_name=self.provider_name,
                    ):
                        yield event_
                elif isinstance(event.delta, BetaInputJSONDelta):
                    maybe_event = self._parts_manager.handle_tool_call_delta(
                        vendor_part_id=event.index,
                        args=event.delta.partial_json,
                    )
                    if maybe_event is not None:  # pragma: no branch
                        yield maybe_event
                # TODO(Marcelo): We need to handle citations.
                elif isinstance(event.delta, BetaCitationsDelta):
                    pass

            elif isinstance(event, BetaRawMessageDeltaEvent):
                self._usage = _map_usage(event, self._provider_name, self._provider_url, self._model_name, self._usage)
                if raw_finish_reason := event.delta.stop_reason:  # pragma: no branch
                    self.provider_details = {'finish_reason': raw_finish_reason}
                    self.finish_reason = _FINISH_REASON_MAP.get(raw_finish_reason)

            elif isinstance(event, BetaRawContentBlockStopEvent):  # pragma: no branch
                if isinstance(current_block, BetaMCPToolUseBlock):
                    maybe_event = self._parts_manager.handle_tool_call_delta(
                        vendor_part_id=event.index,
                        args='}',
                    )
                    if maybe_event is not None:  # pragma: no branch
                        yield maybe_event
                current_block = None
            elif isinstance(event, BetaRawMessageStopEvent):  # pragma: no branch
                current_block = None

    @property
    def model_name(self) -> AnthropicModelName:
        """Get the model name of the response."""
        return self._model_name

    @property
    def provider_name(self) -> str:
        """Get the provider name."""
        return self._provider_name

    @property
    def timestamp(self) -> datetime:
        """Get the timestamp of the response."""
        return self._timestamp

```

#### model_name

```python
model_name: AnthropicModelName

```

Get the model name of the response.

#### provider_name

```python
provider_name: str

```

Get the provider name.

#### timestamp

```python
timestamp: datetime

```

Get the timestamp of the response.
