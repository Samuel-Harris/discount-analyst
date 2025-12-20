### Storage

Bases: `ABC`, `Generic[ContextT]`

A storage to retrieve and save tasks, as well as retrieve and save context.

The storage serves two purposes:

1. Task storage: Stores tasks in A2A protocol format with their status, artifacts, and message history
1. Context storage: Stores conversation context in a format optimized for the specific agent implementation

Source code in `.venv/lib/python3.12/site-packages/fasta2a/storage.py`

```python
class Storage(ABC, Generic[ContextT]):
    """A storage to retrieve and save tasks, as well as retrieve and save context.

    The storage serves two purposes:
    1. Task storage: Stores tasks in A2A protocol format with their status, artifacts, and message history
    2. Context storage: Stores conversation context in a format optimized for the specific agent implementation
    """

    @abstractmethod
    async def load_task(self, task_id: str, history_length: int | None = None) -> Task | None:
        """Load a task from storage.

        If the task is not found, return None.
        """

    @abstractmethod
    async def submit_task(self, context_id: str, message: Message) -> Task:
        """Submit a task to storage."""

    @abstractmethod
    async def update_task(
        self,
        task_id: str,
        state: TaskState,
        new_artifacts: list[Artifact] | None = None,
        new_messages: list[Message] | None = None,
    ) -> Task:
        """Update the state of a task. Appends artifacts and messages, if specified."""

    @abstractmethod
    async def load_context(self, context_id: str) -> ContextT | None:
        """Retrieve the stored context given the `context_id`."""

    @abstractmethod
    async def update_context(self, context_id: str, context: ContextT) -> None:
        """Updates the context for a `context_id`.

        Implementing agent can decide what to store in context.
        """

```

#### load_task

```python
load_task(
    task_id: str, history_length: int | None = None
) -> Task | None

```

Load a task from storage.

If the task is not found, return None.

Source code in `.venv/lib/python3.12/site-packages/fasta2a/storage.py`

```python
@abstractmethod
async def load_task(self, task_id: str, history_length: int | None = None) -> Task | None:
    """Load a task from storage.

    If the task is not found, return None.
    """

```

#### submit_task

```python
submit_task(context_id: str, message: Message) -> Task

```

Submit a task to storage.

Source code in `.venv/lib/python3.12/site-packages/fasta2a/storage.py`

```python
@abstractmethod
async def submit_task(self, context_id: str, message: Message) -> Task:
    """Submit a task to storage."""

```

#### update_task

```python
update_task(
    task_id: str,
    state: TaskState,
    new_artifacts: list[Artifact] | None = None,
    new_messages: list[Message] | None = None,
) -> Task

```

Update the state of a task. Appends artifacts and messages, if specified.

Source code in `.venv/lib/python3.12/site-packages/fasta2a/storage.py`

```python
@abstractmethod
async def update_task(
    self,
    task_id: str,
    state: TaskState,
    new_artifacts: list[Artifact] | None = None,
    new_messages: list[Message] | None = None,
) -> Task:
    """Update the state of a task. Appends artifacts and messages, if specified."""

```

#### load_context

```python
load_context(context_id: str) -> ContextT | None

```

Retrieve the stored context given the `context_id`.

Source code in `.venv/lib/python3.12/site-packages/fasta2a/storage.py`

```python
@abstractmethod
async def load_context(self, context_id: str) -> ContextT | None:
    """Retrieve the stored context given the `context_id`."""

```

#### update_context

```python
update_context(context_id: str, context: ContextT) -> None

```

Updates the context for a `context_id`.

Implementing agent can decide what to store in context.

Source code in `.venv/lib/python3.12/site-packages/fasta2a/storage.py`

```python
@abstractmethod
async def update_context(self, context_id: str, context: ContextT) -> None:
    """Updates the context for a `context_id`.

    Implementing agent can decide what to store in context.
    """

```
