## Durable Agent

Any agent can be wrapped in a PrefectAgent to get durable execution. `PrefectAgent` automatically:

- Wraps Agent.run and Agent.run_sync as Prefect flows.
- Wraps [model requests](../../models/overview/) as Prefect tasks.
- Wraps [tool calls](../../tools/) as Prefect tasks (configurable per-tool).
- Wraps [MCP communication](../../mcp/client/) as Prefect tasks.

Event stream handlers are **automatically wrapped** by Prefect when running inside a Prefect flow. Each event from the stream is processed in a separate Prefect task for durability. You can customize the task behavior using the `event_stream_handler_task_config` parameter when creating the `PrefectAgent`. Do **not** manually decorate event stream handlers with `@task`. For examples, see the [streaming docs](../../agents/#streaming-all-events)

The original agent, model, and MCP server can still be used as normal outside the Prefect flow.

Here is a simple but complete example of wrapping an agent for durable execution. All it requires is to install Pydantic AI with Prefect:

```bash
pip install pydantic-ai[prefect]

```

```bash
uv add pydantic-ai[prefect]

```

Or if you're using the slim package, you can install it with the `prefect` optional group:

```bash
pip install pydantic-ai-slim[prefect]

```

```bash
uv add pydantic-ai-slim[prefect]

```

prefect_agent.py

```python
from pydantic_ai import Agent
from pydantic_ai.durable_exec.prefect import PrefectAgent

agent = Agent(
    'gpt-5',
    instructions="You're an expert in geography.",
    name='geography',  # (1)!
)

prefect_agent = PrefectAgent(agent)  # (2)!

async def main():
    result = await prefect_agent.run('What is the capital of Mexico?')  # (3)!
    print(result.output)
    #> Mexico City (Ciudad de MÃ©xico, CDMX)

```

1. The agent's `name` is used to uniquely identify its flows and tasks.
1. Wrapping the agent with `PrefectAgent` enables durable execution for all agent runs.
1. PrefectAgent.run() works like Agent.run(), but runs as a Prefect flow and executes model requests, decorated tool calls, and MCP communication as Prefect tasks.

_(This example is complete, it can be run "as is" â€” you'll need to add `asyncio.run(main())` to run `main`)_

For more information on how to use Prefect in Python applications, see their [Python documentation](https://docs.prefect.io/v3/how-to-guides/workflows/write-and-run).
