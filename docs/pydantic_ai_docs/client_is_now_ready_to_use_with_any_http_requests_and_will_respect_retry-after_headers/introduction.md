```

The `wait_retry_after` function automatically detects `Retry-After` headers in 429 (rate limit) responses and waits for the specified time. If no header is present, it falls back to exponential backoff.
