### StreamFunction

Bases: `Protocol[StateT, DepsT, InputT, OutputT]`

Protocol for stream functions that can be executed in the graph.

Stream functions are async callables that receive a step context and return an async iterator.

Type Parameters

StateT: The type of the graph state DepsT: The type of the dependencies InputT: The type of the input data OutputT: The type of the output data

Source code in `pydantic_graph/pydantic_graph/beta/step.py`

```python
class StreamFunction(Protocol[StateT, DepsT, InputT, OutputT]):
    """Protocol for stream functions that can be executed in the graph.

    Stream functions are async callables that receive a step context and return an async iterator.

    Type Parameters:
        StateT: The type of the graph state
        DepsT: The type of the dependencies
        InputT: The type of the input data
        OutputT: The type of the output data
    """

    def __call__(self, ctx: StepContext[StateT, DepsT, InputT]) -> AsyncIterator[OutputT]:
        """Execute the stream function with the given context.

        Args:
            ctx: The step context containing state, dependencies, and inputs

        Returns:
            An async iterator yielding the streamed output
        """
        raise NotImplementedError
        yield

```

#### **call**

```python
__call__(
    ctx: StepContext[StateT, DepsT, InputT],
) -> AsyncIterator[OutputT]

```

Execute the stream function with the given context.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `ctx` | `StepContext[StateT, DepsT, InputT]` | The step context containing state, dependencies, and inputs | _required_ |

Returns:

| Type | Description | | --- | --- | | `AsyncIterator[OutputT]` | An async iterator yielding the streamed output |

Source code in `pydantic_graph/pydantic_graph/beta/step.py`

```python
def __call__(self, ctx: StepContext[StateT, DepsT, InputT]) -> AsyncIterator[OutputT]:
    """Execute the stream function with the given context.

    Args:
        ctx: The step context containing state, dependencies, and inputs

    Returns:
        An async iterator yielding the streamed output
    """
    raise NotImplementedError
    yield

```
