### EndNode

Bases: `Generic[InputT]`

Terminal node representing the completion of graph execution.

The EndNode marks the successful completion of a graph execution flow and can collect the final output data.

Source code in `pydantic_graph/pydantic_graph/beta/node.py`

```python
class EndNode(Generic[InputT]):
    """Terminal node representing the completion of graph execution.

    The EndNode marks the successful completion of a graph execution flow
    and can collect the final output data.
    """

    id = NodeID('__end__')
    """Fixed identifier for the end node."""

    def _force_variance(self, inputs: InputT) -> None:  # pragma: no cover
        """Force type variance for proper generic typing.

        This method exists solely for type checking purposes and should never be called.

        Args:
            inputs: Input data of type InputT.

        Raises:
            RuntimeError: Always, as this method should never be executed.
        """
        raise RuntimeError('This method should never be called, it is just defined for typing purposes.')

```

#### id

```python
id = NodeID('__end__')

```

Fixed identifier for the end node.
