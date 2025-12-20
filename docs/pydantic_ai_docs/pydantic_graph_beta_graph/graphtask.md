### GraphTask

Bases: `GraphTaskRequest`

A task representing the execution of a node in the graph.

GraphTask encapsulates all the information needed to execute a specific node, including its inputs and the fork context it's executing within, and has a unique ID to identify the task within the graph run.

Source code in `pydantic_graph/pydantic_graph/beta/graph.py`

```python
@dataclass
class GraphTask(GraphTaskRequest):
    """A task representing the execution of a node in the graph.

    GraphTask encapsulates all the information needed to execute a specific
    node, including its inputs and the fork context it's executing within,
    and has a unique ID to identify the task within the graph run.
    """

    task_id: TaskID = field(repr=False)
    """Unique identifier for this task."""

    @staticmethod
    def from_request(request: GraphTaskRequest, get_task_id: Callable[[], TaskID]) -> GraphTask:
        # Don't call the get_task_id callable, this is already a task
        if isinstance(request, GraphTask):
            return request
        return GraphTask(request.node_id, request.inputs, request.fork_stack, get_task_id())

```

#### task_id

```python
task_id: TaskID = field(repr=False)

```

Unique identifier for this task.
