### Events

Pydantic AI tools can send [AG-UI events](https://docs.ag-ui.com/concepts/events) simply by returning a [`ToolReturn`](../../tools-advanced/#advanced-tool-returns) object with a [`BaseEvent`](https://docs.ag-ui.com/sdk/python/core/events#baseevent) (or a list of events) as `metadata`, which allows for custom events and state updates.

[Learn about Gateway](../../gateway) ag_ui_tool_events.py

```python
from ag_ui.core import CustomEvent, EventType, StateSnapshotEvent
from pydantic import BaseModel

from pydantic_ai import Agent, RunContext, ToolReturn
from pydantic_ai.ui import StateDeps
from pydantic_ai.ui.ag_ui.app import AGUIApp


class DocumentState(BaseModel):
    """State for the document being written."""

    document: str = ''


agent = Agent(
    'gateway/openai:gpt-5',
    instructions='Be fun!',
    deps_type=StateDeps[DocumentState],
)
app = AGUIApp(agent, deps=StateDeps(DocumentState()))


@agent.tool
async def update_state(ctx: RunContext[StateDeps[DocumentState]]) -> ToolReturn:
    return ToolReturn(
        return_value='State updated',
        metadata=[
            StateSnapshotEvent(
                type=EventType.STATE_SNAPSHOT,
                snapshot=ctx.deps.state,
            ),
        ],
    )


@agent.tool_plain
async def custom_events() -> ToolReturn:
    return ToolReturn(
        return_value='Count events sent',
        metadata=[
            CustomEvent(
                type=EventType.CUSTOM,
                name='count',
                value=1,
            ),
            CustomEvent(
                type=EventType.CUSTOM,
                name='count',
                value=2,
            ),
        ]
    )

```

ag_ui_tool_events.py

```python
from ag_ui.core import CustomEvent, EventType, StateSnapshotEvent
from pydantic import BaseModel

from pydantic_ai import Agent, RunContext, ToolReturn
from pydantic_ai.ui import StateDeps
from pydantic_ai.ui.ag_ui.app import AGUIApp


class DocumentState(BaseModel):
    """State for the document being written."""

    document: str = ''


agent = Agent(
    'openai:gpt-5',
    instructions='Be fun!',
    deps_type=StateDeps[DocumentState],
)
app = AGUIApp(agent, deps=StateDeps(DocumentState()))


@agent.tool
async def update_state(ctx: RunContext[StateDeps[DocumentState]]) -> ToolReturn:
    return ToolReturn(
        return_value='State updated',
        metadata=[
            StateSnapshotEvent(
                type=EventType.STATE_SNAPSHOT,
                snapshot=ctx.deps.state,
            ),
        ],
    )


@agent.tool_plain
async def custom_events() -> ToolReturn:
    return ToolReturn(
        return_value='Count events sent',
        metadata=[
            CustomEvent(
                type=EventType.CUSTOM,
                name='count',
                value=1,
            ),
            CustomEvent(
                type=EventType.CUSTOM,
                name='count',
                value=2,
            ),
        ]
    )

```

Since `app` is an ASGI application, it can be used with any ASGI server:

```bash
uvicorn ag_ui_tool_events:app --host 0.0.0.0 --port 9000

```
