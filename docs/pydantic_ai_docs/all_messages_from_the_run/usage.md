### Usage

The `history_processors` is a list of callables that take a list of ModelMessage and return a modified list of the same type.

Each processor is applied in sequence, and processors can be either synchronous or asynchronous.

[Learn about Gateway](../gateway) simple_history_processor.py

```python
from pydantic_ai import (
    Agent,
    ModelMessage,
    ModelRequest,
    ModelResponse,
    TextPart,
    UserPromptPart,
)


def filter_responses(messages: list[ModelMessage]) -> list[ModelMessage]:
    """Remove all ModelResponse messages, keeping only ModelRequest messages."""
    return [msg for msg in messages if isinstance(msg, ModelRequest)]
