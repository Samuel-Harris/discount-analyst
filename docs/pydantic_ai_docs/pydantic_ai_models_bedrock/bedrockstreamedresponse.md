### BedrockStreamedResponse

Bases: `StreamedResponse`

Implementation of `StreamedResponse` for Bedrock models.

Source code in `pydantic_ai_slim/pydantic_ai/models/bedrock.py`

```python
@dataclass
class BedrockStreamedResponse(StreamedResponse):
    """Implementation of `StreamedResponse` for Bedrock models."""

    _model_name: BedrockModelName
    _event_stream: EventStream[ConverseStreamOutputTypeDef]
    _provider_name: str
    _timestamp: datetime = field(default_factory=_utils.now_utc)
    _provider_response_id: str | None = None

    async def _get_event_iterator(self) -> AsyncIterator[ModelResponseStreamEvent]:  # noqa: C901
        """Return an async iterator of [`ModelResponseStreamEvent`][pydantic_ai.messages.ModelResponseStreamEvent]s.

        This method should be implemented by subclasses to translate the vendor-specific stream of events into
        pydantic_ai-format events.
        """
        if self._provider_response_id is not None:  # pragma: no cover
            self.provider_response_id = self._provider_response_id

        chunk: ConverseStreamOutputTypeDef
        tool_id: str | None = None
        async for chunk in _AsyncIteratorWrapper(self._event_stream):
            match chunk:
                case {'messageStart': _}:
                    continue
                case {'messageStop': message_stop}:
                    raw_finish_reason = message_stop['stopReason']
                    self.provider_details = {'finish_reason': raw_finish_reason}
                    self.finish_reason = _FINISH_REASON_MAP.get(raw_finish_reason)
                case {'metadata': metadata}:
                    if 'usage' in metadata:  # pragma: no branch
                        self._usage += self._map_usage(metadata)
                case {'contentBlockStart': content_block_start}:
                    index = content_block_start['contentBlockIndex']
                    start = content_block_start['start']
                    if 'toolUse' in start:  # pragma: no branch
                        tool_use_start = start['toolUse']
                        tool_id = tool_use_start['toolUseId']
                        tool_name = tool_use_start['name']
                        maybe_event = self._parts_manager.handle_tool_call_delta(
                            vendor_part_id=index,
                            tool_name=tool_name,
                            args=None,
                            tool_call_id=tool_id,
                        )
                        if maybe_event:  # pragma: no branch
                            yield maybe_event
                case {'contentBlockDelta': content_block_delta}:
                    index = content_block_delta['contentBlockIndex']
                    delta = content_block_delta['delta']
                    if 'reasoningContent' in delta:
                        if redacted_content := delta['reasoningContent'].get('redactedContent'):
                            for event in self._parts_manager.handle_thinking_delta(
                                vendor_part_id=index,
                                id='redacted_content',
                                signature=redacted_content.decode('utf-8'),
                                provider_name=self.provider_name,
                            ):
                                yield event
                        else:
                            signature = delta['reasoningContent'].get('signature')
                            for event in self._parts_manager.handle_thinking_delta(
                                vendor_part_id=index,
                                content=delta['reasoningContent'].get('text'),
                                signature=signature,
                                provider_name=self.provider_name if signature else None,
                            ):
                                yield event
                    if text := delta.get('text'):
                        for event in self._parts_manager.handle_text_delta(vendor_part_id=index, content=text):
                            yield event
                    if 'toolUse' in delta:
                        tool_use = delta['toolUse']
                        maybe_event = self._parts_manager.handle_tool_call_delta(
                            vendor_part_id=index,
                            tool_name=tool_use.get('name'),
                            args=tool_use.get('input'),
                            tool_call_id=tool_id,
                        )
                        if maybe_event:  # pragma: no branch
                            yield maybe_event
                case _:
                    pass  # pyright wants match statements to be exhaustive

    @property
    def model_name(self) -> str:
        """Get the model name of the response."""
        return self._model_name

    @property
    def provider_name(self) -> str:
        """Get the provider name."""
        return self._provider_name

    @property
    def timestamp(self) -> datetime:
        return self._timestamp

    def _map_usage(self, metadata: ConverseStreamMetadataEventTypeDef) -> usage.RequestUsage:
        return usage.RequestUsage(
            input_tokens=metadata['usage']['inputTokens'],
            output_tokens=metadata['usage']['outputTokens'],
        )

```

#### model_name

```python
model_name: str

```

Get the model name of the response.

#### provider_name

```python
provider_name: str

```

Get the provider name.
