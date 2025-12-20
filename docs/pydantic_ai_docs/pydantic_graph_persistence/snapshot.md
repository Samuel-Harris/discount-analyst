### Snapshot

```python
Snapshot = (
    NodeSnapshot[StateT, RunEndT]
    | EndSnapshot[StateT, RunEndT]
)

```

A step in the history of a graph run.

Graph.run returns a list of these steps describing the execution of the graph, together with the run return value.
