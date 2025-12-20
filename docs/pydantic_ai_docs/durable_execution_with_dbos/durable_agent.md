## Durable Agent

Any agent can be wrapped in a DBOSAgent to get durable execution. `DBOSAgent` automatically:,

- Wraps `Agent.run` and `Agent.run_sync` as DBOS workflows.
- Wraps [model requests](../../models/overview/) and [MCP communication](../../mcp/client/) as DBOS steps.

Custom tool functions and event stream handlers are **not automatically wrapped** by DBOS. If they involve non-deterministic behavior or perform I/O, you should explicitly decorate them with `@DBOS.step`.

The original agent, model, and MCP server can still be used as normal outside the DBOS workflow.

Here is a simple but complete example of wrapping an agent for durable execution. All it requires is to install Pydantic AI with the DBOS [open-source library](https://github.com/dbos-inc/dbos-transact-py):

```bash
pip install pydantic-ai[dbos]

```

```bash
uv add pydantic-ai[dbos]

```

Or if you're using the slim package, you can install it with the `dbos` optional group:

```bash
pip install pydantic-ai-slim[dbos]

```

```bash
uv add pydantic-ai-slim[dbos]

```

dbos_agent.py

```python
from dbos import DBOS, DBOSConfig

from pydantic_ai import Agent
from pydantic_ai.durable_exec.dbos import DBOSAgent

dbos_config: DBOSConfig = {
    'name': 'pydantic_dbos_agent',
    'system_database_url': 'sqlite:///dbostest.sqlite',  # (3)!
}
DBOS(config=dbos_config)

agent = Agent(
    'gpt-5',
    instructions="You're an expert in geography.",
    name='geography',  # (4)!
)

dbos_agent = DBOSAgent(agent)  # (1)!

async def main():
    DBOS.launch()
    result = await dbos_agent.run('What is the capital of Mexico?')  # (2)!
    print(result.output)
    #> Mexico City (Ciudad de MÃ©xico, CDMX)

```

1. Workflows and `DBOSAgent` must be defined before `DBOS.launch()` so that recovery can correctly find all workflows.
1. DBOSAgent.run() works like Agent.run(), but runs as a DBOS workflow and executes model requests, decorated tool calls, and MCP communication as DBOS steps.
1. This example uses SQLite. Postgres is recommended for production.
1. The agent's `name` is used to uniquely identify its workflows.

_(This example is complete, it can be run "as is" â€” you'll need to add `asyncio.run(main())` to run `main`)_

Because DBOS workflows need to be defined before calling `DBOS.launch()` and the `DBOSAgent` instance automatically registers `run` and `run_sync` as workflows, it needs to be defined before calling `DBOS.launch()` as well.

For more information on how to use DBOS in Python applications, see their [Python SDK guide](https://docs.dbos.dev/python/programming-guide).
