### StepFunction

Bases: `Protocol[StateT, DepsT, InputT, OutputT]`

Protocol for step functions that can be executed in the graph.

Step functions are async callables that receive a step context and return a result.

Type Parameters

StateT: The type of the graph state DepsT: The type of the dependencies InputT: The type of the input data OutputT: The type of the output data

Source code in `pydantic_graph/pydantic_graph/beta/step.py`

```python
class StepFunction(Protocol[StateT, DepsT, InputT, OutputT]):
    """Protocol for step functions that can be executed in the graph.

    Step functions are async callables that receive a step context and return a result.

    Type Parameters:
        StateT: The type of the graph state
        DepsT: The type of the dependencies
        InputT: The type of the input data
        OutputT: The type of the output data
    """

    def __call__(self, ctx: StepContext[StateT, DepsT, InputT]) -> Awaitable[OutputT]:
        """Execute the step function with the given context.

        Args:
            ctx: The step context containing state, dependencies, and inputs

        Returns:
            An awaitable that resolves to the step's output
        """
        raise NotImplementedError

```

#### **call**

```python
__call__(
    ctx: StepContext[StateT, DepsT, InputT],
) -> Awaitable[OutputT]

```

Execute the step function with the given context.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `ctx` | `StepContext[StateT, DepsT, InputT]` | The step context containing state, dependencies, and inputs | _required_ |

Returns:

| Type | Description | | --- | --- | | `Awaitable[OutputT]` | An awaitable that resolves to the step's output |

Source code in `pydantic_graph/pydantic_graph/beta/step.py`

```python
def __call__(self, ctx: StepContext[StateT, DepsT, InputT]) -> Awaitable[OutputT]:
    """Execute the step function with the given context.

    Args:
        ctx: The step context containing state, dependencies, and inputs

    Returns:
        An awaitable that resolves to the step's output
    """
    raise NotImplementedError

```
