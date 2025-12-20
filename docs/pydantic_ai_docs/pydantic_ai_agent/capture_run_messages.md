### capture_run_messages

```python
capture_run_messages() -> Iterator[list[ModelMessage]]

```

Context manager to access the messages used in a run, run_sync, or run_stream call.

Useful when a run may raise an exception, see [model errors](../../agents/#model-errors) for more information.

Examples:

```python
from pydantic_ai import Agent, capture_run_messages

agent = Agent('test')

with capture_run_messages() as messages:
    try:
        result = agent.run_sync('foobar')
    except Exception:
        print(messages)
        raise

```

Note

If you call `run`, `run_sync`, or `run_stream` more than once within a single `capture_run_messages` context, `messages` will represent the messages exchanged during the first call only.

Source code in `pydantic_ai_slim/pydantic_ai/_agent_graph.py`

````python
@contextmanager
def capture_run_messages() -> Iterator[list[_messages.ModelMessage]]:
    """Context manager to access the messages used in a [`run`][pydantic_ai.agent.AbstractAgent.run], [`run_sync`][pydantic_ai.agent.AbstractAgent.run_sync], or [`run_stream`][pydantic_ai.agent.AbstractAgent.run_stream] call.

    Useful when a run may raise an exception, see [model errors](../agents.md#model-errors) for more information.

    Examples:
    ```python
    from pydantic_ai import Agent, capture_run_messages

    agent = Agent('test')

    with capture_run_messages() as messages:
        try:
            result = agent.run_sync('foobar')
        except Exception:
            print(messages)
            raise
    ```

    !!! note
        If you call `run`, `run_sync`, or `run_stream` more than once within a single `capture_run_messages` context,
        `messages` will represent the messages exchanged during the first call only.
    """
    token = None
    messages: list[_messages.ModelMessage] = []

    # Try to reuse existing message context if available
    try:
        messages = _messages_ctx_var.get().messages
    except LookupError:
        # No existing context, create a new one
        token = _messages_ctx_var.set(_RunMessages(messages))

    try:
        yield messages
    finally:
        # Clean up context if we created it
        if token is not None:
            _messages_ctx_var.reset(token)

````
