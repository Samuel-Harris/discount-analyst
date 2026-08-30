from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlmodel import Session

from discount_analyst.adapters.observability.yfinance_freshness import (
    YfinanceFreshness,
    installed_yfinance_version,
)
from discount_analyst.composition.api import create_app
from discount_analyst.adapters.persistence.migrate import migrate_to_head
from discount_analyst.adapters.persistence.session import SessionFactory
from discount_analyst.adapters.observability.logging import (
    configure_dashboard_observability,
)
from discount_analyst.config.settings import Settings
from discount_analyst.config.testing_settings import dashboard_settings_for_tests


@pytest.fixture(autouse=True)
def stub_yfinance_freshness_check(monkeypatch: pytest.MonkeyPatch) -> None:
    """Dashboard tests must not call PyPI from GET /api/status."""

    async def _installed_is_current() -> YfinanceFreshness:
        installed = installed_yfinance_version()
        return YfinanceFreshness(
            installed_version=installed,
            latest_version=installed,
            is_outdated=False,
        )

    monkeypatch.setattr(
        "discount_analyst.entrypoints.api.routers.status.check_yfinance_freshness",
        _installed_is_current,
    )


@pytest.fixture
def dashboard_settings(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Settings:
    # pydantic-settings reads ``ENV`` from the process; pin it so tests do not
    # inherit launch / shell ``ENV=DEV`` (which would force mock-only behaviour).
    monkeypatch.setenv("ENV", "PROD")
    return dashboard_settings_for_tests(
        database_path=tmp_path / "dashboard.sqlite",
        deploy_env="PROD",
    )


@pytest.fixture
def test_app(dashboard_settings: Settings) -> FastAPI:
    return create_app(dashboard_settings)


@pytest.fixture
def client(test_app: FastAPI) -> Iterator[TestClient]:
    with TestClient(test_app) as test_client:
        yield test_client


@pytest.fixture
def db_session_factory(test_app: FastAPI) -> SessionFactory:
    return test_app.state.db_session_factory


@pytest.fixture
def db_session(db_session_factory: SessionFactory) -> Iterator[Session]:
    with db_session_factory() as session:
        yield session


@pytest.fixture
def migrated_temp_db_url(tmp_path: Path) -> str:
    configure_dashboard_observability(
        dashboard_settings_for_tests(database_path=tmp_path / "migration_smoke.sqlite")
    )
    db_path = tmp_path / "migration_smoke.sqlite"
    db_url = f"sqlite:///{db_path}"
    migrate_to_head(db_url)
    return db_url
