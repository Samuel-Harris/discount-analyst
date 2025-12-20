## Runs vs. Conversations

An agent **run** might represent an entire conversation â€” there's no limit to how many messages can be exchanged in a single run. However, a **conversation** might also be composed of multiple runs, especially if you need to maintain state between separate interactions or API calls.

Here's an example of a conversation comprised of multiple runs:

[Learn about Gateway](../gateway) conversation_example.py

```python
from pydantic_ai import Agent

agent = Agent('gateway/openai:gpt-5')
