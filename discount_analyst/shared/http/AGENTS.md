<!-- Parent: ../AGENTS.md -->
<!-- Generated: 2026-03-03 | Updated: 2026-03-03 -->

# http

## Purpose

Asynchronous HTTP client with exponential backoff and retry logic for rate limits, timeouts, and transient errors. Used by AI model providers and streaming agent runs.

## Key Files

| File | Description |
| --------- | ---------------------------- |
| `rate_limit_client.py` | `create_rate_limit_client()` factory and `stream_with_retries()` context manager for resilient API calls. |

## Subdirectories

None.

## For AI Agents

### Working In This Directory

- **Retry Configuration**: Adjust `_RETRY_EXCEPTIONS`, `RETRY_WAIT_MULTIPLIER`, and `stop_after_attempt` for different failure profiles.
- **Streaming**: `stream_with_retries` handles async generator retries (Tenacity cannot retry during iteration).

### Testing Requirements

- Verify retry logic with mock HTTP failures (429, timeouts, 503).
- Ensure `stream_with_retries` properly cleans up context on exception.

### Common Patterns

- **AsyncTenacityTransport**: Uses pydantic-ai's `AsyncTenacityTransport` with `RetryConfig` and `wait_retry_after` for Retry-After header support.
- **Exponential Backoff**: Fallback for errors without Retry-After header.

## Dependencies

### Internal

- This is used by `discount_analyst.shared.ai.model` and `scripts/run_dcf_analysis.py`.

### External

- **httpx**: Async HTTP client.
- **pydantic-ai**: `AsyncTenacityTransport`, `RetryConfig`, `wait_retry_after`.
- **tenacity**: Retry strategies.
- **openai**: Exception types for rate limit and timeout handling.

<!-- MANUAL: Any manually added notes below this line are preserved on regeneration -->
