### Using Messages as Input for Further Agent Runs

The primary use of message histories in Pydantic AI is to maintain context across multiple agent runs.

To use existing messages in a run, pass them to the `message_history` parameter of Agent.run, Agent.run_sync or Agent.run_stream.

If `message_history` is set and not empty, a new system prompt is not generated â€” we assume the existing message history includes a system prompt.

[Learn about Gateway](../gateway) Reusing messages in a conversation

```python
from pydantic_ai import Agent

agent = Agent('gateway/openai:gpt-5', system_prompt='Be a helpful assistant.')

result1 = agent.run_sync('Tell me a joke.')
print(result1.output)
#> Did you hear about the toothpaste scandal? They called it Colgate.

result2 = agent.run_sync('Explain?', message_history=result1.new_messages())
print(result2.output)
#> This is an excellent joke invented by Samuel Colvin, it needs no explanation.

print(result2.all_messages())
"""
[
    ModelRequest(
        parts=[
            SystemPromptPart(
                content='Be a helpful assistant.',
                timestamp=datetime.datetime(...),
            ),
            UserPromptPart(
                content='Tell me a joke.',
                timestamp=datetime.datetime(...),
            ),
        ],
        run_id='...',
    ),
    ModelResponse(
        parts=[
            TextPart(
                content='Did you hear about the toothpaste scandal? They called it Colgate.'
            )
        ],
        usage=RequestUsage(input_tokens=60, output_tokens=12),
        model_name='gpt-5',
        timestamp=datetime.datetime(...),
        run_id='...',
    ),
    ModelRequest(
        parts=[
            UserPromptPart(
                content='Explain?',
                timestamp=datetime.datetime(...),
            )
        ],
        run_id='...',
    ),
    ModelResponse(
        parts=[
            TextPart(
                content='This is an excellent joke invented by Samuel Colvin, it needs no explanation.'
            )
        ],
        usage=RequestUsage(input_tokens=61, output_tokens=26),
        model_name='gpt-5',
        timestamp=datetime.datetime(...),
        run_id='...',
    ),
]
"""

```

Reusing messages in a conversation

```python
from pydantic_ai import Agent

agent = Agent('openai:gpt-5', system_prompt='Be a helpful assistant.')

result1 = agent.run_sync('Tell me a joke.')
print(result1.output)
#> Did you hear about the toothpaste scandal? They called it Colgate.

result2 = agent.run_sync('Explain?', message_history=result1.new_messages())
print(result2.output)
#> This is an excellent joke invented by Samuel Colvin, it needs no explanation.

print(result2.all_messages())
"""
[
    ModelRequest(
        parts=[
            SystemPromptPart(
                content='Be a helpful assistant.',
                timestamp=datetime.datetime(...),
            ),
            UserPromptPart(
                content='Tell me a joke.',
                timestamp=datetime.datetime(...),
            ),
        ],
        run_id='...',
    ),
    ModelResponse(
        parts=[
            TextPart(
                content='Did you hear about the toothpaste scandal? They called it Colgate.'
            )
        ],
        usage=RequestUsage(input_tokens=60, output_tokens=12),
        model_name='gpt-5',
        timestamp=datetime.datetime(...),
        run_id='...',
    ),
    ModelRequest(
        parts=[
            UserPromptPart(
                content='Explain?',
                timestamp=datetime.datetime(...),
            )
        ],
        run_id='...',
    ),
    ModelResponse(
        parts=[
            TextPart(
                content='This is an excellent joke invented by Samuel Colvin, it needs no explanation.'
            )
        ],
        usage=RequestUsage(input_tokens=61, output_tokens=26),
        model_name='gpt-5',
        timestamp=datetime.datetime(...),
        run_id='...',
    ),
]
"""

```

_(This example is complete, it can be run "as is")_
