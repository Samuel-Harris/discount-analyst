### OpenRouterStreamedResponse

Bases: `OpenAIStreamedResponse`

Implementation of `StreamedResponse` for OpenRouter models.

Source code in `pydantic_ai_slim/pydantic_ai/models/openrouter.py`

```python
@dataclass
class OpenRouterStreamedResponse(OpenAIStreamedResponse):
    """Implementation of `StreamedResponse` for OpenRouter models."""

    @override
    async def _validate_response(self):
        try:
            async for chunk in self._response:
                yield _OpenRouterChatCompletionChunk.model_validate(chunk.model_dump())
        except APIError as e:
            error = _OpenRouterError.model_validate(e.body)
            raise ModelHTTPError(status_code=error.code, model_name=self._model_name, body=error.message)

    @override
    def _map_thinking_delta(self, choice: chat_completion_chunk.Choice) -> Iterable[ModelResponseStreamEvent]:
        assert isinstance(choice, _OpenRouterChunkChoice)

        if reasoning_details := choice.delta.reasoning_details:
            for i, detail in enumerate(reasoning_details):
                thinking_part = _from_reasoning_detail(detail)
                # Use unique vendor_part_id for each reasoning detail type to prevent
                # different detail types (e.g., reasoning.text, reasoning.encrypted)
                # from being incorrectly merged into a single ThinkingPart.
                # This is required for Gemini 3 Pro which returns multiple reasoning
                # detail types that must be preserved separately for thought_signature handling.
                vendor_id = f'reasoning_detail_{detail.type}_{i}'
                yield from self._parts_manager.handle_thinking_delta(
                    vendor_part_id=vendor_id,
                    id=thinking_part.id,
                    content=thinking_part.content,
                    signature=thinking_part.signature,
                    provider_name=self._provider_name,
                    provider_details=thinking_part.provider_details,
                )
        else:
            return super()._map_thinking_delta(choice)

    @override
    def _map_provider_details(self, chunk: chat.ChatCompletionChunk) -> dict[str, Any] | None:
        assert isinstance(chunk, _OpenRouterChatCompletionChunk)

        if provider_details := super()._map_provider_details(chunk):
            provider_details.update(_map_openrouter_provider_details(chunk))
            return provider_details

    @override
    def _map_finish_reason(  # type: ignore[reportIncompatibleMethodOverride]
        self, key: Literal['stop', 'length', 'tool_calls', 'content_filter', 'error']
    ) -> FinishReason | None:
        return _CHAT_FINISH_REASON_MAP.get(key)

```
