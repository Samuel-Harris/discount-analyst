### Overriding model via pytest fixtures

If you're writing lots of tests that all require model to be overridden, you can use [pytest fixtures](https://docs.pytest.org/en/6.2.x/fixture.html) to override the model with TestModel or FunctionModel in a reusable way.

Here's an example of a fixture that overrides the model with `TestModel`:

test_agent.py

```python
import pytest

from pydantic_ai.models.test import TestModel

from weather_app import weather_agent


@pytest.fixture
def override_weather_agent():
    with weather_agent.override(model=TestModel()):
        yield


async def test_forecast(override_weather_agent: None):
    ...
    # test code here

```
