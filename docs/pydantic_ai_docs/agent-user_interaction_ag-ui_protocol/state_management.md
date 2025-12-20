### State management

The integration provides full support for [AG-UI state management](https://docs.ag-ui.com/concepts/state), which enables real-time synchronization between agents and frontend applications.

In the example below we have document state which is shared between the UI and server using the StateDeps [dependencies type](../../dependencies/) that can be used to automatically validate state contained in [`RunAgentInput.state`](https://docs.ag-ui.com/sdk/js/core/types#runagentinput) using a Pydantic `BaseModel` specified as a generic parameter.

Custom dependencies type with AG-UI state

If you want to use your own dependencies type to hold AG-UI state as well as other things, it needs to implements the StateHandler protocol, meaning it needs to be a [dataclass](https://docs.python.org/3/library/dataclasses.html) with a non-optional `state` field. This lets Pydantic AI ensure that state is properly isolated between requests by building a new dependencies object each time.

If the `state` field's type is a Pydantic `BaseModel` subclass, the raw state dictionary on the request is automatically validated. If not, you can validate the raw value yourself in your dependencies dataclass's `__post_init__` method.

If AG-UI state is provided but your dependencies do not implement StateHandler, Pydantic AI will emit a warning and ignore the state. Use StateDeps or a custom StateHandler implementation to receive and validate the incoming state.

[Learn about Gateway](../../gateway) ag_ui_state.py

```python
from pydantic import BaseModel

from pydantic_ai import Agent
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

```

ag_ui_state.py

```python
from pydantic import BaseModel

from pydantic_ai import Agent
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

```

Since `app` is an ASGI application, it can be used with any ASGI server:

```bash
uvicorn ag_ui_state:app --host 0.0.0.0 --port 9000

```
