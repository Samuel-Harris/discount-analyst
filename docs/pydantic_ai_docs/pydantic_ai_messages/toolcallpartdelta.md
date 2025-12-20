### ToolCallPartDelta

A partial update (delta) for a `ToolCallPart` to modify tool name, arguments, or tool call ID.

Source code in `pydantic_ai_slim/pydantic_ai/messages.py`

```python
@dataclass(repr=False, kw_only=True)
class ToolCallPartDelta:
    """A partial update (delta) for a `ToolCallPart` to modify tool name, arguments, or tool call ID."""

    tool_name_delta: str | None = None
    """Incremental text to add to the existing tool name, if any."""

    args_delta: str | dict[str, Any] | None = None
    """Incremental data to add to the tool arguments.

    If this is a string, it will be appended to existing JSON arguments.
    If this is a dict, it will be merged with existing dict arguments.
    """

    tool_call_id: str | None = None
    """Optional tool call identifier, this is used by some models including OpenAI.

    Note this is never treated as a delta â€” it can replace None, but otherwise if a
    non-matching value is provided an error will be raised."""

    provider_details: dict[str, Any] | None = None
    """Additional data returned by the provider that can't be mapped to standard fields.

    This is used for data that is required to be sent back to APIs, as well as data users may want to access programmatically."""

    part_delta_kind: Literal['tool_call'] = 'tool_call'
    """Part delta type identifier, used as a discriminator."""

    def as_part(self) -> ToolCallPart | None:
        """Convert this delta to a fully formed `ToolCallPart` if possible, otherwise return `None`.

        Returns:
            A `ToolCallPart` if `tool_name_delta` is set, otherwise `None`.
        """
        if self.tool_name_delta is None:
            return None

        return ToolCallPart(self.tool_name_delta, self.args_delta, self.tool_call_id or _generate_tool_call_id())

    @overload
    def apply(self, part: ModelResponsePart) -> ToolCallPart | BuiltinToolCallPart: ...

    @overload
    def apply(
        self, part: ModelResponsePart | ToolCallPartDelta
    ) -> ToolCallPart | BuiltinToolCallPart | ToolCallPartDelta: ...

    def apply(
        self, part: ModelResponsePart | ToolCallPartDelta
    ) -> ToolCallPart | BuiltinToolCallPart | ToolCallPartDelta:
        """Apply this delta to a part or delta, returning a new part or delta with the changes applied.

        Args:
            part: The existing model response part or delta to update.

        Returns:
            Either a new `ToolCallPart` or `BuiltinToolCallPart`, or an updated `ToolCallPartDelta`.

        Raises:
            ValueError: If `part` is neither a `ToolCallPart`, `BuiltinToolCallPart`, nor a `ToolCallPartDelta`.
            UnexpectedModelBehavior: If applying JSON deltas to dict arguments or vice versa.
        """
        if isinstance(part, ToolCallPart | BuiltinToolCallPart):
            return self._apply_to_part(part)

        if isinstance(part, ToolCallPartDelta):
            return self._apply_to_delta(part)

        raise ValueError(  # pragma: no cover
            f'Can only apply ToolCallPartDeltas to ToolCallParts, BuiltinToolCallParts, or ToolCallPartDeltas, not {part}'
        )

    def _apply_to_delta(self, delta: ToolCallPartDelta) -> ToolCallPart | BuiltinToolCallPart | ToolCallPartDelta:
        """Internal helper to apply this delta to another delta."""
        if self.tool_name_delta:
            # Append incremental text to the existing tool_name_delta
            updated_tool_name_delta = (delta.tool_name_delta or '') + self.tool_name_delta
            delta = replace(delta, tool_name_delta=updated_tool_name_delta)

        if isinstance(self.args_delta, str):
            if isinstance(delta.args_delta, dict):
                raise UnexpectedModelBehavior(
                    f'Cannot apply JSON deltas to non-JSON tool arguments ({delta=}, {self=})'
                )
            updated_args_delta = (delta.args_delta or '') + self.args_delta
            delta = replace(delta, args_delta=updated_args_delta)
        elif isinstance(self.args_delta, dict):
            if isinstance(delta.args_delta, str):
                raise UnexpectedModelBehavior(
                    f'Cannot apply dict deltas to non-dict tool arguments ({delta=}, {self=})'
                )
            updated_args_delta = {**(delta.args_delta or {}), **self.args_delta}
            delta = replace(delta, args_delta=updated_args_delta)

        if self.tool_call_id:
            delta = replace(delta, tool_call_id=self.tool_call_id)

        # If we now have enough data to create a full ToolCallPart, do so
        if delta.tool_name_delta is not None:
            return ToolCallPart(delta.tool_name_delta, delta.args_delta, delta.tool_call_id or _generate_tool_call_id())

        return delta

    def _apply_to_part(self, part: ToolCallPart | BuiltinToolCallPart) -> ToolCallPart | BuiltinToolCallPart:
        """Internal helper to apply this delta directly to a `ToolCallPart` or `BuiltinToolCallPart`."""
        if self.tool_name_delta:
            # Append incremental text to the existing tool_name
            tool_name = part.tool_name + self.tool_name_delta
            part = replace(part, tool_name=tool_name)

        if isinstance(self.args_delta, str):
            if isinstance(part.args, dict):
                raise UnexpectedModelBehavior(f'Cannot apply JSON deltas to non-JSON tool arguments ({part=}, {self=})')
            updated_json = (part.args or '') + self.args_delta
            part = replace(part, args=updated_json)
        elif isinstance(self.args_delta, dict):
            if isinstance(part.args, str):
                raise UnexpectedModelBehavior(f'Cannot apply dict deltas to non-dict tool arguments ({part=}, {self=})')
            updated_dict = {**(part.args or {}), **self.args_delta}
            part = replace(part, args=updated_dict)

        if self.tool_call_id:
            part = replace(part, tool_call_id=self.tool_call_id)
        return part

    __repr__ = _utils.dataclasses_no_defaults_repr

```

#### tool_name_delta

```python
tool_name_delta: str | None = None

```

Incremental text to add to the existing tool name, if any.

#### args_delta

```python
args_delta: str | dict[str, Any] | None = None

```

Incremental data to add to the tool arguments.

If this is a string, it will be appended to existing JSON arguments. If this is a dict, it will be merged with existing dict arguments.

#### tool_call_id

```python
tool_call_id: str | None = None

```

Optional tool call identifier, this is used by some models including OpenAI.

Note this is never treated as a delta â€” it can replace None, but otherwise if a non-matching value is provided an error will be raised.

#### provider_details

```python
provider_details: dict[str, Any] | None = None

```

Additional data returned by the provider that can't be mapped to standard fields.

This is used for data that is required to be sent back to APIs, as well as data users may want to access programmatically.

#### part_delta_kind

```python
part_delta_kind: Literal['tool_call'] = 'tool_call'

```

Part delta type identifier, used as a discriminator.

#### as_part

```python
as_part() -> ToolCallPart | None

```

Convert this delta to a fully formed `ToolCallPart` if possible, otherwise return `None`.

Returns:

| Type | Description | | --- | --- | | `ToolCallPart | None` | A ToolCallPart if tool_name_delta is set, otherwise None. |

Source code in `pydantic_ai_slim/pydantic_ai/messages.py`

```python
def as_part(self) -> ToolCallPart | None:
    """Convert this delta to a fully formed `ToolCallPart` if possible, otherwise return `None`.

    Returns:
        A `ToolCallPart` if `tool_name_delta` is set, otherwise `None`.
    """
    if self.tool_name_delta is None:
        return None

    return ToolCallPart(self.tool_name_delta, self.args_delta, self.tool_call_id or _generate_tool_call_id())

```

#### apply

```python
apply(
    part: ModelResponsePart,
) -> ToolCallPart | BuiltinToolCallPart

```

```python
apply(
    part: ModelResponsePart | ToolCallPartDelta,
) -> ToolCallPart | BuiltinToolCallPart | ToolCallPartDelta

```

```python
apply(
    part: ModelResponsePart | ToolCallPartDelta,
) -> ToolCallPart | BuiltinToolCallPart | ToolCallPartDelta

```

Apply this delta to a part or delta, returning a new part or delta with the changes applied.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `part` | `ModelResponsePart | ToolCallPartDelta` | The existing model response part or delta to update. | _required_ |

Returns:

| Type | Description | | --- | --- | | `ToolCallPart | BuiltinToolCallPart | ToolCallPartDelta` | Either a new ToolCallPart or BuiltinToolCallPart, or an updated ToolCallPartDelta. |

Raises:

| Type | Description | | --- | --- | | `ValueError` | If part is neither a ToolCallPart, BuiltinToolCallPart, nor a ToolCallPartDelta. | | `UnexpectedModelBehavior` | If applying JSON deltas to dict arguments or vice versa. |

Source code in `pydantic_ai_slim/pydantic_ai/messages.py`

```python
def apply(
    self, part: ModelResponsePart | ToolCallPartDelta
) -> ToolCallPart | BuiltinToolCallPart | ToolCallPartDelta:
    """Apply this delta to a part or delta, returning a new part or delta with the changes applied.

    Args:
        part: The existing model response part or delta to update.

    Returns:
        Either a new `ToolCallPart` or `BuiltinToolCallPart`, or an updated `ToolCallPartDelta`.

    Raises:
        ValueError: If `part` is neither a `ToolCallPart`, `BuiltinToolCallPart`, nor a `ToolCallPartDelta`.
        UnexpectedModelBehavior: If applying JSON deltas to dict arguments or vice versa.
    """
    if isinstance(part, ToolCallPart | BuiltinToolCallPart):
        return self._apply_to_part(part)

    if isinstance(part, ToolCallPartDelta):
        return self._apply_to_delta(part)

    raise ValueError(  # pragma: no cover
        f'Can only apply ToolCallPartDeltas to ToolCallParts, BuiltinToolCallParts, or ToolCallPartDeltas, not {part}'
    )

```
