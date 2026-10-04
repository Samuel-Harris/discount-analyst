"""Process-wide admission for provider model streams.

Each model name has one ``ProcessModelGate``. A slot covers one
``request_stream`` segment. A provider rate limit sets that model's
ready time so another workflow cannot start a segment of the same
model during the retry sleep, after the slot has been released.
"""

from __future__ import annotations

import asyncio
import random
import re
import time
from collections import deque
from contextvars import ContextVar

import httpx
from openai import APIError, RateLimitError
from pydantic_ai.concurrency import AbstractConcurrencyLimiter
from pydantic_ai.exceptions import ModelHTTPError
from pydantic_ai.models import Model

from discount_analyst.domain.model_selection.model_name import ModelName

SLEEP_FLOOR_SECONDS: float = 60.0
SLEEP_CAP_SECONDS: float = 480.0
SLEEP_JITTER_RATIO: float = 0.25
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
_ARMED_MEMORY = 32
_UNNAMED_MAX_RUNNING = 1
_process_gates: dict[str, ProcessModelGate] = {}


def bind_stream_attempt(attempt: int) -> None:
    """Record this task's stream-retry attempt for ``AdmittedModel``.

    The model call does not receive the attempt, so the wrapper reads
    this task-local value and passes it to ``ProcessModelGate.arm``.
    A missing bind reads as attempt 0.
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
    return _is_provider_rate_limit(exc, seen=set())


def _is_provider_rate_limit(exc: BaseException, *, seen: set[int]) -> bool:
    exc_id = id(exc)
    if exc_id in seen:
        return False
    seen.add(exc_id)
    if isinstance(exc, RateLimitError):
        return True
    if isinstance(exc, ModelHTTPError) and exc.status_code == 429:
        return True
    if isinstance(exc, httpx.HTTPStatusError) and exc.response.status_code == 429:
        return True
    if error_text_indicates_rate_limit(provider_error_text(exc)):
        return True
    cause = exc.__cause__
    return cause is not None and _is_provider_rate_limit(cause, seen=seen)


def _exception_chain(exc: BaseException) -> tuple[BaseException, ...]:
    chain: list[BaseException] = []
    current: BaseException | None = exc
    seen: set[int] = set()
    while current is not None and id(current) not in seen:
        seen.add(id(current))
        chain.append(current)
        current = current.__cause__
    return tuple(chain)


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
    spread = min(wait_seconds * SLEEP_JITTER_RATIO, cap - wait_seconds)
    if spread <= 0:
        return wait_seconds
    return wait_seconds + random.uniform(0.0, spread)


def rate_limit_sleep_seconds(*, attempt: int, error_text: str) -> float:
    """Seconds to sleep for this attempt.

    Base is ``min(60 * 2**attempt, 480)``. A longer provider
    ``try again in`` hint raises that base, still capped at 480.
    High-side jitter never shrinks the base and never exceeds the cap.
    """
    exponential = min(SLEEP_FLOOR_SECONDS * (2**attempt), SLEEP_CAP_SECONDS)
    suggested = _provider_retry_after_seconds(error_text)
    wait_seconds = min(max(exponential, suggested), SLEEP_CAP_SECONDS)
    return _with_high_side_jitter(wait_seconds, cap=SLEEP_CAP_SECONDS)


class ProcessModelGate(AbstractConcurrencyLimiter):
    """In-process cap on provider model segments, plus one ready time.

    At most ``max_running`` slots are held. The queue is unlimited.
    Slots are an ``asyncio.Semaphore``: a debounced stream enters
    ``request_stream`` on one task and leaves it on another, and anyio's
    capacity limiter will not return a token borrowed by a different task.
    ``acquire`` sleeps until the gate is ready before taking a slot, and
    drops the slot if another arm moved the ready time. A rate-limit arm
    extends the ready time with ``max``. A failure already in the recent
    chain, including one wrapped as ``__cause__``, does not arm again.
    """

    def __init__(self, max_running: int) -> None:
        if max_running < 1:
            raise ValueError(f"max_running must be >= 1, got {max_running}.")
        self._slots = asyncio.Semaphore(max_running)
        self.max_running = max_running
        self._ready_at = 0.0
        self._armed_failures: deque[BaseException] = deque(maxlen=_ARMED_MEMORY)

    async def acquire(self, source: str) -> None:
        """Sleep until the gate is ready, then take one slot."""
        while True:
            remaining = self.sleep_time_remaining_s
            if remaining > 0:
                await asyncio.sleep(remaining)
                continue
            await self._slots.acquire()
            if self.sleep_time_remaining_s > 0:
                self._slots.release()
                continue
            return

    def release(self) -> None:
        """Return one slot. Only valid while this caller holds one."""
        self._slots.release()

    def arm(self, exc: BaseException, *, attempt: int) -> None:
        """Push the ready time later when ``exc`` is a provider rate limit.

        ``attempt`` is the zero-based stream retry index. A second call for
        the same failure, including a new exception whose ``__cause__`` is
        already armed, does not add another wait.
        """
        if not is_provider_rate_limit(exc):
            return
        chain = _exception_chain(exc)
        if any(
            remembered is link for link in chain for remembered in self._armed_failures
        ):
            return
        self._armed_failures.extend(chain)
        duration = rate_limit_sleep_seconds(
            attempt=attempt,
            error_text=provider_error_text(exc),
        )
        self._ready_at = max(self._ready_at, time.monotonic() + duration)

    @property
    def sleep_time_remaining_s(self) -> float:
        """Seconds until a new segment may start. ``0`` when the gate is ready."""
        remaining = self._ready_at - time.monotonic()
        if remaining <= 0:
            return 0.0
        return remaining

    async def sleep_until_ready(self) -> float:
        """Sleep until the ready time has passed. Does not take a slot."""
        waited = 0.0
        while True:
            remaining = self.sleep_time_remaining_s
            if remaining <= 0:
                return waited
            await asyncio.sleep(remaining)
            waited += remaining


def process_model_gate(model_name: str, max_running: int) -> ProcessModelGate:
    """Return this process's gate for ``model_name``, built once.

    A later call with a different ``max_running`` raises. The semaphore
    is not resized.
    """
    gate = _process_gates.get(model_name)
    if gate is None:
        gate = ProcessModelGate(max_running)
        _process_gates[model_name] = gate
        return gate
    if gate.max_running != max_running:
        raise ValueError(
            f"Process gate for {model_name!r} already has max_running "
            f"{gate.max_running}, got {max_running}."
        )
    return gate


def reset_process_model_gate() -> None:
    """Drop every model gate. Tests use this so a ready time cannot leak."""
    _process_gates.clear()


def gate_for_agent(agent: object) -> ProcessModelGate:
    """Return the gate the agent's model already holds.

    A retry that never entered ``AdmittedModel`` still arms that same gate.
    An agent with no model, such as a test double, uses an unnamed gate.
    """
    from discount_analyst.config.ai_models_config import AdmittedModel

    model = getattr(agent, "model", None)
    if isinstance(model, AdmittedModel):
        return model.gate
    if isinstance(model, Model):
        return _gate_for_configured_model(model.model_name)
    if isinstance(model, str):
        return _gate_for_configured_model(model)
    return process_model_gate("", _UNNAMED_MAX_RUNNING)


def _gate_for_configured_model(model_name: str) -> ProcessModelGate:
    from discount_analyst.config.ai_models_config import AIModelsConfig

    cap = AIModelsConfig(
        model_name=ModelName(model_name)
    ).pydantic_ai_model.max_concurrent_agents
    return process_model_gate(model_name, cap)
