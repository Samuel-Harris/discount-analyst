## Durable Agent

Any agent can be wrapped in a TemporalAgent to get a durable agent that can be used inside a deterministic Temporal workflow, by automatically offloading all work that requires I/O (namely model requests, tool calls, and MCP server communication) to non-deterministic activities.

At the time of wrapping, the agent's [model](../../models/overview/) and [toolsets](../../toolsets/) (including function tools registered on the agent and MCP servers) are frozen, activities are dynamically created for each, and the original model and toolsets are wrapped to call on the worker to execute the corresponding activities instead of directly performing the actions inside the workflow. The original agent can still be used as normal outside the Temporal workflow, but any changes to its model or toolsets after wrapping will not be reflected in the durable agent.

Here is a simple but complete example of wrapping an agent for durable execution, creating a Temporal workflow with durable execution logic, connecting to a Temporal server, and running the workflow from non-durable code. All it requires is a Temporal server to be [running locally](https://github.com/temporalio/temporal#download-and-start-temporal-server-locally):

```sh
brew install temporal
temporal server start-dev

```

temporal_agent.py

```python
import uuid

from temporalio import workflow
from temporalio.client import Client
from temporalio.worker import Worker

from pydantic_ai import Agent
from pydantic_ai.durable_exec.temporal import (
    AgentPlugin,
    PydanticAIPlugin,
    TemporalAgent,
)

agent = Agent(
    'gpt-5',
    instructions="You're an expert in geography.",
    name='geography',  # (10)!
)

temporal_agent = TemporalAgent(agent)  # (1)!


@workflow.defn
class GeographyWorkflow:  # (2)!
    @workflow.run
    async def run(self, prompt: str) -> str:
        result = await temporal_agent.run(prompt)  # (3)!
        return result.output


async def main():
    client = await Client.connect(  # (4)!
        'localhost:7233',  # (5)!
        plugins=[PydanticAIPlugin()],  # (6)!
    )

    async with Worker(  # (7)!
        client,
        task_queue='geography',
        workflows=[GeographyWorkflow],
        plugins=[AgentPlugin(temporal_agent)],  # (8)!
    ):
        output = await client.execute_workflow(  # (9)!
            GeographyWorkflow.run,
            args=['What is the capital of Mexico?'],
            id=f'geography-{uuid.uuid4()}',
            task_queue='geography',
        )
        print(output)
        #> Mexico City (Ciudad de MÃ©xico, CDMX)

```

1. The original `Agent` cannot be used inside a deterministic Temporal workflow, but the `TemporalAgent` can.
1. As explained above, the workflow represents a deterministic piece of code that can use non-deterministic activities for operations that require I/O.
1. TemporalAgent.run() works just like Agent.run(), but it will automatically offload model requests, tool calls, and MCP server communication to Temporal activities.
1. We connect to the Temporal server which keeps track of workflow and activity execution.
1. This assumes the Temporal server is [running locally](https://github.com/temporalio/temporal#download-and-start-temporal-server-locally).
1. The PydanticAIPlugin tells Temporal to use Pydantic for serialization and deserialization, and to treat UserError exceptions as non-retryable.
1. We start the worker that will listen on the specified task queue and run workflows and activities. In a real world application, this might be run in a separate service.
1. The AgentPlugin registers the `TemporalAgent`'s activities with the worker.
1. We call on the server to execute the workflow on a worker that's listening on the specified task queue.
1. The agent's `name` is used to uniquely identify its activities.

_(This example is complete, it can be run "as is" â€” you'll need to add `asyncio.run(main())` to run `main`)_

In a real world application, the agent, workflow, and worker are typically defined separately from the code that calls for a workflow to be executed. Because Temporal workflows need to be defined at the top level of the file and the `TemporalAgent` instance is needed inside the workflow and when starting the worker (to register the activities), it needs to be defined at the top level of the file as well.

For more information on how to use Temporal in Python applications, see their [Python SDK guide](https://docs.temporal.io/develop/python).
