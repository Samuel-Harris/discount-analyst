### Handle run input and output directly

This example uses AGUIAdapter.run_stream() and performs its own request parsing and response generation. This can be modified to work with any web framework.

[Learn about Gateway](../../gateway) run_ag_ui.py

```python
import json
from http import HTTPStatus

from fastapi import FastAPI
from fastapi.requests import Request
from fastapi.responses import Response, StreamingResponse
from pydantic import ValidationError

from pydantic_ai import Agent
from pydantic_ai.ui import SSE_CONTENT_TYPE
from pydantic_ai.ui.ag_ui import AGUIAdapter

agent = Agent('gateway/openai:gpt-5', instructions='Be fun!')

app = FastAPI()


@app.post('/')
async def run_agent(request: Request) -> Response:
    accept = request.headers.get('accept', SSE_CONTENT_TYPE)
    try:
        run_input = AGUIAdapter.build_run_input(await request.body())  # (1)
    except ValidationError as e:
        return Response(
            content=json.dumps(e.json()),
            media_type='application/json',
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
        )

    adapter = AGUIAdapter(agent=agent, run_input=run_input, accept=accept)
    event_stream = adapter.run_stream() # (2)

    sse_event_stream = adapter.encode_stream(event_stream)
    return StreamingResponse(sse_event_stream, media_type=accept) # (3)

```

1. AGUIAdapter.build_run_input() takes the request body as bytes and returns an AG-UI [`RunAgentInput`](https://docs.ag-ui.com/sdk/python/core/types#runagentinput) object. You can also use the AGUIAdapter.from_request() class method to build an adapter directly from a request.
1. AGUIAdapter.run_stream() runs the agent and returns a stream of AG-UI events. It supports the same optional arguments as [`Agent.run_stream_events()`](../../agents/#running-agents), including `deps`. You can also use AGUIAdapter.run_stream_native() to run the agent and return a stream of Pydantic AI events instead, which can then be transformed into AG-UI events using AGUIAdapter.transform_stream().
1. AGUIAdapter.encode_stream() encodes the stream of AG-UI events as strings according to the accept header value. You can also use AGUIAdapter.streaming_response() to generate a streaming response directly from the AG-UI event stream returned by `run_stream()`.

run_ag_ui.py

```python
import json
from http import HTTPStatus

from fastapi import FastAPI
from fastapi.requests import Request
from fastapi.responses import Response, StreamingResponse
from pydantic import ValidationError

from pydantic_ai import Agent
from pydantic_ai.ui import SSE_CONTENT_TYPE
from pydantic_ai.ui.ag_ui import AGUIAdapter

agent = Agent('openai:gpt-5', instructions='Be fun!')

app = FastAPI()


@app.post('/')
async def run_agent(request: Request) -> Response:
    accept = request.headers.get('accept', SSE_CONTENT_TYPE)
    try:
        run_input = AGUIAdapter.build_run_input(await request.body())  # (1)
    except ValidationError as e:
        return Response(
            content=json.dumps(e.json()),
            media_type='application/json',
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
        )

    adapter = AGUIAdapter(agent=agent, run_input=run_input, accept=accept)
    event_stream = adapter.run_stream() # (2)

    sse_event_stream = adapter.encode_stream(event_stream)
    return StreamingResponse(sse_event_stream, media_type=accept) # (3)

```

1. AGUIAdapter.build_run_input() takes the request body as bytes and returns an AG-UI [`RunAgentInput`](https://docs.ag-ui.com/sdk/python/core/types#runagentinput) object. You can also use the AGUIAdapter.from_request() class method to build an adapter directly from a request.
1. AGUIAdapter.run_stream() runs the agent and returns a stream of AG-UI events. It supports the same optional arguments as [`Agent.run_stream_events()`](../../agents/#running-agents), including `deps`. You can also use AGUIAdapter.run_stream_native() to run the agent and return a stream of Pydantic AI events instead, which can then be transformed into AG-UI events using AGUIAdapter.transform_stream().
1. AGUIAdapter.encode_stream() encodes the stream of AG-UI events as strings according to the accept header value. You can also use AGUIAdapter.streaming_response() to generate a streaming response directly from the AG-UI event stream returned by `run_stream()`.

Since `app` is an ASGI application, it can be used with any ASGI server:

```shell
uvicorn run_ag_ui:app

```

This will expose the agent as an AG-UI server, and your frontend can start sending requests to it.
