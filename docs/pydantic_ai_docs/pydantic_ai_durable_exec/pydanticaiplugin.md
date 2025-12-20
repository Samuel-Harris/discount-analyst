### PydanticAIPlugin

Bases: `SimplePlugin`

Temporal client and worker plugin for Pydantic AI.

Source code in `pydantic_ai_slim/pydantic_ai/durable_exec/temporal/__init__.py`

```python
class PydanticAIPlugin(SimplePlugin):
    """Temporal client and worker plugin for Pydantic AI."""

    def __init__(self):
        super().__init__(  # type: ignore[reportUnknownMemberType]
            name='PydanticAIPlugin',
            data_converter=_data_converter,
            workflow_runner=_workflow_runner,
            workflow_failure_exception_types=[UserError, PydanticUserError],
        )

```
