from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import text

from backend.app.main import create_app
from backend.db.session import sqlite_url_from_path
from backend.settings.testing import dashboard_settings_for_tests

REPO_ROOT = Path(__file__).resolve().parents[3]
ALEMBIC_INI = REPO_ROOT / "backend" / "db" / "alembic.ini"
ALEMBIC_SCRIPT_DIR = REPO_ROOT / "backend" / "db" / "alembic"


def _alembic_config_for_url(database_url: str) -> Config:
    cfg = Config(str(ALEMBIC_INI))
    cfg.set_main_option("script_location", str(ALEMBIC_SCRIPT_DIR))
    cfg.set_main_option("sqlalchemy.url", database_url)
    return cfg


def test_startup_applies_alembic_head_and_is_idempotent(tmp_path: Path) -> None:
    db_path = tmp_path / "startup.sqlite"
    settings = dashboard_settings_for_tests(database_path=db_path)

    app_one = create_app(settings)
    app_two = create_app(settings)

    with app_two.state.db_session_factory() as session:
        tables = session.exec(
            text("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        ).all()

    table_names = {row[0] for row in tables}
    assert "workflow_runs" in table_names
    assert "candidate_snapshots" in table_names
    assert "agent_conversation_message_parts" in table_names
    assert not any(name.endswith("_json") for name in table_names)

    # Ensure both app instances are usable against the same upgraded DB.
    with app_one.state.db_session_factory() as session:
        rows = session.exec(text("SELECT COUNT(*) FROM workflow_runs")).one()
    assert rows[0] == 0


def test_alembic_metadata_matches_head(tmp_path: Path) -> None:
    db_path = tmp_path / "alembic-check.sqlite"
    database_url = sqlite_url_from_path(db_path)
    cfg = _alembic_config_for_url(database_url)
    command.upgrade(cfg, "head")
    command.check(cfg)
