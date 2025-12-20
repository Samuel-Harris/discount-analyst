## Durable Execution

In Temporal's durable execution implementation, a program that crashes or encounters an exception while interacting with a model or API will retry until it can successfully complete.

Temporal relies primarily on a replay mechanism to recover from failures. As the program makes progress, Temporal saves key inputs and decisions, allowing a re-started program to pick up right where it left off.

The key to making this work is to separate the application's repeatable (deterministic) and non-repeatable (non-deterministic) parts:

1. Deterministic pieces, termed [**workflows**](https://docs.temporal.io/workflow-definition), execute the same way when re-run with the same inputs.
1. Non-deterministic pieces, termed [**activities**](https://docs.temporal.io/activities), can run arbitrary code, performing I/O and any other operations.

Workflow code can run for extended periods and, if interrupted, resume exactly where it left off. Critically, workflow code generally _cannot_ include any kind of I/O, over the network, disk, etc. Activity code faces no restrictions on I/O or external interactions, but if an activity fails part-way through it is restarted from the beginning.

Note

If you are familiar with celery, it may be helpful to think of Temporal activities as similar to celery tasks, but where you wait for the task to complete and obtain its result before proceeding to the next step in the workflow. However, Temporal workflows and activities offer a great deal more flexibility and functionality than celery tasks.

See the [Temporal documentation](https://docs.temporal.io/evaluate/understanding-temporal#temporal-application-the-building-blocks) for more information

In the case of Pydantic AI agents, integration with Temporal means that [model requests](../../models/overview/), [tool calls](../../tools/) that may require I/O, and [MCP server communication](../../mcp/client/) all need to be offloaded to Temporal activities due to their I/O requirements, while the logic that coordinates them (i.e. the agent run) lives in the workflow. Code that handles a scheduled job or web request can then execute the workflow, which will in turn execute the activities as needed.

The diagram below shows the overall architecture of an agentic application in Temporal. The Temporal Server is responsible for tracking program execution and making sure the associated state is preserved reliably (i.e., stored to an internal database, and possibly replicated across cloud regions). Temporal Server manages data in encrypted form, so all data processing occurs on the Worker, which runs the workflow and activities.

```text
            +---------------------+
            |   Temporal Server   |      (Stores workflow state,
            +---------------------+       schedules activities,
                     ^                    persists progress)
                     |
        Save state,  |   Schedule Tasks,
        progress,    |   load state on resume
        timeouts     |
                     |
+------------------------------------------------------+
|                      Worker                          |
|   +----------------------------------------------+   |
|   |              Workflow Code                   |   |
|   |       (Agent Run Loop)                       |   |
|   +----------------------------------------------+   |
|          |          |                |               |
|          v          v                v               |
|   +-----------+ +------------+ +-------------+       |
|   | Activity  | | Activity   | |  Activity   |       |
|   | (Tool)    | | (MCP Tool) | | (Model API) |       |
|   +-----------+ +------------+ +-------------+       |
|         |           |                |               |
+------------------------------------------------------+
          |           |                |
          v           v                v
      [External APIs, services, databases, etc.]

```

See the [Temporal documentation](https://docs.temporal.io/evaluate/understanding-temporal#temporal-application-the-building-blocks) for more information.
