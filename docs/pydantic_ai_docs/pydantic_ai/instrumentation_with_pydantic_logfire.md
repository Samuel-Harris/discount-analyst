## Instrumentation with Pydantic Logfire

Even a simple agent with just a handful of tools can result in a lot of back-and-forth with the LLM, making it nearly impossible to be confident of what's going on just from reading the code. To understand the flow of the above runs, we can watch the agent in action using Pydantic Logfire.

To do this, we need to [set up Logfire](logfire/#using-logfire), and add the following to our code:

[Learn about Gateway](../gateway) bank_support_with_logfire.py

```python
...
from pydantic_ai import Agent, RunContext

from bank_database import DatabaseConn

import logfire
logfire.configure()  # (1)!
logfire.instrument_pydantic_ai()  # (2)!
logfire.instrument_asyncpg()  # (3)!

...

support_agent = Agent(
    'gateway/openai:gpt-5',
    deps_type=SupportDependencies,
    output_type=SupportOutput,
    system_prompt=(
        'You are a support agent in our bank, give the '
        'customer support and judge the risk level of their query.'
    ),
)

```

1. Configure the Logfire SDK, this will fail if project is not set up.
1. This will instrument all Pydantic AI agents used from here on out. If you want to instrument only a specific agent, you can pass the instrument=True keyword argument to the agent.
1. In our demo, `DatabaseConn` uses `asyncpg` to connect to a PostgreSQL database, so [`logfire.instrument_asyncpg()`](https://magicstack.github.io/asyncpg/current/) is used to log the database queries.

bank_support_with_logfire.py

```python
...
from pydantic_ai import Agent, RunContext

from bank_database import DatabaseConn

import logfire
logfire.configure()  # (1)!
logfire.instrument_pydantic_ai()  # (2)!
logfire.instrument_asyncpg()  # (3)!

...

support_agent = Agent(
    'openai:gpt-5',
    deps_type=SupportDependencies,
    output_type=SupportOutput,
    system_prompt=(
        'You are a support agent in our bank, give the '
        'customer support and judge the risk level of their query.'
    ),
)

```

1. Configure the Logfire SDK, this will fail if project is not set up.
1. This will instrument all Pydantic AI agents used from here on out. If you want to instrument only a specific agent, you can pass the instrument=True keyword argument to the agent.
1. In our demo, `DatabaseConn` uses `asyncpg` to connect to a PostgreSQL database, so [`logfire.instrument_asyncpg()`](https://magicstack.github.io/asyncpg/current/) is used to log the database queries.

That's enough to get the following view of your agent in action:

See [Monitoring and Performance](logfire/) to learn more.
