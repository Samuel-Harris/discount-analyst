### MistralStreamedResponse

Bases: `StreamedResponse`

Implementation of `StreamedResponse` for Mistral models.

Source code in `pydantic_ai_slim/pydantic_ai/models/mistral.py`

```python
@dataclass
class MistralStreamedResponse(StreamedResponse):
    """Implementation of `StreamedResponse` for Mistral models."""

    _model_name: MistralModelName
    _response: AsyncIterable[MistralCompletionEvent]
    _timestamp: datetime
    _provider_name: str

    _delta_content: str = field(default='', init=False)

    async def _get_event_iterator(self) -> AsyncIterator[ModelResponseStreamEvent]:
        chunk: MistralCompletionEvent
        async for chunk in self._response:
            self._usage += _map_usage(chunk.data)

            if chunk.data.id:  # pragma: no branch
                self.provider_response_id = chunk.data.id

            try:
                choice = chunk.data.choices[0]
            except IndexError:
                continue

            if raw_finish_reason := choice.finish_reason:
                self.provider_details = {'finish_reason': raw_finish_reason}
                self.finish_reason = _FINISH_REASON_MAP.get(raw_finish_reason)

            # Handle the text part of the response
            content = choice.delta.content
            text, thinking = _map_content(content)
            for thought in thinking:
                for event in self._parts_manager.handle_thinking_delta(vendor_part_id='thinking', content=thought):
                    yield event
            if text:
                # Attempt to produce an output tool call from the received text
                output_tools = {c.name: c for c in self.model_request_parameters.output_tools}
                if output_tools:
                    self._delta_content += text
                    # TODO: Port to native "manual JSON" mode
                    maybe_tool_call_part = self._try_get_output_tool_from_text(self._delta_content, output_tools)
                    if maybe_tool_call_part:
                        yield self._parts_manager.handle_tool_call_part(
                            vendor_part_id='output',
                            tool_name=maybe_tool_call_part.tool_name,
                            args=maybe_tool_call_part.args_as_dict(),
                            tool_call_id=maybe_tool_call_part.tool_call_id,
                        )
                else:
                    for event in self._parts_manager.handle_text_delta(vendor_part_id='content', content=text):
                        yield event

            # Handle the explicit tool calls
            for index, dtc in enumerate(choice.delta.tool_calls or []):
                # It seems that mistral just sends full tool calls, so we just use them directly, rather than building
                yield self._parts_manager.handle_tool_call_part(
                    vendor_part_id=index, tool_name=dtc.function.name, args=dtc.function.arguments, tool_call_id=dtc.id
                )

    @property
    def model_name(self) -> MistralModelName:
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

    @staticmethod
    def _try_get_output_tool_from_text(text: str, output_tools: dict[str, ToolDefinition]) -> ToolCallPart | None:
        output_json: dict[str, Any] | None = pydantic_core.from_json(text, allow_partial='trailing-strings')
        if output_json:
            for output_tool in output_tools.values():
                # NOTE: Additional verification to prevent JSON validation to crash
                # Ensures required parameters in the JSON schema are respected, especially for stream-based return types.
                # Example with BaseModel and required fields.
                if not MistralStreamedResponse._validate_required_json_schema(
                    output_json, output_tool.parameters_json_schema
                ):
                    continue

                # The following part_id will be thrown away
                return ToolCallPart(tool_name=output_tool.name, args=output_json)

    @staticmethod
    def _validate_required_json_schema(json_dict: dict[str, Any], json_schema: dict[str, Any]) -> bool:
        """Validate that all required parameters in the JSON schema are present in the JSON dictionary."""
        required_params = json_schema.get('required', [])
        properties = json_schema.get('properties', {})

        for param in required_params:
            if param not in json_dict:
                return False

            param_schema = properties.get(param, {})
            param_type = param_schema.get('type')
            param_items_type = param_schema.get('items', {}).get('type')

            if param_type == 'array' and param_items_type:
                if not isinstance(json_dict[param], list):
                    return False
                for item in json_dict[param]:
                    if not isinstance(item, VALID_JSON_TYPE_MAPPING[param_items_type]):
                        return False
            elif param_type and not isinstance(json_dict[param], VALID_JSON_TYPE_MAPPING[param_type]):
                return False

            if isinstance(json_dict[param], dict) and 'properties' in param_schema:
                nested_schema = param_schema
                if not MistralStreamedResponse._validate_required_json_schema(json_dict[param], nested_schema):
                    return False

        return True

```

#### model_name

```python
model_name: MistralModelName

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
