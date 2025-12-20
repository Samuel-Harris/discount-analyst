## Observability with Prefect and Logfire

Prefect provides a built-in UI for monitoring flow runs, task executions, and failures. You can:

- View real-time flow run status
- Debug failures with full stack traces
- Set up alerts and notifications

To access the Prefect UI, you can either:

1. Use [Prefect Cloud](https://www.prefect.io/cloud) (managed service)
1. Run a local [Prefect server](https://docs.prefect.io/v3/how-to-guides/self-hosted/server-cli) with `prefect server start`

You can also use [Pydantic Logfire](../../logfire/) for detailed observability. When using both Prefect and Logfire, you'll get complementary views:

- **Prefect**: Workflow-level orchestration, task status, and retry history
- **Logfire**: Fine-grained tracing of agent runs, model requests, and tool invocations

When using Logfire with Prefect, you can enable distributed tracing to see spans for your Prefect runs included with your agent runs, model requests, and tool invocations.

For more information about Prefect monitoring, see the [Prefect documentation](https://docs.prefect.io/).
