### Custom Agents

You can specify a custom agent using the `--agent` flag with a module path and variable name:

[Learn about Gateway](../gateway) custom_agent.py

```python
from pydantic_ai import Agent

agent = Agent('gateway/openai:gpt-5', instructions='You always respond in Italian.')

```

custom_agent.py

```python
from pydantic_ai import Agent

agent = Agent('openai:gpt-5', instructions='You always respond in Italian.')

```

Then run:

```bash
uvx clai --agent custom_agent:agent "What's the weather today?"

```

The format must be `module:variable` where:

- `module` is the importable Python module path
- `variable` is the name of the Agent instance in that module

Additionally, you can directly launch CLI mode from an `Agent` instance using `Agent.to_cli_sync()`:

[Learn about Gateway](../gateway) agent_to_cli_sync.py

```python
from pydantic_ai import Agent

agent = Agent('gateway/openai:gpt-5', instructions='You always respond in Italian.')
agent.to_cli_sync()

```

agent_to_cli_sync.py

```python
from pydantic_ai import Agent

agent = Agent('openai:gpt-5', instructions='You always respond in Italian.')
agent.to_cli_sync()

```

You can also use the async interface with `Agent.to_cli()`:

[Learn about Gateway](../gateway) agent_to_cli.py

```python
from pydantic_ai import Agent

agent = Agent('gateway/openai:gpt-5', instructions='You always respond in Italian.')

async def main():
    await agent.to_cli()

```

agent_to_cli.py

```python
from pydantic_ai import Agent

agent = Agent('openai:gpt-5', instructions='You always respond in Italian.')

async def main():
    await agent.to_cli()

```

_(You'll need to add `asyncio.run(main())` to run `main`)_
