### Worker

Bases: `ABC`, `Generic[ContextT]`

A worker is responsible for executing tasks.

Source code in `.venv/lib/python3.12/site-packages/fasta2a/worker.py`

```python
@dataclass
class Worker(ABC, Generic[ContextT]):
    """A worker is responsible for executing tasks."""

    broker: Broker
    storage: Storage[ContextT]

    @asynccontextmanager
    async def run(self) -> AsyncIterator[None]:
        """Run the worker.

        It connects to the broker, and it makes itself available to receive commands.
        """
        async with anyio.create_task_group() as tg:
            tg.start_soon(self._loop)
            yield
            tg.cancel_scope.cancel()

    async def _loop(self) -> None:
        async for task_operation in self.broker.receive_task_operations():
            await self._handle_task_operation(task_operation)

    async def _handle_task_operation(self, task_operation: TaskOperation) -> None:
        try:
            with use_span(task_operation['_current_span']):
                with tracer.start_as_current_span(
                    f'{task_operation["operation"]} task', attributes={'logfire.tags': ['fasta2a']}
                ):
                    if task_operation['operation'] == 'run':
                        await self.run_task(task_operation['params'])
                    elif task_operation['operation'] == 'cancel':
                        await self.cancel_task(task_operation['params'])
                    else:
                        assert_never(task_operation)
        except Exception:
            await self.storage.update_task(task_operation['params']['id'], state='failed')

    @abstractmethod
    async def run_task(self, params: TaskSendParams) -> None: ...

    @abstractmethod
    async def cancel_task(self, params: TaskIdParams) -> None: ...

    @abstractmethod
    def build_message_history(self, history: list[Message]) -> list[Any]: ...

    @abstractmethod
    def build_artifacts(self, result: Any) -> list[Artifact]: ...

```

#### run

```python
run() -> AsyncIterator[None]

```

Run the worker.

It connects to the broker, and it makes itself available to receive commands.

Source code in `.venv/lib/python3.12/site-packages/fasta2a/worker.py`

```python
@asynccontextmanager
async def run(self) -> AsyncIterator[None]:
    """Run the worker.

    It connects to the broker, and it makes itself available to receive commands.
    """
    async with anyio.create_task_group() as tg:
        tg.start_soon(self._loop)
        yield
        tg.cancel_scope.cancel()

```

This module contains the schema for the agent card.
