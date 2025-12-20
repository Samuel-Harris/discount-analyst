## Running Agents

There are five ways to run an agent:

1. agent.run() â€” an async function which returns a RunResult containing a completed response.
1. agent.run_sync() â€” a plain, synchronous function which returns a RunResult containing a completed response (internally, this just calls `loop.run_until_complete(self.run())`).
1. agent.run_stream() â€” an async context manager which returns a StreamedRunResult, which contains methods to stream text and structured output as an async iterable. agent.run_stream_sync() is a synchronous variation that returns a StreamedRunResultSync with synchronous versions of the same methods.
1. agent.run_stream_events() â€” a function which returns an async iterable of AgentStreamEvents and a AgentRunResultEvent containing the final run result.
1. agent.iter() â€” a context manager which returns an AgentRun, an async iterable over the nodes of the agent's underlying Graph.

Here's a simple example demonstrating the first four:

[Learn about Gateway](../gateway) run_agent.py

```python
from pydantic_ai import Agent, AgentRunResultEvent, AgentStreamEvent

agent = Agent('gateway/openai:gpt-5')

result_sync = agent.run_sync('What is the capital of Italy?')
print(result_sync.output)
#> The capital of Italy is Rome.


async def main():
    result = await agent.run('What is the capital of France?')
    print(result.output)
    #> The capital of France is Paris.

    async with agent.run_stream('What is the capital of the UK?') as response:
        async for text in response.stream_text():
            print(text)
            #> The capital of
            #> The capital of the UK is
            #> The capital of the UK is London.

    events: list[AgentStreamEvent | AgentRunResultEvent] = []
    async for event in agent.run_stream_events('What is the capital of Mexico?'):
        events.append(event)
    print(events)
    """
    [
        PartStartEvent(index=0, part=TextPart(content='The capital of ')),
        FinalResultEvent(tool_name=None, tool_call_id=None),
        PartDeltaEvent(index=0, delta=TextPartDelta(content_delta='Mexico is Mexico ')),
        PartDeltaEvent(index=0, delta=TextPartDelta(content_delta='City.')),
        PartEndEvent(
            index=0, part=TextPart(content='The capital of Mexico is Mexico City.')
        ),
        AgentRunResultEvent(
            result=AgentRunResult(output='The capital of Mexico is Mexico City.')
        ),
    ]
    """

```

run_agent.py

```python
from pydantic_ai import Agent, AgentRunResultEvent, AgentStreamEvent

agent = Agent('openai:gpt-5')

result_sync = agent.run_sync('What is the capital of Italy?')
print(result_sync.output)
#> The capital of Italy is Rome.


async def main():
    result = await agent.run('What is the capital of France?')
    print(result.output)
    #> The capital of France is Paris.

    async with agent.run_stream('What is the capital of the UK?') as response:
        async for text in response.stream_text():
            print(text)
            #> The capital of
            #> The capital of the UK is
            #> The capital of the UK is London.

    events: list[AgentStreamEvent | AgentRunResultEvent] = []
    async for event in agent.run_stream_events('What is the capital of Mexico?'):
        events.append(event)
    print(events)
    """
    [
        PartStartEvent(index=0, part=TextPart(content='The capital of ')),
        FinalResultEvent(tool_name=None, tool_call_id=None),
        PartDeltaEvent(index=0, delta=TextPartDelta(content_delta='Mexico is Mexico ')),
        PartDeltaEvent(index=0, delta=TextPartDelta(content_delta='City.')),
        PartEndEvent(
            index=0, part=TextPart(content='The capital of Mexico is Mexico City.')
        ),
        AgentRunResultEvent(
            result=AgentRunResult(output='The capital of Mexico is Mexico City.')
        ),
    ]
    """

```

_(This example is complete, it can be run "as is" â€” you'll need to add `asyncio.run(main())` to run `main`)_

You can also pass messages from previous runs to continue a conversation or provide context, as described in [Messages and Chat History](../message-history/).
