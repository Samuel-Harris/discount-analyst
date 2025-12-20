### AgentCapabilities

Bases: `TypedDict`

The capabilities of the agent.

Source code in `.venv/lib/python3.12/site-packages/fasta2a/schema.py`

```python
@pydantic.with_config({'alias_generator': to_camel})
class AgentCapabilities(TypedDict):
    """The capabilities of the agent."""

    streaming: NotRequired[bool]
    """Whether the agent supports streaming."""

    push_notifications: NotRequired[bool]
    """Whether the agent can notify updates to client."""

    state_transition_history: NotRequired[bool]
    """Whether the agent exposes status change history for tasks."""

```

#### streaming

```python
streaming: NotRequired[bool]

```

Whether the agent supports streaming.

#### push_notifications

```python
push_notifications: NotRequired[bool]

```

Whether the agent can notify updates to client.

#### state_transition_history

```python
state_transition_history: NotRequired[bool]

```

Whether the agent exposes status change history for tasks.
