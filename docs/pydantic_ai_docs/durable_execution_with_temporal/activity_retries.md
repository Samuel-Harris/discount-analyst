## Activity Retries

On top of the automatic retries for request failures that Temporal will perform, Pydantic AI and various provider API clients also have their own request retry logic. Enabling these at the same time may cause the request to be retried more often than expected, with improper `Retry-After` handling.

When using Temporal, it's recommended to not use [HTTP Request Retries](../../retries/) and to turn off your provider API client's own retry logic, for example by setting `max_retries=0` on a [custom `OpenAIProvider` API client](../../models/openai/#custom-openai-client).

You can customize Temporal's retry policy using [activity configuration](#activity-configuration).
