### StateDeps

Bases: `Generic[StateT]`

Dependency type that holds state.

This class is used to manage the state of an agent run. It allows setting the state of the agent run with a specific type of state model, which must be a subclass of `BaseModel`.

The state is set using the `state` setter by the `Adapter` when the run starts.

Implements the `StateHandler` protocol.

Source code in `pydantic_ai_slim/pydantic_ai/ui/_adapter.py`

```python
@dataclass
class StateDeps(Generic[StateT]):
    """Dependency type that holds state.

    This class is used to manage the state of an agent run. It allows setting
    the state of the agent run with a specific type of state model, which must
    be a subclass of `BaseModel`.

    The state is set using the `state` setter by the `Adapter` when the run starts.

    Implements the `StateHandler` protocol.
    """

    state: StateT

```
