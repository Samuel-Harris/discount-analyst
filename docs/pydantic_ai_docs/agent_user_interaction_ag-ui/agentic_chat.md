### Agentic Chat

This demonstrates a basic agent interaction including Pydantic AI server side tools and AG-UI client side tools.

If you've [run the example](#running-the-example), you can view it at <http://localhost:3000/pydantic-ai/feature/agentic_chat>.

#### Agent Tools

- `time` - Pydantic AI tool to check the current time for a time zone
- `background` - AG-UI tool to set the background color of the client window

#### Agent Prompts

```text
What is the time in New York?

```

```text
Change the background to blue

```

A complex example which mixes both AG-UI and Pydantic AI tools:

```text
Perform the following steps, waiting for the response of each step before continuing:
1. Get the time
2. Set the background to red
3. Get the time
4. Report how long the background set took by diffing the two times

```

#### Agentic Chat - Code

[Learn about Gateway](../../gateway) [ag_ui/api/agentic_chat.py](https://github.com/pydantic/pydantic-ai/blob/main/examples/pydantic_ai_examples/ag_ui/api/agentic_chat.py)

```python
"""Agentic Chat feature."""

from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from pydantic_ai import Agent
from pydantic_ai.ui.ag_ui.app import AGUIApp

agent = Agent('gateway/openai:gpt-5-mini')


@agent.tool_plain
async def current_time(timezone: str = 'UTC') -> str:
    """Get the current time in ISO format.

    Args:
        timezone: The timezone to use.

    Returns:
        The current time in ISO format string.
    """
    tz: ZoneInfo = ZoneInfo(timezone)
    return datetime.now(tz=tz).isoformat()


app = AGUIApp(agent)

```

[ag_ui/api/agentic_chat.py](https://github.com/pydantic/pydantic-ai/blob/main/examples/pydantic_ai_examples/ag_ui/api/agentic_chat.py)

```python
"""Agentic Chat feature."""

from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from pydantic_ai import Agent
from pydantic_ai.ui.ag_ui.app import AGUIApp

agent = Agent('openai:gpt-5-mini')


@agent.tool_plain
async def current_time(timezone: str = 'UTC') -> str:
    """Get the current time in ISO format.

    Args:
        timezone: The timezone to use.

    Returns:
        The current time in ISO format string.
    """
    tz: ZoneInfo = ZoneInfo(timezone)
    return datetime.now(tz=tz).isoformat()


app = AGUIApp(agent)

```
