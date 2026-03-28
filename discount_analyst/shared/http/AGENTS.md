<!-- Parent: ../AGENTS.md -->
<!-- Generated: 2026-03-03 | Updated: 2026-03-28 -->

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

- **Retry Configuration**: Adjust `_http_transport_should_retry`, `RETRY_WAIT_MULTIPLIER`, and Tenacity `stop_after_attempt` for different failure profiles.
- **Streaming**: `stream_with_retries` retries transient errors on `run_stream` entry and during `stream_output()` iteration (e.g. OpenAI TPM mid-stream), using exponential backoff or the API’s “try again in Xs” hint when present.

### Testing Requirements

- Verify retry logic with mock HTTP failures (429, timeouts, 503).
- Ensure `stream_with_retries` properly cleans up context on exception.

### Common Patterns

- **AsyncTenacityTransport**: Uses pydantic-ai's `AsyncTenacityTransport` with `RetryConfig` and `wait_retry_after` for Retry-After header support.
- **Exponential Backoff**: Fallback for errors without Retry-After header.
- **OpenAI diagnostics**: On non-success responses from `api.openai.com`, `create_rate_limit_client()` logs a truncated response body to Logfire (`OpenAI HTTP error response`) before raising, so 400s from `/v1/responses` include the API's error JSON in traces. (408/429 are skipped to avoid spam during retries.) Error bodies are loaded with `await response.aread()` in `_AsyncTenacityTransportWithErrorBody` first — otherwise httpx async `Response.text` raises `ResponseNotRead` and Logfire would show `<response body unavailable>`. Logging falls back to decoding `response.content` if `.text` still fails.
- **HTTP retries**: The Tenacity transport retries timeouts, connection errors, 408/429, and 5xx. **4xx other than 408/429 are not retried** (fail fast); retrying e.g. 400 Bad Request only delays failures and floods logs.

## Dependencies

### Internal

- This is used by `discount_analyst.shared.ai.model` and `scripts/run_dcf_analysis.py`.

### External

- **httpx**: Async HTTP client.
- **pydantic-ai**: `AsyncTenacityTransport`, `RetryConfig`, `wait_retry_after`.
- **tenacity**: Retry strategies.
- **openai**: Exception types for rate limit and timeout handling.
- **logfire**: Warning logs for OpenAI HTTP error bodies (when configured).

<!-- MANUAL: Any manually added notes below this line are preserved on regeneration -->
