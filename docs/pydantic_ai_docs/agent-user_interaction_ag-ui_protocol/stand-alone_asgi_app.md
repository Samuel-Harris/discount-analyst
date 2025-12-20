### Stand-alone ASGI app

This example uses AGUIApp to turn the agent into a stand-alone ASGI application:

[Learn about Gateway](../../gateway) ag_ui_app.py

```python
from pydantic_ai import Agent
from pydantic_ai.ui.ag_ui.app import AGUIApp

agent = Agent('gateway/openai:gpt-5', instructions='Be fun!')
app = AGUIApp(agent)

```

ag_ui_app.py

```python
from pydantic_ai import Agent
from pydantic_ai.ui.ag_ui.app import AGUIApp

agent = Agent('openai:gpt-5', instructions='Be fun!')
app = AGUIApp(agent)

```

Since `app` is an ASGI application, it can be used with any ASGI server:

```shell
uvicorn ag_ui_app:app

```

This will expose the agent as an AG-UI server, and your frontend can start sending requests to it.
