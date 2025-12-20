### StreamedResponse

Bases: `ABC`

Streamed response from an LLM when calling a tool.

Source code in `pydantic_ai_slim/pydantic_ai/models/__init__.py`

```python
@dataclass
class StreamedResponse(ABC):
    """Streamed response from an LLM when calling a tool."""

    model_request_parameters: ModelRequestParameters

    final_result_event: FinalResultEvent | None = field(default=None, init=False)

    provider_response_id: str | None = field(default=None, init=False)
    provider_details: dict[str, Any] | None = field(default=None, init=False)
    finish_reason: FinishReason | None = field(default=None, init=False)

    _parts_manager: ModelResponsePartsManager = field(default_factory=ModelResponsePartsManager, init=False)
    _event_iterator: AsyncIterator[ModelResponseStreamEvent] | None = field(default=None, init=False)
    _usage: RequestUsage = field(default_factory=RequestUsage, init=False)

    def __aiter__(self) -> AsyncIterator[ModelResponseStreamEvent]:
        """Stream the response as an async iterable of [`ModelResponseStreamEvent`][pydantic_ai.messages.ModelResponseStreamEvent]s.

        This proxies the `_event_iterator()` and emits all events, while also checking for matches
        on the result schema and emitting a [`FinalResultEvent`][pydantic_ai.messages.FinalResultEvent] if/when the
        first match is found.
        """
        if self._event_iterator is None:

            async def iterator_with_final_event(
                iterator: AsyncIterator[ModelResponseStreamEvent],
            ) -> AsyncIterator[ModelResponseStreamEvent]:
                async for event in iterator:
                    yield event
                    if (
                        final_result_event := _get_final_result_event(event, self.model_request_parameters)
                    ) is not None:
                        self.final_result_event = final_result_event
                        yield final_result_event
                        break

                # If we broke out of the above loop, we need to yield the rest of the events
                # If we didn't, this will just be a no-op
                async for event in iterator:
                    yield event

            async def iterator_with_part_end(
                iterator: AsyncIterator[ModelResponseStreamEvent],
            ) -> AsyncIterator[ModelResponseStreamEvent]:
                last_start_event: PartStartEvent | None = None

                def part_end_event(next_part: ModelResponsePart | None = None) -> PartEndEvent | None:
                    if not last_start_event:
                        return None

                    index = last_start_event.index
                    part = self._parts_manager.get_parts()[index]
                    if not isinstance(part, TextPart | ThinkingPart | BaseToolCallPart):
                        # Parts other than these 3 don't have deltas, so don't need an end part.
                        return None

                    return PartEndEvent(
                        index=index,
                        part=part,
                        next_part_kind=next_part.part_kind if next_part else None,
                    )

                async for event in iterator:
                    if isinstance(event, PartStartEvent):
                        if last_start_event:
                            end_event = part_end_event(event.part)
                            if end_event:
                                yield end_event

                            event.previous_part_kind = last_start_event.part.part_kind
                        last_start_event = event

                    yield event

                end_event = part_end_event()
                if end_event:
                    yield end_event

            self._event_iterator = iterator_with_part_end(iterator_with_final_event(self._get_event_iterator()))
        return self._event_iterator

    @abstractmethod
    async def _get_event_iterator(self) -> AsyncIterator[ModelResponseStreamEvent]:
        """Return an async iterator of [`ModelResponseStreamEvent`][pydantic_ai.messages.ModelResponseStreamEvent]s.

        This method should be implemented by subclasses to translate the vendor-specific stream of events into
        pydantic_ai-format events.

        It should use the `_parts_manager` to handle deltas, and should update the `_usage` attributes as it goes.
        """
        raise NotImplementedError()
        # noinspection PyUnreachableCode
        yield

    def get(self) -> ModelResponse:
        """Build a [`ModelResponse`][pydantic_ai.messages.ModelResponse] from the data received from the stream so far."""
        return ModelResponse(
            parts=self._parts_manager.get_parts(),
            model_name=self.model_name,
            timestamp=self.timestamp,
            usage=self.usage(),
            provider_name=self.provider_name,
            provider_response_id=self.provider_response_id,
            provider_details=self.provider_details,
            finish_reason=self.finish_reason,
        )

    # TODO (v2): Make this a property
    def usage(self) -> RequestUsage:
        """Get the usage of the response so far. This will not be the final usage until the stream is exhausted."""
        return self._usage

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Get the model name of the response."""
        raise NotImplementedError()

    @property
    @abstractmethod
    def provider_name(self) -> str | None:
        """Get the provider name."""
        raise NotImplementedError()

    @property
    @abstractmethod
    def timestamp(self) -> datetime:
        """Get the timestamp of the response."""
        raise NotImplementedError()

```

#### **aiter**

```python
__aiter__() -> AsyncIterator[ModelResponseStreamEvent]

```

Stream the response as an async iterable of ModelResponseStreamEvents.

This proxies the `_event_iterator()` and emits all events, while also checking for matches on the result schema and emitting a FinalResultEvent if/when the first match is found.

Source code in `pydantic_ai_slim/pydantic_ai/models/__init__.py`

```python
def __aiter__(self) -> AsyncIterator[ModelResponseStreamEvent]:
    """Stream the response as an async iterable of [`ModelResponseStreamEvent`][pydantic_ai.messages.ModelResponseStreamEvent]s.

    This proxies the `_event_iterator()` and emits all events, while also checking for matches
    on the result schema and emitting a [`FinalResultEvent`][pydantic_ai.messages.FinalResultEvent] if/when the
    first match is found.
    """
    if self._event_iterator is None:

        async def iterator_with_final_event(
            iterator: AsyncIterator[ModelResponseStreamEvent],
        ) -> AsyncIterator[ModelResponseStreamEvent]:
            async for event in iterator:
                yield event
                if (
                    final_result_event := _get_final_result_event(event, self.model_request_parameters)
                ) is not None:
                    self.final_result_event = final_result_event
                    yield final_result_event
                    break

            # If we broke out of the above loop, we need to yield the rest of the events
            # If we didn't, this will just be a no-op
            async for event in iterator:
                yield event

        async def iterator_with_part_end(
            iterator: AsyncIterator[ModelResponseStreamEvent],
        ) -> AsyncIterator[ModelResponseStreamEvent]:
            last_start_event: PartStartEvent | None = None

            def part_end_event(next_part: ModelResponsePart | None = None) -> PartEndEvent | None:
                if not last_start_event:
                    return None

                index = last_start_event.index
                part = self._parts_manager.get_parts()[index]
                if not isinstance(part, TextPart | ThinkingPart | BaseToolCallPart):
                    # Parts other than these 3 don't have deltas, so don't need an end part.
                    return None

                return PartEndEvent(
                    index=index,
                    part=part,
                    next_part_kind=next_part.part_kind if next_part else None,
                )

            async for event in iterator:
                if isinstance(event, PartStartEvent):
                    if last_start_event:
                        end_event = part_end_event(event.part)
                        if end_event:
                            yield end_event

                        event.previous_part_kind = last_start_event.part.part_kind
                    last_start_event = event

                yield event

            end_event = part_end_event()
            if end_event:
                yield end_event

        self._event_iterator = iterator_with_part_end(iterator_with_final_event(self._get_event_iterator()))
    return self._event_iterator

```

#### get

```python
get() -> ModelResponse

```

Build a ModelResponse from the data received from the stream so far.

Source code in `pydantic_ai_slim/pydantic_ai/models/__init__.py`

```python
def get(self) -> ModelResponse:
    """Build a [`ModelResponse`][pydantic_ai.messages.ModelResponse] from the data received from the stream so far."""
    return ModelResponse(
        parts=self._parts_manager.get_parts(),
        model_name=self.model_name,
        timestamp=self.timestamp,
        usage=self.usage(),
        provider_name=self.provider_name,
        provider_response_id=self.provider_response_id,
        provider_details=self.provider_details,
        finish_reason=self.finish_reason,
    )

```

#### usage

```python
usage() -> RequestUsage

```

Get the usage of the response so far. This will not be the final usage until the stream is exhausted.

Source code in `pydantic_ai_slim/pydantic_ai/models/__init__.py`

```python
def usage(self) -> RequestUsage:
    """Get the usage of the response so far. This will not be the final usage until the stream is exhausted."""
    return self._usage

```

#### model_name

```python
model_name: str

```

Get the model name of the response.

#### provider_name

```python
provider_name: str | None

```

Get the provider name.

#### timestamp

```python
timestamp: datetime

```

Get the timestamp of the response.
