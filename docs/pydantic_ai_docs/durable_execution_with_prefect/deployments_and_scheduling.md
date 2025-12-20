## Deployments and Scheduling

To deploy and schedule a `PrefectAgent`, wrap it in a Prefect flow and use the flow's [`serve()`](https://docs.prefect.io/v3/how-to-guides/deployments/create-deployments#create-a-deployment-with-serve) or [`deploy()`](https://docs.prefect.io/v3/how-to-guides/deployments/deploy-via-python) methods:

[Learn about Gateway](../../gateway) serve_agent.py

```python
from prefect import flow

from pydantic_ai import Agent
from pydantic_ai.durable_exec.prefect import PrefectAgent


@flow
async def daily_report_flow(user_prompt: str):
    """Generate a daily report using the agent."""
    agent = Agent(  # (1)!
        'gateway/openai:gpt-5',
        name='daily_report_agent',
        instructions='Generate a daily summary report.',
    )

    prefect_agent = PrefectAgent(agent)

    result = await prefect_agent.run(user_prompt)
    return result.output
