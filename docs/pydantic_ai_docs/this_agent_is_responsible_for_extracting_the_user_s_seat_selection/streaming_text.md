### Streaming Text

Example of streamed text output:

streamed_hello_world.py

```python
from pydantic_ai import Agent

agent = Agent('google-gla:gemini-2.5-flash')  # (1)!


async def main():
    async with agent.run_stream('Where does "hello world" come from?') as result:  # (2)!
        async for message in result.stream_text():  # (3)!
            print(message)
            #> The first known
            #> The first known use of "hello,
            #> The first known use of "hello, world" was in
            #> The first known use of "hello, world" was in a 1974 textbook
            #> The first known use of "hello, world" was in a 1974 textbook about the C
            #> The first known use of "hello, world" was in a 1974 textbook about the C programming language.

```

1. Streaming works with the standard Agent class, and doesn't require any special setup, just a model that supports streaming (currently all models support streaming).
1. The Agent.run_stream() method is used to start a streamed run, this method returns a context manager so the connection can be closed when the stream completes.
1. Each item yield by StreamedRunResult.stream_text() is the complete text response, extended as new data is received.

_(This example is complete, it can be run "as is" â€” you'll need to add `asyncio.run(main())` to run `main`)_

We can also stream text as deltas rather than the entire text in each item:

streamed_delta_hello_world.py

```python
from pydantic_ai import Agent

agent = Agent('google-gla:gemini-2.5-flash')


async def main():
    async with agent.run_stream('Where does "hello world" come from?') as result:
        async for message in result.stream_text(delta=True):  # (1)!
            print(message)
            #> The first known
            #> use of "hello,
            #> world" was in
            #> a 1974 textbook
            #> about the C
            #> programming language.

```

1. stream_text will error if the response is not text.

_(This example is complete, it can be run "as is" â€” you'll need to add `asyncio.run(main())` to run `main`)_

Output message not included in `messages`

The final output message will **NOT** be added to result messages if you use `.stream_text(delta=True)`, see [Messages and chat history](../message-history/) for more information.
