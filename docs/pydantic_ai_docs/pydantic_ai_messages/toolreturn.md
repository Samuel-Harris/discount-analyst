### ToolReturn

A structured return value for tools that need to provide both a return value and custom content to the model.

This class allows tools to return complex responses that include:

- A return value for actual tool return
- Custom content (including multi-modal content) to be sent to the model as a UserPromptPart
- Optional metadata for application use

Source code in `pydantic_ai_slim/pydantic_ai/messages.py`

```python
@dataclass(repr=False)
class ToolReturn:
    """A structured return value for tools that need to provide both a return value and custom content to the model.

    This class allows tools to return complex responses that include:
    - A return value for actual tool return
    - Custom content (including multi-modal content) to be sent to the model as a UserPromptPart
    - Optional metadata for application use
    """

    return_value: Any
    """The return value to be used in the tool response."""

    _: KW_ONLY

    content: str | Sequence[UserContent] | None = None
    """The content to be sent to the model as a UserPromptPart."""

    metadata: Any = None
    """Additional data that can be accessed programmatically by the application but is not sent to the LLM."""

    kind: Literal['tool-return'] = 'tool-return'

    __repr__ = _utils.dataclasses_no_defaults_repr

```

#### return_value

```python
return_value: Any

```

The return value to be used in the tool response.

#### content

```python
content: str | Sequence[UserContent] | None = None

```

The content to be sent to the model as a UserPromptPart.

#### metadata

```python
metadata: Any = None

```

Additional data that can be accessed programmatically by the application but is not sent to the LLM.
