model_response = model_request_sync(
    'anthropic:claude-haiku-4-5',
    [ModelRequest.user_text_prompt('What is the capital of France?')],
    instrument=True
)

print(model_response.parts[0].content)
#> The capital of France is Paris.

```

See [Debugging and Monitoring](../logfire/) for more details, including how to instrument with plain OpenTelemetry without Logfire.
