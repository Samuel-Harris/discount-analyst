### Usage with Starlette/FastAPI

Besides the request, VercelAIAdapter.dispatch_request() takes the agent, the same optional arguments as [`Agent.run_stream_events()`](../../agents/#running-agents), and an optional `on_complete` callback function that receives the completed AgentRunResult and can optionally yield additional Vercel AI events.

[Learn about Gateway](../../gateway) dispatch_request.py

```python
from fastapi import FastAPI
from starlette.requests import Request
from starlette.responses import Response

from pydantic_ai import Agent
from pydantic_ai.ui.vercel_ai import VercelAIAdapter

agent = Agent('gateway/openai:gpt-5')

app = FastAPI()

@app.post('/chat')
async def chat(request: Request) -> Response:
    return await VercelAIAdapter.dispatch_request(request, agent=agent)

```

dispatch_request.py

```python
from fastapi import FastAPI
from starlette.requests import Request
from starlette.responses import Response

from pydantic_ai import Agent
from pydantic_ai.ui.vercel_ai import VercelAIAdapter

agent = Agent('openai:gpt-5')

app = FastAPI()

@app.post('/chat')
async def chat(request: Request) -> Response:
    return await VercelAIAdapter.dispatch_request(request, agent=agent)

```
