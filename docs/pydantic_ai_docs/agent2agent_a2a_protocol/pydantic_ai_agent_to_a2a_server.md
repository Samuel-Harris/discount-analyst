### Pydantic AI Agent to A2A Server

To expose a Pydantic AI agent as an A2A server, you can use the `to_a2a` method:

[Learn about Gateway](../gateway) agent_to_a2a.py

```python
from pydantic_ai import Agent

agent = Agent('gateway/openai:gpt-5', instructions='Be fun!')
app = agent.to_a2a()

```

agent_to_a2a.py

```python
from pydantic_ai import Agent

agent = Agent('openai:gpt-5', instructions='Be fun!')
app = agent.to_a2a()

```

Since `app` is an ASGI application, it can be used with any ASGI server.

```bash
uvicorn agent_to_a2a:app --host 0.0.0.0 --port 8000

```

Since the goal of `to_a2a` is to be a convenience method, it accepts the same arguments as the FastA2A constructor.

When using `to_a2a()`, Pydantic AI automatically:

- Stores the complete conversation history (including tool calls and responses) in the context storage
- Ensures that subsequent messages with the same `context_id` have access to the full conversation history
- Persists agent results as A2A artifacts:
- String results become `TextPart` artifacts and also appear in the message history
- Structured data (Pydantic models, dataclasses, tuples, etc.) become `DataPart` artifacts with the data wrapped as `{"result": <your_data>}`
- Artifacts include metadata with type information and JSON schema when available
