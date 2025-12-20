wait_strategy_2 = wait_retry_after(
    fallback_strategy=wait_exponential(multiplier=2, max=120),
    max_wait=600  # Never wait more than 10 minutes
)

```

This wait strategy:

- Automatically parses `Retry-After` headers from HTTP 429 responses
- Supports both seconds format (`"30"`) and HTTP date format (`"Wed, 21 Oct 2015 07:28:00 GMT"`)
- Falls back to your chosen strategy when no header is present
- Respects the `max_wait` limit to prevent excessive delays
