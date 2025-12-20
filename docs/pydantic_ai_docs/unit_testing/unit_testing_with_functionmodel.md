### Unit testing with `FunctionModel`

The above tests are a great start, but careful readers will notice that the `WeatherService.get_forecast` is never called since `TestModel` calls `weather_forecast` with a date in the past.

To fully exercise `weather_forecast`, we need to use FunctionModel to customise how the tools is called.

Here's an example of using `FunctionModel` to test the `weather_forecast` tool with custom inputs

test_weather_app2.py

```python
import re

import pytest

from pydantic_ai import models
from pydantic_ai import (
    ModelMessage,
    ModelResponse,
    TextPart,
    ToolCallPart,
)
from pydantic_ai.models.function import AgentInfo, FunctionModel

from fake_database import DatabaseConn
from weather_app import run_weather_forecast, weather_agent

pytestmark = pytest.mark.anyio
models.ALLOW_MODEL_REQUESTS = False


def call_weather_forecast(  # (1)!
    messages: list[ModelMessage], info: AgentInfo
) -> ModelResponse:
    if len(messages) == 1:
        # first call, call the weather forecast tool
        user_prompt = messages[0].parts[-1]
        m = re.search(r'\d{4}-\d{2}-\d{2}', user_prompt.content)
        assert m is not None
        args = {'location': 'London', 'forecast_date': m.group()}  # (2)!
        return ModelResponse(parts=[ToolCallPart('weather_forecast', args)])
    else:
        # second call, return the forecast
        msg = messages[-1].parts[0]
        assert msg.part_kind == 'tool-return'
        return ModelResponse(parts=[TextPart(f'The forecast is: {msg.content}')])


async def test_forecast_future():
    conn = DatabaseConn()
    user_id = 1
    with weather_agent.override(model=FunctionModel(call_weather_forecast)):  # (3)!
        prompt = 'What will the weather be like in London on 2032-01-01?'
        await run_weather_forecast([(prompt, user_id)], conn)

    forecast = await conn.get_forecast(user_id)
    assert forecast == 'The forecast is: Rainy with a chance of sun'

```

1. We define a function `call_weather_forecast` that will be called by `FunctionModel` in place of the LLM, this function has access to the list of ModelMessages that make up the run, and AgentInfo which contains information about the agent and the function tools and return tools.
1. Our function is slightly intelligent in that it tries to extract a date from the prompt, but just hard codes the location.
1. We use FunctionModel to replace the agent's model with our custom function.
