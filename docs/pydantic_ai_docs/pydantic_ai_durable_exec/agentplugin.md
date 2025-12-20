### AgentPlugin

Bases: `SimplePlugin`

Temporal worker plugin for a specific Pydantic AI agent.

Source code in `pydantic_ai_slim/pydantic_ai/durable_exec/temporal/__init__.py`

```python
class AgentPlugin(SimplePlugin):
    """Temporal worker plugin for a specific Pydantic AI agent."""

    def __init__(self, agent: TemporalAgent[Any, Any]):
        super().__init__(  # type: ignore[reportUnknownMemberType]
            name='AgentPlugin',
            activities=agent.temporal_activities,
        )

```
