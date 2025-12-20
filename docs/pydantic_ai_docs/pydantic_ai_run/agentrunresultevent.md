### AgentRunResultEvent

Bases: `Generic[OutputDataT]`

An event indicating the agent run ended and containing the final result of the agent run.

Source code in `pydantic_ai_slim/pydantic_ai/run.py`

```python
@dataclasses.dataclass(repr=False)
class AgentRunResultEvent(Generic[OutputDataT]):
    """An event indicating the agent run ended and containing the final result of the agent run."""

    result: AgentRunResult[OutputDataT]
    """The result of the run."""

    _: dataclasses.KW_ONLY

    event_kind: Literal['agent_run_result'] = 'agent_run_result'
    """Event type identifier, used as a discriminator."""

    __repr__ = _utils.dataclasses_no_defaults_repr

```

#### result

```python
result: AgentRunResult[OutputDataT]

```

The result of the run.

#### event_kind

```python
event_kind: Literal["agent_run_result"] = "agent_run_result"

```

Event type identifier, used as a discriminator.
