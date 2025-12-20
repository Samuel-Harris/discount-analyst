### Accessing Messages from Results

After running an agent, you can access the messages exchanged during that run from the `result` object.

Both RunResult (returned by Agent.run, Agent.run_sync) and StreamedRunResult (returned by Agent.run_stream) have the following methods:

- all_messages(): returns all messages, including messages from prior runs. There's also a variant that returns JSON bytes, all_messages_json().
- new_messages(): returns only the messages from the current run. There's also a variant that returns JSON bytes, new_messages_json().

StreamedRunResult and complete messages

On StreamedRunResult, the messages returned from these methods will only include the final result message once the stream has finished.

E.g. you've awaited one of the following coroutines:

- StreamedRunResult.stream_output()
- StreamedRunResult.stream_text()
- StreamedRunResult.stream_responses()
- StreamedRunResult.get_output()

**Note:** The final result message will NOT be added to result messages if you use .stream_text(delta=True) since in this case the result content is never built as one string.

Example of accessing methods on a RunResult :

[Learn about Gateway](../gateway) run_result_messages.py

```python
from pydantic_ai import Agent

agent = Agent('gateway/openai:gpt-5', system_prompt='Be a helpful assistant.')

result = agent.run_sync('Tell me a joke.')
print(result.output)
#> Did you hear about the toothpaste scandal? They called it Colgate.
