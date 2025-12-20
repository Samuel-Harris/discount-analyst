### Broker

Bases: `ABC`

The broker class is in charge of scheduling the tasks.

The HTTP server uses the broker to schedule tasks.

The simple implementation is the `InMemoryBroker`, which is the broker that runs the tasks in the same process as the HTTP server. That said, this class can be extended to support remote workers.

Source code in `.venv/lib/python3.12/site-packages/fasta2a/broker.py`

```python
@dataclass
class Broker(ABC):
    """The broker class is in charge of scheduling the tasks.

    The HTTP server uses the broker to schedule tasks.

    The simple implementation is the `InMemoryBroker`, which is the broker that
    runs the tasks in the same process as the HTTP server. That said, this class can be
    extended to support remote workers.
    """

    @abstractmethod
    async def run_task(self, params: TaskSendParams) -> None:
        """Send a task to be executed by the worker."""
        raise NotImplementedError('send_run_task is not implemented yet.')

    @abstractmethod
    async def cancel_task(self, params: TaskIdParams) -> None:
        """Cancel a task."""
        raise NotImplementedError('send_cancel_task is not implemented yet.')

    @abstractmethod
    async def __aenter__(self) -> Self: ...

    @abstractmethod
    async def __aexit__(self, exc_type: Any, exc_value: Any, traceback: Any): ...

    @abstractmethod
    def receive_task_operations(self) -> AsyncIterator[TaskOperation]:
        """Receive task operations from the broker.

        On a multi-worker setup, the broker will need to round-robin the task operations
        between the workers.
        """

```

#### run_task

```python
run_task(params: TaskSendParams) -> None

```

Send a task to be executed by the worker.

Source code in `.venv/lib/python3.12/site-packages/fasta2a/broker.py`

```python
@abstractmethod
async def run_task(self, params: TaskSendParams) -> None:
    """Send a task to be executed by the worker."""
    raise NotImplementedError('send_run_task is not implemented yet.')

```

#### cancel_task

```python
cancel_task(params: TaskIdParams) -> None

```

Cancel a task.

Source code in `.venv/lib/python3.12/site-packages/fasta2a/broker.py`

```python
@abstractmethod
async def cancel_task(self, params: TaskIdParams) -> None:
    """Cancel a task."""
    raise NotImplementedError('send_cancel_task is not implemented yet.')

```

#### receive_task_operations

```python
receive_task_operations() -> AsyncIterator[TaskOperation]

```

Receive task operations from the broker.

On a multi-worker setup, the broker will need to round-robin the task operations between the workers.

Source code in `.venv/lib/python3.12/site-packages/fasta2a/broker.py`

```python
@abstractmethod
def receive_task_operations(self) -> AsyncIterator[TaskOperation]:
    """Receive task operations from the broker.

    On a multi-worker setup, the broker will need to round-robin the task operations
    between the workers.
    """

```
