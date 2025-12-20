### Human in the Loop

Demonstrates simple human in the loop workflow where the agent comes up with a plan and the user can approve it using checkboxes.

#### Task Planning Tools

- `generate_task_steps` - AG-UI tool to generate and confirm steps

#### Task Planning Prompt

```text
Generate a list of steps for cleaning a car for me to review

```

#### Human in the Loop - Code

[Learn about Gateway](../../gateway) [ag_ui/api/human_in_the_loop.py](https://github.com/pydantic/pydantic-ai/blob/main/examples/pydantic_ai_examples/ag_ui/api/human_in_the_loop.py)

```python
"""Human in the Loop Feature.

No special handling is required for this feature.
"""

from __future__ import annotations

from textwrap import dedent

from pydantic_ai import Agent
from pydantic_ai.ui.ag_ui.app import AGUIApp

agent = Agent(
    'gateway/openai:gpt-5-mini',
    instructions=dedent(
        """
        When planning tasks use tools only, without any other messages.
        IMPORTANT:
        - Use the `generate_task_steps` tool to display the suggested steps to the user
        - Never repeat the plan, or send a message detailing steps
        - If accepted, confirm the creation of the plan and the number of selected (enabled) steps only
        - If not accepted, ask the user for more information, DO NOT use the `generate_task_steps` tool again
        """
    ),
)

app = AGUIApp(agent)

```

[ag_ui/api/human_in_the_loop.py](https://github.com/pydantic/pydantic-ai/blob/main/examples/pydantic_ai_examples/ag_ui/api/human_in_the_loop.py)

```python
"""Human in the Loop Feature.

No special handling is required for this feature.
"""

from __future__ import annotations

from textwrap import dedent

from pydantic_ai import Agent
from pydantic_ai.ui.ag_ui.app import AGUIApp

agent = Agent(
    'openai:gpt-5-mini',
    instructions=dedent(
        """
        When planning tasks use tools only, without any other messages.
        IMPORTANT:
        - Use the `generate_task_steps` tool to display the suggested steps to the user
        - Never repeat the plan, or send a message detailing steps
        - If accepted, confirm the creation of the plan and the number of selected (enabled) steps only
        - If not accepted, ask the user for more information, DO NOT use the `generate_task_steps` tool again
        """
    ),
)

app = AGUIApp(agent)

```
