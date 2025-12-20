### FunctionStreamedResponse

Bases: `StreamedResponse`

Implementation of `StreamedResponse` for FunctionModel.

Source code in `pydantic_ai_slim/pydantic_ai/models/function.py`

```python
@dataclass
class FunctionStreamedResponse(StreamedResponse):
    """Implementation of `StreamedResponse` for [FunctionModel][pydantic_ai.models.function.FunctionModel]."""

    _model_name: str
    _iter: AsyncIterator[str | DeltaToolCalls | DeltaThinkingCalls | BuiltinToolCallsReturns]
    _timestamp: datetime = field(default_factory=_utils.now_utc)

    def __post_init__(self):
        self._usage += _estimate_usage([])

    async def _get_event_iterator(self) -> AsyncIterator[ModelResponseStreamEvent]:  # noqa: C901
        async for item in self._iter:
            if isinstance(item, str):
                response_tokens = _estimate_string_tokens(item)
                self._usage += usage.RequestUsage(output_tokens=response_tokens)
                for event in self._parts_manager.handle_text_delta(vendor_part_id='content', content=item):
                    yield event
            elif isinstance(item, dict) and item:
                for dtc_index, delta in item.items():
                    if isinstance(delta, DeltaThinkingPart):
                        if delta.content:  # pragma: no branch
                            response_tokens = _estimate_string_tokens(delta.content)
                            self._usage += usage.RequestUsage(output_tokens=response_tokens)
                        for event in self._parts_manager.handle_thinking_delta(
                            vendor_part_id=dtc_index,
                            content=delta.content,
                            signature=delta.signature,
                            provider_name='function' if delta.signature else None,
                        ):
                            yield event
                    elif isinstance(delta, DeltaToolCall):
                        if delta.json_args:
                            response_tokens = _estimate_string_tokens(delta.json_args)
                            self._usage += usage.RequestUsage(output_tokens=response_tokens)
                        maybe_event = self._parts_manager.handle_tool_call_delta(
                            vendor_part_id=dtc_index,
                            tool_name=delta.name,
                            args=delta.json_args,
                            tool_call_id=delta.tool_call_id,
                        )
                        if maybe_event is not None:  # pragma: no branch
                            yield maybe_event
                    elif isinstance(delta, BuiltinToolCallPart):
                        if content := delta.args_as_json_str():  # pragma: no branch
                            response_tokens = _estimate_string_tokens(content)
                            self._usage += usage.RequestUsage(output_tokens=response_tokens)
                        yield self._parts_manager.handle_part(vendor_part_id=dtc_index, part=delta)
                    elif isinstance(delta, BuiltinToolReturnPart):
                        if content := delta.model_response_str():  # pragma: no branch
                            response_tokens = _estimate_string_tokens(content)
                            self._usage += usage.RequestUsage(output_tokens=response_tokens)
                        yield self._parts_manager.handle_part(vendor_part_id=dtc_index, part=delta)
                    else:
                        assert_never(delta)

    @property
    def model_name(self) -> str:
        """Get the model name of the response."""
        return self._model_name

    @property
    def provider_name(self) -> None:
        """Get the provider name."""
        return None

    @property
    def timestamp(self) -> datetime:
        """Get the timestamp of the response."""
        return self._timestamp

```

#### model_name

```python
model_name: str

```

Get the model name of the response.

#### provider_name

```python
provider_name: None

```

Get the provider name.

#### timestamp

```python
timestamp: datetime

```

Get the timestamp of the response.
