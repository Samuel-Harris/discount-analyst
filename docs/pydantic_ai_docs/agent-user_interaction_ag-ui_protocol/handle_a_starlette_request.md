### Handle a Starlette request

This example uses AGUIAdapter.dispatch_request() to directly handle a FastAPI request and return a response. Something analogous to this will work with any Starlette-based web framework.

[Learn about Gateway](../../gateway) handle_ag_ui_request.py

```python
from fastapi import FastAPI
from starlette.requests import Request
from starlette.responses import Response

from pydantic_ai import Agent
from pydantic_ai.ui.ag_ui import AGUIAdapter

agent = Agent('gateway/openai:gpt-5', instructions='Be fun!')

app = FastAPI()

@app.post('/')
async def run_agent(request: Request) -> Response:
    return await AGUIAdapter.dispatch_request(request, agent=agent) # (1)

```

1. This method essentially does the same as the previous example, but it's more convenient to use when you're already using a Starlette/FastAPI app.

handle_ag_ui_request.py

```python
from fastapi import FastAPI
from starlette.requests import Request
from starlette.responses import Response

from pydantic_ai import Agent
from pydantic_ai.ui.ag_ui import AGUIAdapter

agent = Agent('openai:gpt-5', instructions='Be fun!')

app = FastAPI()

@app.post('/')
async def run_agent(request: Request) -> Response:
    return await AGUIAdapter.dispatch_request(request, agent=agent) # (1)

```

1. This method essentially does the same as the previous example, but it's more convenient to use when you're already using a Starlette/FastAPI app.

Since `app` is an ASGI application, it can be used with any ASGI server:

```shell
uvicorn handle_ag_ui_request:app

```

This will expose the agent as an AG-UI server, and your frontend can start sending requests to it.
