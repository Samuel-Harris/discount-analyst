### GroqStreamedResponse

Bases: `StreamedResponse`

Implementation of `StreamedResponse` for Groq models.

Source code in `pydantic_ai_slim/pydantic_ai/models/groq.py`

```python
@dataclass
class GroqStreamedResponse(StreamedResponse):
    """Implementation of `StreamedResponse` for Groq models."""

    _model_name: GroqModelName
    _model_profile: ModelProfile
    _response: AsyncIterable[chat.ChatCompletionChunk]
    _timestamp: datetime
    _provider_name: str

    async def _get_event_iterator(self) -> AsyncIterator[ModelResponseStreamEvent]:  # noqa: C901
        try:
            executed_tool_call_id: str | None = None
            reasoning_index = 0
            reasoning = False
            async for chunk in self._response:
                self._usage += _map_usage(chunk)

                if chunk.id:  # pragma: no branch
                    self.provider_response_id = chunk.id

                try:
                    choice = chunk.choices[0]
                except IndexError:
                    continue

                if raw_finish_reason := choice.finish_reason:
                    self.provider_details = {'finish_reason': raw_finish_reason}
                    self.finish_reason = _FINISH_REASON_MAP.get(raw_finish_reason)

                if choice.delta.reasoning is not None:
                    if not reasoning:
                        reasoning_index += 1
                        reasoning = True

                    # NOTE: The `reasoning` field is only present if `groq_reasoning_format` is set to `parsed`.
                    for event in self._parts_manager.handle_thinking_delta(
                        vendor_part_id=f'reasoning-{reasoning_index}', content=choice.delta.reasoning
                    ):
                        yield event
                else:
                    reasoning = False

                if choice.delta.executed_tools:
                    for tool in choice.delta.executed_tools:
                        call_part, return_part = _map_executed_tool(
                            tool, self.provider_name, streaming=True, tool_call_id=executed_tool_call_id
                        )
                        if call_part:
                            executed_tool_call_id = call_part.tool_call_id
                            yield self._parts_manager.handle_part(
                                vendor_part_id=f'executed_tools-{tool.index}-call', part=call_part
                            )
                        if return_part:
                            executed_tool_call_id = None
                            yield self._parts_manager.handle_part(
                                vendor_part_id=f'executed_tools-{tool.index}-return', part=return_part
                            )

                # Handle the text part of the response
                content = choice.delta.content
                if content:
                    for event in self._parts_manager.handle_text_delta(
                        vendor_part_id='content',
                        content=content,
                        thinking_tags=self._model_profile.thinking_tags,
                        ignore_leading_whitespace=self._model_profile.ignore_streamed_leading_whitespace,
                    ):
                        yield event

                # Handle the tool calls
                for dtc in choice.delta.tool_calls or []:
                    maybe_event = self._parts_manager.handle_tool_call_delta(
                        vendor_part_id=dtc.index,
                        tool_name=dtc.function and dtc.function.name,
                        args=dtc.function and dtc.function.arguments,
                        tool_call_id=dtc.id,
                    )
                    if maybe_event is not None:
                        yield maybe_event
        except APIError as e:
            if isinstance(e.body, dict):  # pragma: no branch
                # The Groq SDK tries to be helpful by raising an exception when generated tool arguments don't match the schema,
                # but we'd rather handle it ourselves so we can tell the model to retry the tool call
                try:
                    error = _GroqToolUseFailedInnerError.model_validate(e.body)  # pyright: ignore[reportUnknownMemberType]
                    yield self._parts_manager.handle_tool_call_part(
                        vendor_part_id='tool_use_failed',
                        tool_name=error.failed_generation.name,
                        args=error.failed_generation.arguments,
                    )
                    return
                except ValidationError as e:  # pragma: no cover
                    pass
            raise  # pragma: no cover

    @property
    def model_name(self) -> GroqModelName:
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
model_name: GroqModelName

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
