from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from backend.settings.config import DashboardSettings
from backend.db.migrate import migrate_to_head
from backend.app.main import create_app


@pytest.fixture
def dashboard_settings(tmp_path, monkeypatch) -> DashboardSettings:
    # pydantic-settings reads ``ENV`` from the process; pin it so tests do not
    # inherit launch / shell ``ENV=DEV`` (which would force mock-only behaviour).
    monkeypatch.setenv("ENV", "PROD")
    return DashboardSettings(database_path=tmp_path / "dashboard.sqlite")


@pytest.fixture
def test_app(dashboard_settings: DashboardSettings):
    return create_app(dashboard_settings)


@pytest.fixture
def client(test_app):
    with TestClient(test_app) as test_client:
        yield test_client


@pytest.fixture
def db_session_factory(test_app):
    return test_app.state.db_session_factory


@pytest.fixture
def db_session(db_session_factory) -> Session:
    with db_session_factory() as session:
        yield session


@pytest.fixture
def migrated_temp_db_url(tmp_path) -> str:
    db_path = tmp_path / "migration_smoke.sqlite"
    db_url = f"sqlite:///{db_path}"
    migrate_to_head(db_url)
    return db_url
