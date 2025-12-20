### OutlinesStreamedResponse

Bases: `StreamedResponse`

Implementation of `StreamedResponse` for Outlines models.

Source code in `pydantic_ai_slim/pydantic_ai/models/outlines.py`

```python
@dataclass
class OutlinesStreamedResponse(StreamedResponse):
    """Implementation of `StreamedResponse` for Outlines models."""

    _model_name: str
    _model_profile: ModelProfile
    _response: AsyncIterable[str]
    _timestamp: datetime
    _provider_name: str

    async def _get_event_iterator(self) -> AsyncIterator[ModelResponseStreamEvent]:
        async for content in self._response:
            for event in self._parts_manager.handle_text_delta(
                vendor_part_id='content',
                content=content,
                thinking_tags=self._model_profile.thinking_tags,
                ignore_leading_whitespace=self._model_profile.ignore_streamed_leading_whitespace,
            ):
                yield event

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
provider_name: str

```

Get the provider name.

#### timestamp

```python
timestamp: datetime

```

Get the timestamp of the response.
