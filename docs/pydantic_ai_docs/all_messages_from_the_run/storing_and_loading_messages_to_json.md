## Storing and loading messages (to JSON)

While maintaining conversation state in memory is enough for many applications, often times you may want to store the messages history of an agent run on disk or in a database. This might be for evals, for sharing data between Python and JavaScript/TypeScript, or any number of other use cases.

The intended way to do this is using a `TypeAdapter`.

We export ModelMessagesTypeAdapter that can be used for this, or you can create your own.

Here's an example showing how:

[Learn about Gateway](../gateway) serialize messages to json

```python
from pydantic_core import to_jsonable_python

from pydantic_ai import (
    Agent,
    ModelMessagesTypeAdapter,  # (1)!
)

agent = Agent('gateway/openai:gpt-5', system_prompt='Be a helpful assistant.')

result1 = agent.run_sync('Tell me a joke.')
history_step_1 = result1.all_messages()
as_python_objects = to_jsonable_python(history_step_1)  # (2)!
same_history_as_step_1 = ModelMessagesTypeAdapter.validate_python(as_python_objects)

result2 = agent.run_sync(  # (3)!
    'Tell me a different joke.', message_history=same_history_as_step_1
)

```

1. Alternatively, you can create a `TypeAdapter` from scratch:

   ```python
   from pydantic import TypeAdapter
   from pydantic_ai import ModelMessage
   ModelMessagesTypeAdapter = TypeAdapter(list[ModelMessage])

   ```

1. Alternatively you can serialize to/from JSON directly:

   ```python
   from pydantic_core import to_json
   ...
   as_json_objects = to_json(history_step_1)
   same_history_as_step_1 = ModelMessagesTypeAdapter.validate_json(as_json_objects)

   ```

1. You can now continue the conversation with history `same_history_as_step_1` despite creating a new agent run.

serialize messages to json

```python
from pydantic_core import to_jsonable_python

from pydantic_ai import (
    Agent,
    ModelMessagesTypeAdapter,  # (1)!
)

agent = Agent('openai:gpt-5', system_prompt='Be a helpful assistant.')

result1 = agent.run_sync('Tell me a joke.')
history_step_1 = result1.all_messages()
as_python_objects = to_jsonable_python(history_step_1)  # (2)!
same_history_as_step_1 = ModelMessagesTypeAdapter.validate_python(as_python_objects)

result2 = agent.run_sync(  # (3)!
    'Tell me a different joke.', message_history=same_history_as_step_1
)

```

1. Alternatively, you can create a `TypeAdapter` from scratch:

   ```python
   from pydantic import TypeAdapter
   from pydantic_ai import ModelMessage
   ModelMessagesTypeAdapter = TypeAdapter(list[ModelMessage])

   ```

1. Alternatively you can serialize to/from JSON directly:

   ```python
   from pydantic_core import to_json
   ...
   as_json_objects = to_json(history_step_1)
   same_history_as_step_1 = ModelMessagesTypeAdapter.validate_json(as_json_objects)

   ```

1. You can now continue the conversation with history `same_history_as_step_1` despite creating a new agent run.

_(This example is complete, it can be run "as is")_
