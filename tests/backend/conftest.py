from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlmodel import Session

from backend.app.main import create_app
from backend.db.migrate import migrate_to_head
from backend.db.session import SessionFactory
from backend.observability.logging import configure_dashboard_observability
from backend.settings.config import Settings
from backend.settings.testing import dashboard_settings_for_tests


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
