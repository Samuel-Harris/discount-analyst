### Unit testing with `TestModel`

The simplest and fastest way to exercise most of your application code is using TestModel, this will (by default) call all tools in the agent, then return either plain text or a structured response depending on the return type of the agent.

`TestModel` is not magic

The "clever" (but not too clever) part of `TestModel` is that it will attempt to generate valid structured data for [function tools](../tools/) and [output types](../output/#structured-output) based on the schema of the registered tools.

There's no ML or AI in `TestModel`, it's just plain old procedural Python code that tries to generate data that satisfies the JSON schema of a tool.

The resulting data won't look pretty or relevant, but it should pass Pydantic's validation in most cases. If you want something more sophisticated, use FunctionModel and write your own data generation logic.

Let's write unit tests for the following application code:

[Learn about Gateway](../gateway) weather_app.py

```python
import asyncio
from datetime import date

from pydantic_ai import Agent, RunContext

from fake_database import DatabaseConn  # (1)!
from weather_service import WeatherService  # (2)!

weather_agent = Agent(
    'gateway/openai:gpt-5',
    deps_type=WeatherService,
    system_prompt='Providing a weather forecast at the locations the user provides.',
)


@weather_agent.tool
def weather_forecast(
    ctx: RunContext[WeatherService], location: str, forecast_date: date
) -> str:
    if forecast_date < date.today():  # (3)!
        return ctx.deps.get_historic_weather(location, forecast_date)
    else:
        return ctx.deps.get_forecast(location, forecast_date)


async def run_weather_forecast(  # (4)!
    user_prompts: list[tuple[str, int]], conn: DatabaseConn
):
    """Run weather forecast for a list of user prompts and save."""
    async with WeatherService() as weather_service:

        async def run_forecast(prompt: str, user_id: int):
            result = await weather_agent.run(prompt, deps=weather_service)
            await conn.store_forecast(user_id, result.output)

        # run all prompts in parallel
        await asyncio.gather(
            *(run_forecast(prompt, user_id) for (prompt, user_id) in user_prompts)
        )

```

1. `DatabaseConn` is a class that holds a database connection
1. `WeatherService` has methods to get weather forecasts and historic data about the weather
1. We need to call a different endpoint depending on whether the date is in the past or the future, you'll see why this nuance is important below
1. This function is the code we want to test, together with the agent it uses

weather_app.py

```python
import asyncio
from datetime import date

from pydantic_ai import Agent, RunContext

from fake_database import DatabaseConn  # (1)!
from weather_service import WeatherService  # (2)!

weather_agent = Agent(
    'openai:gpt-5',
    deps_type=WeatherService,
    system_prompt='Providing a weather forecast at the locations the user provides.',
)


@weather_agent.tool
def weather_forecast(
    ctx: RunContext[WeatherService], location: str, forecast_date: date
) -> str:
    if forecast_date < date.today():  # (3)!
        return ctx.deps.get_historic_weather(location, forecast_date)
    else:
        return ctx.deps.get_forecast(location, forecast_date)


async def run_weather_forecast(  # (4)!
    user_prompts: list[tuple[str, int]], conn: DatabaseConn
):
    """Run weather forecast for a list of user prompts and save."""
    async with WeatherService() as weather_service:

        async def run_forecast(prompt: str, user_id: int):
            result = await weather_agent.run(prompt, deps=weather_service)
            await conn.store_forecast(user_id, result.output)

        # run all prompts in parallel
        await asyncio.gather(
            *(run_forecast(prompt, user_id) for (prompt, user_id) in user_prompts)
        )

```

1. `DatabaseConn` is a class that holds a database connection
1. `WeatherService` has methods to get weather forecasts and historic data about the weather
1. We need to call a different endpoint depending on whether the date is in the past or the future, you'll see why this nuance is important below
1. This function is the code we want to test, together with the agent it uses

Here we have a function that takes a list of `(user_prompt, user_id)` tuples, gets a weather forecast for each prompt, and stores the result in the database.

**We want to test this code without having to mock certain objects or modify our code so we can pass test objects in.**

Here's how we would write tests using TestModel:

test_weather_app.py

```python
from datetime import timezone
import pytest

from dirty_equals import IsNow, IsStr

from pydantic_ai import models, capture_run_messages, RequestUsage
from pydantic_ai.models.test import TestModel
from pydantic_ai import (
    ModelResponse,
    SystemPromptPart,
    TextPart,
    ToolCallPart,
    ToolReturnPart,
    UserPromptPart,
    ModelRequest,
)

from fake_database import DatabaseConn
from weather_app import run_weather_forecast, weather_agent

pytestmark = pytest.mark.anyio  # (1)!
models.ALLOW_MODEL_REQUESTS = False  # (2)!


async def test_forecast():
    conn = DatabaseConn()
    user_id = 1
    with capture_run_messages() as messages:
        with weather_agent.override(model=TestModel()):  # (3)!
            prompt = 'What will the weather be like in London on 2024-11-28?'
            await run_weather_forecast([(prompt, user_id)], conn)  # (4)!

    forecast = await conn.get_forecast(user_id)
    assert forecast == '{"weather_forecast":"Sunny with a chance of rain"}'  # (5)!

    assert messages == [  # (6)!
        ModelRequest(
            parts=[
                SystemPromptPart(
                    content='Providing a weather forecast at the locations the user provides.',
                    timestamp=IsNow(tz=timezone.utc),
                ),
                UserPromptPart(
                    content='What will the weather be like in London on 2024-11-28?',
                    timestamp=IsNow(tz=timezone.utc),  # (7)!
                ),
            ],
            run_id=IsStr(),
        ),
        ModelResponse(
            parts=[
                ToolCallPart(
                    tool_name='weather_forecast',
                    args={
                        'location': 'a',
                        'forecast_date': '2024-01-01',  # (8)!
                    },
                    tool_call_id=IsStr(),
                )
            ],
            usage=RequestUsage(
                input_tokens=71,
                output_tokens=7,
            ),
            model_name='test',
            timestamp=IsNow(tz=timezone.utc),
            run_id=IsStr(),
        ),
        ModelRequest(
            parts=[
                ToolReturnPart(
                    tool_name='weather_forecast',
                    content='Sunny with a chance of rain',
                    tool_call_id=IsStr(),
                    timestamp=IsNow(tz=timezone.utc),
                ),
            ],
            run_id=IsStr(),
        ),
        ModelResponse(
            parts=[
                TextPart(
                    content='{"weather_forecast":"Sunny with a chance of rain"}',
                )
            ],
            usage=RequestUsage(
                input_tokens=77,
                output_tokens=16,
            ),
            model_name='test',
            timestamp=IsNow(tz=timezone.utc),
            run_id=IsStr(),
        ),
    ]

```

1. We're using [anyio](https://anyio.readthedocs.io/en/stable/) to run async tests.
1. This is a safety measure to make sure we don't accidentally make real requests to the LLM while testing, see ALLOW_MODEL_REQUESTS for more details.
1. We're using Agent.override to replace the agent's model with TestModel, the nice thing about `override` is that we can replace the model inside agent without needing access to the agent `run*` methods call site.
1. Now we call the function we want to test inside the `override` context manager.
1. But default, `TestModel` will return a JSON string summarising the tools calls made, and what was returned. If you wanted to customise the response to something more closely aligned with the domain, you could add custom_output_text='Sunny' when defining `TestModel`.
1. So far we don't actually know which tools were called and with which values, we can use capture_run_messages to inspect messages from the most recent run and assert the exchange between the agent and the model occurred as expected.
1. The IsNow helper allows us to use declarative asserts even with data which will contain timestamps that change over time.
1. `TestModel` isn't doing anything clever to extract values from the prompt, so these values are hardcoded.
