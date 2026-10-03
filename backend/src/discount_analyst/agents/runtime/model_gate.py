"""Process-wide admission for provider model streams.

One ``ProcessModelGate`` is shared by every model this process builds.
A slot covers one ``request_stream`` segment. A provider rate limit also
arms a single quiet deadline so another workflow cannot start a segment
during the retry wait, after the slot has been released.
"""

from __future__ import annotations

import asyncio
import random
import re
import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from contextvars import ContextVar
from typing import Any

import httpx
from openai import APIError, RateLimitError
from pydantic_ai.concurrency import AbstractConcurrencyLimiter, ConcurrencyLimiter
from pydantic_ai.exceptions import ModelHTTPError
from pydantic_ai.messages import ModelMessage, ModelResponse
from pydantic_ai.models import Model, ModelRequestParameters, StreamedResponse
from pydantic_ai.models.wrapper import WrapperModel
from pydantic_ai.settings import ModelSettings
from pydantic_ai import RunContext
from pydantic_ai.usage import RequestUsage

from discount_analyst.config.settings import settings

QUIET_FLOOR_SECONDS: float = 60.0
QUIET_CAP_SECONDS: float = 480.0
QUIET_JITTER_RATIO: float = 0.25
_RATE_LIMIT_TEXT_NEEDLES = (
    "rate limit",
    "tokens per min",
    "requests per min",
    "tpm",
    "rpm",
    "too many requests",
)
_TRY_AGAIN_IN_RE = re.compile(
    r"try again in (?P<value>\d+(?:\.\d+)?)(?P<unit>ms|s)?",
    re.IGNORECASE,
)
_ATTEMPT: ContextVar[int] = ContextVar("discount_analyst_model_gate_attempt", default=0)
_process_gate: ProcessModelGate | None = None


def bind_stream_attempt(attempt: int) -> None:
    """Record this task's stream-retry attempt for quiet-period arming.

    ``attempt`` is the zero-based index ``stream_with_retries`` already
    uses. A missing bind reads as attempt 0. The value is task-local.
    """
    _ATTEMPT.set(attempt)


def bound_stream_attempt() -> int:
    """Return the attempt bound on this task, or 0."""
    return _ATTEMPT.get()


def error_text_indicates_rate_limit(text: str) -> bool:
    """True when ``text`` contains a quota needle. A bare ``429`` does not."""
    lowered = text.lower()
    return any(needle in lowered for needle in _RATE_LIMIT_TEXT_NEEDLES)


def _exception_text(exc: BaseException) -> str:
    if isinstance(exc, APIError):
        message = getattr(exc, "message", None)
        if message:
            return str(message)
    if isinstance(exc, ModelHTTPError):
        return f"{exc.status_code} {exc.body}"
    return str(exc)


def provider_error_text(exc: BaseException) -> str:
    parts: list[str] = []
    current: BaseException | None = exc
    seen: set[int] = set()
    while current is not None and id(current) not in seen:
        seen.add(id(current))
        parts.append(_exception_text(current))
        current = current.__cause__
    return "\n".join(parts)


def is_provider_rate_limit(exc: BaseException) -> bool:
    """True when today's long streaming wait treats ``exc`` as quota.

    Walks ``__cause__``. Recognises OpenAI ``RateLimitError``, pydantic-ai
    ``ModelHTTPError`` 429, httpx 429, and the quota needles. Connection,
    timeout, and 5xx failures are false.
    """
    if isinstance(exc, RateLimitError):
        return True
    if isinstance(exc, ModelHTTPError) and exc.status_code == 429:
        return True
    if isinstance(exc, httpx.HTTPStatusError) and exc.response.status_code == 429:
        return True
    if isinstance(exc, APIError) and error_text_indicates_rate_limit(
        _exception_text(exc)
    ):
        return True
    if error_text_indicates_rate_limit(_exception_text(exc)):
        return True
    if error_text_indicates_rate_limit(provider_error_text(exc)):
        return True
    cause = exc.__cause__
    return cause is not None and is_provider_rate_limit(cause)


def _provider_retry_after_seconds(text: str) -> float:
    match = _TRY_AGAIN_IN_RE.search(text)
    if match is None:
        return 0.0
    value = float(match.group("value"))
    unit = (match.group("unit") or "s").casefold()
    if unit == "ms":
        return value / 1000.0
    return value


def _with_high_side_jitter(wait_seconds: float, *, cap: float) -> float:
    """Add up to 25% extra wait. Never waits less than ``wait_seconds``."""
    if wait_seconds >= cap:
        return cap
    spread = min(wait_seconds * QUIET_JITTER_RATIO, cap - wait_seconds)
    if spread <= 0:
        return wait_seconds
    return wait_seconds + random.uniform(0.0, spread)


def rate_limit_quiet_seconds(*, attempt: int, error_text: str) -> float:
    """Quiet duration for this attempt.

    Base is ``min(60 * 2**attempt, 480)``. A longer provider
    ``try again in`` hint raises that base, still capped at 480.
    High-side jitter never shrinks the base and never exceeds the cap.
    """
    exponential = min(QUIET_FLOOR_SECONDS * (2**attempt), QUIET_CAP_SECONDS)
    suggested = _provider_retry_after_seconds(error_text)
    wait_seconds = min(max(exponential, suggested), QUIET_CAP_SECONDS)
    return _with_high_side_jitter(wait_seconds, cap=QUIET_CAP_SECONDS)


def _now() -> float:
    return time.monotonic()


class ProcessModelGate(AbstractConcurrencyLimiter):
    """In-process cap on provider model segments, plus one quiet deadline.

    At most ``max_running`` slots are held. The queue is unlimited.
    ``acquire`` waits out the quiet deadline before taking a slot, and
    drops the slot if another arm moved the deadline. A rate-limit arm
    extends the deadline with ``max`` and does not stack two waits for
    the same exception object.
    """

    def __init__(self, max_running: int) -> None:
        if max_running < 1:
            raise ValueError(f"max_running must be >= 1, got {max_running}.")
        self._slots = ConcurrencyLimiter(
            max_running=max_running,
            name="provider-model",
        )
        self._max_running = max_running
        self._quiet_until = 0.0
        self._last_armed_id: int | None = None

    @property
    def max_running(self) -> int:
        return self._max_running

    async def acquire(self, source: str) -> None:
        """Wait out the quiet deadline, then take one slot."""
        while True:
            remaining = self.quiet_remaining()
            if remaining > 0:
                await asyncio.sleep(remaining)
                continue
            await self._slots.acquire(source)
            if self.quiet_remaining() > 0:
                self._slots.release()
                continue
            return

    def release(self) -> None:
        """Return one slot. Only valid while this caller holds one."""
        self._slots.release()

    def arm_from_exception(self, exc: BaseException) -> None:
        """Extend the quiet deadline when ``exc`` is a provider rate limit.

        A second call with the same exception object does not add another
        wait. ``CancelledError`` is not an ``Exception`` and is not passed
        here.
        """
        if not is_provider_rate_limit(exc):
            return
        exc_id = id(exc)
        if self._last_armed_id == exc_id:
            return
        self._last_armed_id = exc_id
        duration = rate_limit_quiet_seconds(
            attempt=bound_stream_attempt(),
            error_text=provider_error_text(exc),
        )
        self._quiet_until = max(self._quiet_until, _now() + duration)

    def quiet_remaining(self) -> float:
        """Seconds until a new segment may start. ``0`` when the gate is open."""
        remaining = self._quiet_until - _now()
        if remaining <= 0:
            return 0.0
        return remaining

    async def wait_until_quiet(self) -> float:
        """Sleep until the quiet deadline has passed. Does not take a slot."""
        waited = 0.0
        while True:
            remaining = self.quiet_remaining()
            if remaining <= 0:
                return waited
            await asyncio.sleep(remaining)
            waited += remaining


def process_model_gate() -> ProcessModelGate:
    """Return this process's gate, built once from ``settings.model_max_running``."""
    global _process_gate
    if _process_gate is None:
        _process_gate = ProcessModelGate(settings.model_max_running)
    return _process_gate


def reset_process_model_gate() -> None:
    """Drop the process gate. Tests use this so a quiet deadline cannot leak."""
    global _process_gate
    _process_gate = None


class AdmittedModel(WrapperModel):
    """Provider model that takes one process-gate slot per model call.

    On a provider rate limit the gate is armed before the slot is released,
    so another workflow cannot acquire in that gap.
    """

    def __init__(self, wrapped: Model, gate: ProcessModelGate) -> None:
        super().__init__(wrapped)
        self._gate = gate

    @property
    def gate(self) -> ProcessModelGate:
        return self._gate

    @asynccontextmanager
    async def _segment(self, source: str) -> AsyncIterator[None]:
        await self._gate.acquire(source)
        try:
            yield
        except Exception as exc:
            self._gate.arm_from_exception(exc)
            raise
        finally:
            self._gate.release()

    async def request(
        self,
        messages: list[ModelMessage],
        model_settings: ModelSettings | None,
        model_request_parameters: ModelRequestParameters,
    ) -> ModelResponse:
        async with self._segment(f"model:{self.model_name}"):
            return await self.wrapped.request(
                messages, model_settings, model_request_parameters
            )

    async def count_tokens(
        self,
        messages: list[ModelMessage],
        model_settings: ModelSettings | None,
        model_request_parameters: ModelRequestParameters,
    ) -> RequestUsage:
        async with self._segment(f"model:{self.model_name}"):
            return await self.wrapped.count_tokens(
                messages, model_settings, model_request_parameters
            )

    @asynccontextmanager
    async def request_stream(
        self,
        messages: list[ModelMessage],
        model_settings: ModelSettings | None,
        model_request_parameters: ModelRequestParameters,
        run_context: RunContext[Any] | None = None,
    ) -> AsyncIterator[StreamedResponse]:
        async with self._segment(f"model:{self.model_name}"):
            async with self.wrapped.request_stream(
                messages,
                model_settings,
                model_request_parameters,
                run_context,
            ) as response_stream:
                yield response_stream
