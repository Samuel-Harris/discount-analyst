### Retry Considerations

Pydantic AI and provider API clients have their own retry logic. When using Prefect, you may want to:

- Disable [HTTP Request Retries](../../retries/) in Pydantic AI
- Turn off your provider API client's retry logic (e.g., `max_retries=0` on a [custom OpenAI client](../../models/openai/#custom-openai-client))
- Rely on Prefect's task-level retry configuration for consistency

This prevents requests from being retried multiple times at different layers.
