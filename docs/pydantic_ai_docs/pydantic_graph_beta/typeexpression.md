### TypeExpression

Bases: `Generic[T]`

A workaround for type checker limitations when using complex type expressions.

```text
This class serves as a wrapper for types that cannot normally be used in positions

```

requiring `type[T]`, such as `Any`, `Union[...]`, or `Literal[...]`. It provides a way to pass these complex type expressions to functions expecting concrete types.

Example

Instead of `output_type=Union[str, int]` (which may cause type errors), use `output_type=TypeExpression[Union[str, int]]`.

Note

This is a workaround for the lack of TypeForm in the Python type system.

Source code in `pydantic_graph/pydantic_graph/beta/util.py`

```python
class TypeExpression(Generic[T]):
    """A workaround for type checker limitations when using complex type expressions.

        This class serves as a wrapper for types that cannot normally be used in positions
    requiring `type[T]`, such as `Any`, `Union[...]`, or `Literal[...]`. It provides a
        way to pass these complex type expressions to functions expecting concrete types.

    Example:
            Instead of `output_type=Union[str, int]` (which may cause type errors),
            use `output_type=TypeExpression[Union[str, int]]`.

    Note:
            This is a workaround for the lack of TypeForm in the Python type system.
    """

    pass

```
