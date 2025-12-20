### NodeIdent

```python
NodeIdent: TypeAlias = (
    "type[BaseNode[Any, Any, Any]] | BaseNode[Any, Any, Any] | str"
)

```

A type alias for a node identifier.

This can be:

- A node instance (instance of a subclass of BaseNode).
- A node class (subclass of BaseNode).
- A string representing the node ID.
