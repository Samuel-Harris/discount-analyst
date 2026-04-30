"""Unit tests for dashboard Logfire bootstrap wiring."""

from __future__ import annotations

from typing import Any

import pytest
from fastapi import FastAPI

import backend.observability.logging as observability_logging
from backend.settings.testing import dashboard_settings_for_tests


class _FakeBaseLogfire:
    def __init__(self) -> None:
        self.configure_calls: list[dict[str, Any]] = []
        self.instrument_httpx_calls: list[bool] = []
        self.instrument_fastapi_calls: list[int] = []

    def configure(self, **kwargs: Any) -> None:
        self.configure_calls.append(kwargs)

    def instrument_httpx(self, *, capture_all: bool = False) -> None:
        self.instrument_httpx_calls.append(capture_all)

    def instrument_fastapi(self, app: FastAPI) -> None:
        self.instrument_fastapi_calls.append(id(app))


class _FakeAiLogfire:
    def __init__(self) -> None:
        self.instrument_pydantic_ai_calls = 0

    def instrument_pydantic_ai(self) -> None:
        self.instrument_pydantic_ai_calls += 1


def test_configure_dashboard_observability_bootstrap_and_app_idempotency(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_logfire = _FakeBaseLogfire()
    fake_ai_logfire = _FakeAiLogfire()
    monkeypatch.setattr(observability_logging, "logfire", fake_logfire)
    monkeypatch.setattr(observability_logging, "AI_LOGFIRE", fake_ai_logfire)
    monkeypatch.setattr(observability_logging, "_configured", False)
    monkeypatch.setattr(observability_logging, "_instrumented_app_ids", set[int]())

    settings = dashboard_settings_for_tests(
        logfire_api_key="test-token",
        deploy_env="PROD",
    )
    app_a = FastAPI()
    app_b = FastAPI()

    observability_logging.configure_dashboard_observability(settings, app_a)
    observability_logging.configure_dashboard_observability(settings, app_a)
    observability_logging.configure_dashboard_observability(settings, app_b)

    assert len(fake_logfire.configure_calls) == 1
    assert fake_ai_logfire.instrument_pydantic_ai_calls == 1
    assert fake_logfire.instrument_httpx_calls == [True]
    assert fake_logfire.instrument_fastapi_calls == [id(app_a), id(app_b)]
