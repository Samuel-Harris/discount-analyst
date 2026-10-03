"""Process model gate: shared slots and one quiet deadline."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator, AsyncIterator, Iterator
from contextlib import asynccontextmanager
from typing import Any

import pytest
from pydantic_ai._utils import group_by_temporal
from pydantic_ai.exceptions import ModelAPIError, ModelHTTPError
from pydantic_ai.models import Model, ModelRequestParameters

import discount_analyst.agents.runtime.model_gate as model_gate
from discount_analyst.agents.runtime.model_gate import (
    AdmittedModel,
    ProcessModelGate,
    is_provider_rate_limit,
    process_model_gate,
    reset_process_model_gate,
)


@pytest.fixture(autouse=True)
def isolated_process_model_gate() -> Iterator[None]:
    reset_process_model_gate()
    yield
    reset_process_model_gate()


def _fixed_quiet(seconds: float):
    def quiet(*, attempt: int, error_text: str) -> float:
        del attempt, error_text
        return seconds

    return quiet


def _quota_error() -> ModelHTTPError:
    return ModelHTTPError(429, "gate-test", {"message": "rate limit"})


class _RaisingModel(Model):
    def __init__(self, exc: BaseException) -> None:
        super().__init__()
        self._exc = exc

    @property
    def model_name(self) -> str:
        return "gate-test"

    @property
    def system(self) -> str:
        return "test"

    async def request(
        self,
        messages: list[Any],
        model_settings: Any,
        model_request_parameters: Any,
    ) -> Any:
        raise self._exc


class _ChunkModel(Model):
    @property
    def model_name(self) -> str:
        return "gate-test"

    @property
    def system(self) -> str:
        return "test"

    async def request(
        self,
        messages: list[Any],
        model_settings: Any,
        model_request_parameters: Any,
    ) -> Any:
        raise NotImplementedError

    @asynccontextmanager
    async def request_stream(
        self,
        messages: list[Any],
        model_settings: Any,
        model_request_parameters: Any,
        run_context: Any = None,
    ) -> AsyncGenerator[Any]:
        yield None


class _HoldingStreamModel(Model):
    def __init__(self) -> None:
        super().__init__()
        self.started = asyncio.Event()
        self.finish = asyncio.Event()

    @property
    def model_name(self) -> str:
        return "gate-test"

    @property
    def system(self) -> str:
        return "test"

    async def request(
        self,
        messages: list[Any],
        model_settings: Any,
        model_request_parameters: Any,
    ) -> Any:
        raise NotImplementedError

    @asynccontextmanager
    async def request_stream(
        self,
        messages: list[Any],
        model_settings: Any,
        model_request_parameters: Any,
        run_context: Any = None,
    ) -> AsyncGenerator[Any]:
        self.started.set()
        try:
            yield None
        finally:
            await self.finish.wait()


class _OrderGate(ProcessModelGate):
    def __init__(self, max_running: int) -> None:
        super().__init__(max_running)
        self.events: list[str] = []

    def arm(self, exc: BaseException, *, attempt: int) -> None:
        self.events.append("arm")
        super().arm(exc, attempt=attempt)

    def release(self) -> None:
        self.events.append("quiet" if self.quiet_remaining() > 0 else "open")
        super().release()


def test_each_model_family_has_its_own_gate(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(model_gate.settings, "model_max_running_sol", 5)
    monkeypatch.setattr(model_gate.settings, "model_max_running_luna", 20)
    reset_process_model_gate()
    sol = process_model_gate("gpt-6.1-sol")
    luna = process_model_gate("gpt-6-luna")
    other = process_model_gate("deepseek-v4-pro")
    assert sol is process_model_gate("gpt-6.1-sol")
    assert luna is process_model_gate("gpt-5.6-luna")
    assert sol is not luna
    assert other is not sol
    assert sol.max_running == 5
    assert luna.max_running == 20
    assert other.max_running == 2


def test_a_sol_rate_limit_does_not_quiet_luna(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(model_gate, "rate_limit_quiet_seconds", _fixed_quiet(60.0))
    monkeypatch.setattr(model_gate, "_now", lambda: 1_000.0)
    sol = process_model_gate("gpt-6.1-sol")
    luna = process_model_gate("gpt-6-luna")
    sol.arm(_quota_error(), attempt=0)
    assert sol.quiet_remaining() == 60.0
    assert luna.quiet_remaining() == 0.0


@pytest.mark.anyio
async def test_a_full_sol_gate_does_not_block_luna(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(model_gate.settings, "model_max_running_sol", 1)
    monkeypatch.setattr(model_gate.settings, "model_max_running_luna", 1)
    reset_process_model_gate()
    sol = process_model_gate("gpt-6.1-sol")
    luna = process_model_gate("gpt-6-luna")
    await sol.acquire("sol")
    await asyncio.wait_for(luna.acquire("luna"), timeout=0.2)
    luna.release()
    sol.release()


def test_same_exception_arms_the_quiet_deadline_once(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[int] = []

    def _quiet(*, attempt: int, error_text: str) -> float:
        del error_text
        calls.append(attempt)
        return 60.0

    clock = {"now": 1_000.0}
    monkeypatch.setattr(model_gate, "rate_limit_quiet_seconds", _quiet)
    monkeypatch.setattr(model_gate, "_now", lambda: clock["now"])
    gate = ProcessModelGate(2)
    exc = _quota_error()
    gate.arm(exc, attempt=1)
    gate.arm(exc, attempt=1)
    assert calls == [1]
    assert gate.quiet_remaining() == 60.0


def test_a_later_quota_failure_extends_the_deadline(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def _quiet(*, attempt: int, error_text: str) -> float:
        del error_text
        return 60.0 if attempt == 0 else 120.0

    clock = {"now": 1_000.0}
    monkeypatch.setattr(model_gate, "rate_limit_quiet_seconds", _quiet)
    monkeypatch.setattr(model_gate, "_now", lambda: clock["now"])
    gate = ProcessModelGate(2)
    first = _quota_error()
    second = _quota_error()
    gate.arm(first, attempt=0)
    assert gate.quiet_remaining() == 60.0
    gate.arm(second, attempt=1)
    assert gate.quiet_remaining() == 120.0


def test_wrapped_cause_does_not_arm_again(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[int] = []

    def _quiet(*, attempt: int, error_text: str) -> float:
        del error_text
        calls.append(attempt)
        return 60.0 if attempt == 0 else 120.0

    clock = {"now": 1_000.0}
    monkeypatch.setattr(model_gate, "rate_limit_quiet_seconds", _quiet)
    monkeypatch.setattr(model_gate, "_now", lambda: clock["now"])
    gate = ProcessModelGate(2)
    inner = _quota_error()
    gate.arm(inner, attempt=0)
    wrapped = ModelAPIError("gate-test", "Connection error.")
    wrapped.__cause__ = inner
    assert is_provider_rate_limit(wrapped) is True
    gate.arm(wrapped, attempt=1)
    assert calls == [0]
    assert gate.quiet_remaining() == 60.0


@pytest.mark.anyio
async def test_callers_share_one_slot() -> None:
    gate = ProcessModelGate(1)
    order: list[str] = []

    async def _hold() -> None:
        await gate.acquire("first")
        order.append("first-in")
        await asyncio.sleep(0.05)
        gate.release()
        order.append("first-out")

    async def _wait() -> None:
        await asyncio.sleep(0.01)
        order.append("second-wait")
        await gate.acquire("second")
        order.append("second-in")
        gate.release()

    await asyncio.gather(_hold(), _wait())
    assert order.index("first-out") < order.index("second-in")


@pytest.mark.anyio
async def test_quiet_blocks_a_free_slot(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(model_gate, "rate_limit_quiet_seconds", _fixed_quiet(0.05))
    gate = ProcessModelGate(2)
    holder_in = asyncio.Event()
    release_holder = asyncio.Event()

    async def _hold() -> None:
        await gate.acquire("holder")
        holder_in.set()
        await release_holder.wait()
        gate.release()

    holder_task = asyncio.create_task(_hold())
    await holder_in.wait()
    gate.arm(_quota_error(), attempt=0)
    started = asyncio.get_running_loop().time()
    try:
        await asyncio.wait_for(gate.acquire("other"), timeout=1.0)
        elapsed = asyncio.get_running_loop().time() - started
        gate.release()
    finally:
        release_holder.set()
        await holder_task
    assert elapsed >= 0.03


@pytest.mark.anyio
async def test_quiet_wait_releases_the_slot(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(model_gate, "rate_limit_quiet_seconds", _fixed_quiet(0.05))
    gate = ProcessModelGate(1)
    await gate.acquire("segment")
    gate.arm(_quota_error(), attempt=0)
    gate.release()
    await asyncio.wait_for(gate.acquire("retry"), timeout=1.0)
    gate.release()


@pytest.mark.anyio
async def test_admitted_model_arms_before_releasing_the_slot(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(model_gate, "rate_limit_quiet_seconds", _fixed_quiet(60.0))
    gate = _OrderGate(2)
    model = AdmittedModel(_RaisingModel(_quota_error()), gate)
    with pytest.raises(ModelHTTPError):
        await model.request([], None, ModelRequestParameters())
    assert gate.events == ["arm", "quiet"]


@pytest.mark.anyio
async def test_admitted_model_does_not_arm_when_cancelled() -> None:
    gate = _OrderGate(1)
    model = AdmittedModel(_RaisingModel(asyncio.CancelledError()), gate)
    with pytest.raises(asyncio.CancelledError):
        await model.request([], None, ModelRequestParameters())
    assert gate.events == ["open"]


@pytest.mark.anyio
async def test_request_stream_holds_the_slot_until_the_caller_exits() -> None:
    gate = ProcessModelGate(1)
    inner = _HoldingStreamModel()
    model = AdmittedModel(inner, gate)
    order: list[str] = []

    async def _stream() -> None:
        async with model.request_stream([], None, ModelRequestParameters()):
            order.append("streaming")
            await asyncio.sleep(0.05)
            order.append("still-holding")

    async def _other() -> None:
        await inner.started.wait()
        order.append("other-wait")
        await gate.acquire("other")
        order.append("other-in")
        gate.release()

    stream_task = asyncio.create_task(_stream())
    await inner.started.wait()
    other_task = asyncio.create_task(_other())
    try:
        await asyncio.sleep(0.01)
        assert "other-in" not in order
    finally:
        inner.finish.set()
    await stream_task
    await other_task
    assert order.index("still-holding") < order.index("other-in")


@pytest.mark.anyio
async def test_debounced_stream_returns_the_slot_from_another_task() -> None:
    gate = ProcessModelGate(1)
    model = AdmittedModel(_ChunkModel(), gate)

    async def chunks() -> AsyncIterator[str]:
        async with model.request_stream([], None, ModelRequestParameters()):
            yield "one"
            yield "two"

    collected: list[str] = []
    async with group_by_temporal(chunks(), 0.0) as groups:
        async for group in groups:
            collected.extend(group)

    assert collected == ["one", "two"]
    await asyncio.wait_for(gate.acquire("after"), timeout=0.2)
    gate.release()
