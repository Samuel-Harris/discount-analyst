### Retry Modes

- `'legacy'` (default): 5 attempts, basic retry behavior
- `'standard'`: 3 attempts, more comprehensive error coverage
- `'adaptive'`: 3 attempts with client-side rate limiting (recommended for handling `ThrottlingException`)

For more details on boto3 retry configuration, see the [AWS boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/guide/retries.html).

Note

Unlike other providers that use httpx for HTTP requests, Bedrock uses boto3's native retry mechanisms. The retry strategies described in [HTTP Request Retries](../../retries/) do not apply to Bedrock.
