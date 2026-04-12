from __future__ import annotations

from pathlib import Path

from sqlalchemy import text

from backend.app.main import create_app
from backend.settings.config import DashboardSettings


def test_startup_applies_alembic_head_and_is_idempotent(tmp_path: Path) -> None:
    db_path = tmp_path / "startup.sqlite"
    settings = DashboardSettings(database_path=db_path)

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
