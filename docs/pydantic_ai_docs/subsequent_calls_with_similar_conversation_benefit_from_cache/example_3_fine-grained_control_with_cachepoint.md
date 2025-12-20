### Example 3: Fine-Grained Control with CachePoint

Use manual `CachePoint` markers to control cache locations precisely:

[Learn about Gateway](../../gateway)

```python
from pydantic_ai import Agent, CachePoint

agent = Agent(
    'gateway/anthropic:claude-sonnet-4-5',
    system_prompt='Instructions...',
)
