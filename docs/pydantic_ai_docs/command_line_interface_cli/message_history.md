### Message History

Both `Agent.to_cli()` and `Agent.to_cli_sync()` support a `message_history` parameter, allowing you to continue an existing conversation or provide conversation context:

[Learn about Gateway](../gateway) agent_with_history.py

```python
from pydantic_ai import (
    Agent,
    ModelMessage,
    ModelRequest,
    ModelResponse,
    TextPart,
    UserPromptPart,
)

agent = Agent('gateway/openai:gpt-5')
