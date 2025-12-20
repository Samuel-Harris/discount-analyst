### CancelTaskResponse

```python
CancelTaskResponse = JSONRPCResponse[
    Task, Union[TaskNotCancelableError, TaskNotFoundError]
]

```

A JSON RPC response to cancel a task.
