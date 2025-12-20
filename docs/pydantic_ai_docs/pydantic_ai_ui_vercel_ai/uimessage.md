### UIMessage

Bases: `CamelBaseModel`

A message as displayed in the UI by Vercel AI Elements.

Source code in `pydantic_ai_slim/pydantic_ai/ui/vercel_ai/request_types.py`

```python
class UIMessage(CamelBaseModel):
    """A message as displayed in the UI by Vercel AI Elements."""

    id: str
    """A unique identifier for the message."""

    role: Literal['system', 'user', 'assistant']
    """The role of the message."""

    metadata: Any | None = None
    """The metadata of the message."""

    parts: list[UIMessagePart]
    """
    The parts of the message. Use this for rendering the message in the UI.
    System messages should be avoided (set the system prompt on the server instead).
    They can have text parts.
    User messages can have text parts and file parts.
    Assistant messages can have text, reasoning, tool invocation, and file parts.
    """

```

#### id

```python
id: str

```

A unique identifier for the message.

#### role

```python
role: Literal['system', 'user', 'assistant']

```

The role of the message.

#### metadata

```python
metadata: Any | None = None

```

The metadata of the message.

#### parts

```python
parts: list[UIMessagePart]

```

The parts of the message. Use this for rendering the message in the UI. System messages should be avoided (set the system prompt on the server instead). They can have text parts. User messages can have text parts and file parts. Assistant messages can have text, reasoning, tool invocation, and file parts.
