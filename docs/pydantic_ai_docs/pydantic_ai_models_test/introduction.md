Utility model for quickly testing apps built with Pydantic AI.

Here's a minimal example:

[Learn about Gateway](../../../gateway) test_model_usage.py

```python
from pydantic_ai import Agent
from pydantic_ai.models.test import TestModel

my_agent = Agent('gateway/openai:gpt-5', system_prompt='...')


async def test_my_agent():
    """Unit test for my_agent, to be run by pytest."""
    m = TestModel()
    with my_agent.override(model=m):
        result = await my_agent.run('Testing my agent...')
        assert result.output == 'success (no tool calls)'
    assert m.last_model_request_parameters.function_tools == []

```

test_model_usage.py

```python
from pydantic_ai import Agent
from pydantic_ai.models.test import TestModel

my_agent = Agent('openai:gpt-5', system_prompt='...')


async def test_my_agent():
    """Unit test for my_agent, to be run by pytest."""
    m = TestModel()
    with my_agent.override(model=m):
        result = await my_agent.run('Testing my agent...')
        assert result.output == 'success (no tool calls)'
    assert m.last_model_request_parameters.function_tools == []

```

See [Unit testing with `TestModel`](../../../testing/#unit-testing-with-testmodel) for detailed documentation.
