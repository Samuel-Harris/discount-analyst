<!-- Parent: ../AGENTS.md -->
<!-- Generated: 2026-04-05 -->

# http

## Purpose

Provider HTTP transport with Tenacity retries, Retry-After handling, and OpenAI error-body logging. Streaming retry/resume for agent runs lives in `discount_analyst.agents.common.streaming_retries`, not here.

## Key Files

| File                 | Description                                          |
| -------------------- | ---------------------------------------------------- |
| `retrying_client.py` | `create_rate_limit_client()` and Tenacity transport. |

## Subdirectories

None.

## Dependencies

### Internal

- Used by `discount_analyst.agents.common.model` when constructing pydantic-ai providers.

### External

- **httpx**, **tenacity**, **pydantic-ai** (`AsyncTenacityTransport`, `RetryConfig`, `wait_retry_after`), **openai** (exception types), **logfire**.
