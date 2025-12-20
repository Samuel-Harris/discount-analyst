### MessagesBuilder

Helper class to build Pydantic AI messages from request/response parts.

Source code in `pydantic_ai_slim/pydantic_ai/ui/_messages_builder.py`

```python
@dataclass
class MessagesBuilder:
    """Helper class to build Pydantic AI messages from request/response parts."""

    messages: list[ModelMessage] = field(default_factory=list)

    def add(self, part: ModelRequestPart | ModelResponsePart) -> None:
        """Add a new part, creating a new request or response message if necessary."""
        last_message = self.messages[-1] if self.messages else None
        if isinstance(part, get_union_args(ModelRequestPart)):
            part = cast(ModelRequestPart, part)
            if isinstance(last_message, ModelRequest):
                last_message.parts = [*last_message.parts, part]
            else:
                self.messages.append(ModelRequest(parts=[part]))
        else:
            part = cast(ModelResponsePart, part)
            if isinstance(last_message, ModelResponse):
                last_message.parts = [*last_message.parts, part]
            else:
                self.messages.append(ModelResponse(parts=[part]))

```

#### add

```python
add(part: ModelRequestPart | ModelResponsePart) -> None

```

Add a new part, creating a new request or response message if necessary.

Source code in `pydantic_ai_slim/pydantic_ai/ui/_messages_builder.py`

```python
def add(self, part: ModelRequestPart | ModelResponsePart) -> None:
    """Add a new part, creating a new request or response message if necessary."""
    last_message = self.messages[-1] if self.messages else None
    if isinstance(part, get_union_args(ModelRequestPart)):
        part = cast(ModelRequestPart, part)
        if isinstance(last_message, ModelRequest):
            last_message.parts = [*last_message.parts, part]
        else:
            self.messages.append(ModelRequest(parts=[part]))
    else:
        part = cast(ModelResponsePart, part)
        if isinstance(last_message, ModelResponse):
            last_message.parts = [*last_message.parts, part]
        else:
            self.messages.append(ModelResponse(parts=[part]))

```
