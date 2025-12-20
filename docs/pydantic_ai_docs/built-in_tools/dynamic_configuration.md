## Dynamic Configuration

Sometimes you need to configure a built-in tool dynamically based on the run context (e.g., user dependencies), or conditionally omit it. You can achieve this by passing a function to `builtin_tools` that takes RunContext as an argument and returns an AbstractBuiltinTool or `None`.

This is particularly useful for tools like WebSearchTool where you might want to set the user's location based on the current request, or disable the tool if the user provides no location.

[Learn about Gateway](../gateway) dynamic_builtin_tool.py

```python
from pydantic_ai import Agent, RunContext, WebSearchTool


async def prepared_web_search(ctx: RunContext[dict]) -> WebSearchTool | None:
    if not ctx.deps.get('location'):
        return None

    return WebSearchTool(
        user_location={'city': ctx.deps['location']},
    )

agent = Agent(
    'gateway/openai-responses:gpt-5',
    builtin_tools=[prepared_web_search],
    deps_type=dict,
)
