### BaseToolCallPart

A tool call from a model.

Source code in `pydantic_ai_slim/pydantic_ai/messages.py`

```python
@dataclass(repr=False)
class BaseToolCallPart:
    """A tool call from a model."""

    tool_name: str
    """The name of the tool to call."""

    args: str | dict[str, Any] | None = None
    """The arguments to pass to the tool.

    This is stored either as a JSON string or a Python dictionary depending on how data was received.
    """

    tool_call_id: str = field(default_factory=_generate_tool_call_id)
    """The tool call identifier, this is used by some models including OpenAI.

    In case the tool call id is not provided by the model, Pydantic AI will generate a random one.
    """

    _: KW_ONLY

    id: str | None = None
    """An optional identifier of the tool call part, separate from the tool call ID.

    This is used by some APIs like OpenAI Responses."""

    provider_details: dict[str, Any] | None = None
    """Additional data returned by the provider that can't be mapped to standard fields.

    This is used for data that is required to be sent back to APIs, as well as data users may want to access programmatically."""

    def args_as_dict(self) -> dict[str, Any]:
        """Return the arguments as a Python dictionary.

        This is just for convenience with models that require dicts as input.
        """
        if not self.args:
            return {}
        if isinstance(self.args, dict):
            return self.args
        args = pydantic_core.from_json(self.args)
        assert isinstance(args, dict), 'args should be a dict'
        return cast(dict[str, Any], args)

    def args_as_json_str(self) -> str:
        """Return the arguments as a JSON string.

        This is just for convenience with models that require JSON strings as input.
        """
        if not self.args:
            return '{}'
        if isinstance(self.args, str):
            return self.args
        return pydantic_core.to_json(self.args).decode()

    def has_content(self) -> bool:
        """Return `True` if the arguments contain any data."""
        if isinstance(self.args, dict):
            # TODO: This should probably return True if you have the value False, or 0, etc.
            #   It makes sense to me to ignore empty strings, but not sure about empty lists or dicts
            return any(self.args.values())
        else:
            return bool(self.args)

    __repr__ = _utils.dataclasses_no_defaults_repr

```

#### tool_name

```python
tool_name: str

```

The name of the tool to call.

#### args

```python
args: str | dict[str, Any] | None = None

```

The arguments to pass to the tool.

This is stored either as a JSON string or a Python dictionary depending on how data was received.

#### tool_call_id

```python
tool_call_id: str = field(
    default_factory=generate_tool_call_id
)

```

The tool call identifier, this is used by some models including OpenAI.

In case the tool call id is not provided by the model, Pydantic AI will generate a random one.

#### id

```python
id: str | None = None

```

An optional identifier of the tool call part, separate from the tool call ID.

This is used by some APIs like OpenAI Responses.

#### provider_details

```python
provider_details: dict[str, Any] | None = None

```

Additional data returned by the provider that can't be mapped to standard fields.

This is used for data that is required to be sent back to APIs, as well as data users may want to access programmatically.

#### args_as_dict

```python
args_as_dict() -> dict[str, Any]

```

Return the arguments as a Python dictionary.

This is just for convenience with models that require dicts as input.

Source code in `pydantic_ai_slim/pydantic_ai/messages.py`

```python
def args_as_dict(self) -> dict[str, Any]:
    """Return the arguments as a Python dictionary.

    This is just for convenience with models that require dicts as input.
    """
    if not self.args:
        return {}
    if isinstance(self.args, dict):
        return self.args
    args = pydantic_core.from_json(self.args)
    assert isinstance(args, dict), 'args should be a dict'
    return cast(dict[str, Any], args)

```

#### args_as_json_str

```python
args_as_json_str() -> str

```

Return the arguments as a JSON string.

This is just for convenience with models that require JSON strings as input.

Source code in `pydantic_ai_slim/pydantic_ai/messages.py`

```python
def args_as_json_str(self) -> str:
    """Return the arguments as a JSON string.

    This is just for convenience with models that require JSON strings as input.
    """
    if not self.args:
        return '{}'
    if isinstance(self.args, str):
        return self.args
    return pydantic_core.to_json(self.args).decode()

```

#### has_content

```python
has_content() -> bool

```

Return `True` if the arguments contain any data.

Source code in `pydantic_ai_slim/pydantic_ai/messages.py`

```python
def has_content(self) -> bool:
    """Return `True` if the arguments contain any data."""
    if isinstance(self.args, dict):
        # TODO: This should probably return True if you have the value False, or 0, etc.
        #   It makes sense to me to ignore empty strings, but not sure about empty lists or dicts
        return any(self.args.values())
    else:
        return bool(self.args)

```
