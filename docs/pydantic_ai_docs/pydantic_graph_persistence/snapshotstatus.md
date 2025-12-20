### SnapshotStatus

```python
SnapshotStatus = Literal[
    "created", "pending", "running", "success", "error"
]

```

The status of a snapshot.

- `'created'`: The snapshot has been created but not yet run.
- `'pending'`: The snapshot has been retrieved with load_next but not yet run.
- `'running'`: The snapshot is currently running.
- `'success'`: The snapshot has been run successfully.
- `'error'`: The snapshot has been run but an error occurred.
