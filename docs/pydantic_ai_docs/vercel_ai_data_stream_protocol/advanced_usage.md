### Advanced Usage

If you're using a web framework not based on Starlette (e.g. Django or Flask) or need fine-grained control over the input or output, you can create a `VercelAIAdapter` instance and directly use its methods, which can be chained to accomplish the same thing as the `VercelAIAdapter.dispatch_request()` class method shown above:

1. The VercelAIAdapter.build_run_input() class method takes the request body as bytes and returns a Vercel AI RequestData run input object, which you can then pass to the VercelAIAdapter() constructor along with the agent.
   - You can also use the VercelAIAdapter.from_request() class method to build an adapter directly from a Starlette/FastAPI request.
1. The VercelAIAdapter.run_stream() method runs the agent and returns a stream of Vercel AI events. It supports the same optional arguments as [`Agent.run_stream_events()`](../../agents/#running-agents) and an optional `on_complete` callback function that receives the completed AgentRunResult and can optionally yield additional Vercel AI events.
   - You can also use VercelAIAdapter.run_stream_native() to run the agent and return a stream of Pydantic AI events instead, which can then be transformed into Vercel AI events using VercelAIAdapter.transform_stream().
1. The VercelAIAdapter.encode_stream() method encodes the stream of Vercel AI events as SSE (HTTP Server-Sent Events) strings, which you can then return as a streaming response.
   - You can also use VercelAIAdapter.streaming_response() to generate a Starlette/FastAPI streaming response directly from the Vercel AI event stream returned by `run_stream()`.

Note

This example uses FastAPI, but can be modified to work with any web framework.

[Learn about Gateway](../../gateway) run_stream.py

```python
import json
from http import HTTPStatus

from fastapi import FastAPI
from fastapi.requests import Request
from fastapi.responses import Response, StreamingResponse
from pydantic import ValidationError

from pydantic_ai import Agent
from pydantic_ai.ui import SSE_CONTENT_TYPE
from pydantic_ai.ui.vercel_ai import VercelAIAdapter

agent = Agent('gateway/openai:gpt-5')

app = FastAPI()


@app.post('/chat')
async def chat(request: Request) -> Response:
    accept = request.headers.get('accept', SSE_CONTENT_TYPE)
    try:
        run_input = VercelAIAdapter.build_run_input(await request.body())
    except ValidationError as e:
        return Response(
            content=json.dumps(e.json()),
            media_type='application/json',
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
        )

    adapter = VercelAIAdapter(agent=agent, run_input=run_input, accept=accept)
    event_stream = adapter.run_stream()

    sse_event_stream = adapter.encode_stream(event_stream)
    return StreamingResponse(sse_event_stream, media_type=accept)

```

run_stream.py

```python
import json
from http import HTTPStatus

from fastapi import FastAPI
from fastapi.requests import Request
from fastapi.responses import Response, StreamingResponse
from pydantic import ValidationError

from pydantic_ai import Agent
from pydantic_ai.ui import SSE_CONTENT_TYPE
from pydantic_ai.ui.vercel_ai import VercelAIAdapter

agent = Agent('openai:gpt-5')

app = FastAPI()


@app.post('/chat')
async def chat(request: Request) -> Response:
    accept = request.headers.get('accept', SSE_CONTENT_TYPE)
    try:
        run_input = VercelAIAdapter.build_run_input(await request.body())
    except ValidationError as e:
        return Response(
            content=json.dumps(e.json()),
            media_type='application/json',
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
        )

    adapter = VercelAIAdapter(agent=agent, run_input=run_input, accept=accept)
    event_stream = adapter.run_stream()

    sse_event_stream = adapter.encode_stream(event_stream)
    return StreamingResponse(sse_event_stream, media_type=accept)

```
