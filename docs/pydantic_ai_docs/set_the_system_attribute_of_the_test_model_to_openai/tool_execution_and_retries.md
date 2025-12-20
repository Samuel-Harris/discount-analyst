## Tool Execution and Retries

When a tool is executed, its arguments (provided by the LLM) are first validated against the function's signature using Pydantic (with optional [validation context](../output/#validation-context)). If validation fails (e.g., due to incorrect types or missing required arguments), a `ValidationError` is raised, and the framework automatically generates a RetryPromptPart containing the validation details. This prompt is sent back to the LLM, informing it of the error and allowing it to correct the parameters and retry the tool call.

Beyond automatic validation errors, the tool's own internal logic can also explicitly request a retry by raising the ModelRetry exception. This is useful for situations where the parameters were technically valid, but an issue occurred during execution (like a transient network error, or the tool determining the initial attempt needs modification).

```python
from pydantic_ai import ModelRetry


def my_flaky_tool(query: str) -> str:
    if query == 'bad':
        # Tell the LLM the query was bad and it should try again
        raise ModelRetry("The query 'bad' is not allowed. Please provide a different query.")
    # ... process query ...
    return 'Success!'

```

Raising `ModelRetry` also generates a `RetryPromptPart` containing the exception message, which is sent back to the LLM to guide its next attempt. Both `ValidationError` and `ModelRetry` respect the `retries` setting configured on the `Tool` or `Agent`.
