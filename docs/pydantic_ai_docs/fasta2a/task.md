### Task

Bases: `TypedDict`

A Task is a stateful entity that allows Clients and Remote Agents to achieve a specific outcome.

Clients and Remote Agents exchange Messages within a Task. Remote Agents generate results as Artifacts. A Task is always created by a Client and the status is always determined by the Remote Agent.

Source code in `.venv/lib/python3.12/site-packages/fasta2a/schema.py`

```python
@pydantic.with_config({'alias_generator': to_camel})
class Task(TypedDict):
    """A Task is a stateful entity that allows Clients and Remote Agents to achieve a specific outcome.

    Clients and Remote Agents exchange Messages within a Task. Remote Agents generate results as Artifacts.
    A Task is always created by a Client and the status is always determined by the Remote Agent.
    """

    id: str
    """Unique identifier for the task."""

    context_id: str
    """The context the task is associated with."""

    kind: Literal['task']
    """Event type."""

    status: TaskStatus
    """Current status of the task."""

    history: NotRequired[list[Message]]
    """Optional history of messages."""

    artifacts: NotRequired[list[Artifact]]
    """Collection of artifacts created by the agent."""

    metadata: NotRequired[dict[str, Any]]
    """Extension metadata."""

```

#### id

```python
id: str

```

Unique identifier for the task.

#### context_id

```python
context_id: str

```

The context the task is associated with.

#### kind

```python
kind: Literal['task']

```

Event type.

#### status

```python
status: TaskStatus

```

Current status of the task.

#### history

```python
history: NotRequired[list[Message]]

```

Optional history of messages.

#### artifacts

```python
artifacts: NotRequired[list[Artifact]]

```

Collection of artifacts created by the agent.

#### metadata

```python
metadata: NotRequired[dict[str, Any]]

```

Extension metadata.
