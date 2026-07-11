from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text

from backend.app.main import create_app
from backend.db.session import sqlite_url_from_path
from backend.db.verify_schema import verify_alembic_schema
from backend.settings.testing import dashboard_settings_for_tests


def test_startup_applies_alembic_head_and_is_idempotent(tmp_path: Path) -> None:
    db_path = tmp_path / "startup.sqlite"
    settings = dashboard_settings_for_tests(database_path=db_path)

    app_one = create_app(settings)
    app_two = create_app(settings)

    with app_two.state.db_session_factory() as session:
        tables = session.exec(
            text("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        ).all()
        revision = session.exec(text("SELECT version_num FROM alembic_version")).one()

    table_names = {row[0] for row in tables}
    assert revision[0] == "0010_unify_agent_executions"
    assert "workflow_runs" in table_names
    assert "candidate_snapshots" in table_names
    assert "agent_conversation_message_parts" in table_names
    assert "workflow_agent_executions" not in table_names
    assert not any(name.endswith("_json") for name in table_names)

    # Ensure both app instances are usable against the same upgraded DB.
    with app_one.state.db_session_factory() as session:
        rows = session.exec(text("SELECT COUNT(*) FROM workflow_runs")).one()
    assert rows[0] == 0


def test_alembic_metadata_matches_head(tmp_path: Path) -> None:
    db_path = tmp_path / "alembic-check.sqlite"
    verify_alembic_schema(database_url=sqlite_url_from_path(db_path))


def test_upgrade_from_0009_unifies_agent_executions_preserving_ids(
    tmp_path: Path,
) -> None:
    database_url = sqlite_url_from_path(tmp_path / "upgrade-from-0009.sqlite")
    database_directory = Path(__file__).resolve().parents[3] / "backend" / "db"
    config = Config(str(database_directory / "alembic.ini"))
    config.set_main_option("script_location", str(database_directory / "alembic"))
    config.set_main_option("sqlalchemy.url", database_url)
    command.upgrade(config, "0009_run_lane_aborted")

    engine = create_engine(database_url)
    with engine.begin() as connection:
        connection.execute(
            text(
                """
                INSERT INTO workflow_runs (id, started_at, status, is_mock)
                VALUES ('workflow-1', '2026-07-11 00:00:00', 'running', 1)
                """
            )
        )
        connection.execute(
            text(
                """
                INSERT INTO workflow_agent_executions (
                    id, workflow_run_id, agent_name, status, model_name
                )
                VALUES (
                    'surveyor-execution', 'workflow-1', 'surveyor', 'completed',
                    'gpt-5.2'
                )
                """
            )
        )
        connection.execute(
            text(
                """
                INSERT INTO runs (
                    id, workflow_run_id, ticker, company_name, started_at,
                    entry_path, is_existing_position, status, is_mock, lane_aborted
                )
                VALUES (
                    'run-1', 'workflow-1', 'ABC.L', 'ABC plc',
                    '2026-07-11 00:00:00', 'profiler', 1, 'running', 1, 0
                )
                """
            )
        )
        connection.execute(
            text(
                """
                INSERT INTO agent_executions (
                    id, run_id, agent_name, status, model_name
                )
                VALUES (
                    'profiler-execution', 'run-1', 'profiler', 'completed',
                    'claude-opus-4-6'
                )
                """
            )
        )
        connection.execute(
            text(
                """
                INSERT INTO candidate_snapshots (
                    id, workflow_agent_execution_id, agent_execution_id,
                    sort_order, ticker, company_name, exchange, currency,
                    market_cap_local, market_cap_display, sector, industry,
                    rationale, red_flags, data_gaps
                )
                VALUES
                    (
                        'surveyor-snapshot', 'surveyor-execution', NULL,
                        0, 'ABC.L', 'ABC plc', 'LSE', 'GBP',
                        1000000, '£1M', 'Industrials', 'Testing',
                        'Rationale', 'None', 'None'
                    ),
                    (
                        'profiler-snapshot', NULL, 'profiler-execution',
                        0, 'ABC.L', 'ABC plc', 'LSE', 'GBP',
                        1000000, '£1M', 'Industrials', 'Testing',
                        'Rationale', 'None', 'None'
                    )
                """
            )
        )
        connection.execute(
            text(
                """
                INSERT INTO agent_conversations (
                    id, workflow_agent_execution_id, agent_execution_id, system_prompt
                )
                VALUES
                    (
                        'surveyor-conversation', 'surveyor-execution', NULL,
                        'Surveyor prompt'
                    ),
                    (
                        'profiler-conversation', NULL, 'profiler-execution',
                        'Profiler prompt'
                    )
                """
            )
        )
    engine.dispose()

    command.upgrade(config, "head")

    upgraded_engine = create_engine(database_url)
    with upgraded_engine.connect() as connection:
        execution_rows = connection.execute(
            text(
                """
                SELECT id, workflow_run_id, run_id
                FROM agent_executions
                ORDER BY id
                """
            )
        ).all()
        snapshot_rows = connection.execute(
            text(
                """
                SELECT id, agent_execution_id
                FROM candidate_snapshots
                ORDER BY id
                """
            )
        ).all()
        conversation_rows = connection.execute(
            text(
                """
                SELECT id, agent_execution_id
                FROM agent_conversations
                ORDER BY id
                """
            )
        ).all()
        tables = connection.execute(
            text("SELECT name FROM sqlite_master WHERE type='table'")
        ).all()
    upgraded_engine.dispose()

    assert execution_rows == [
        ("profiler-execution", None, "run-1"),
        ("surveyor-execution", "workflow-1", None),
    ]
    assert snapshot_rows == [
        ("profiler-snapshot", "profiler-execution"),
        ("surveyor-snapshot", "surveyor-execution"),
    ]
    assert conversation_rows == [
        ("profiler-conversation", "profiler-execution"),
        ("surveyor-conversation", "surveyor-execution"),
    ]
    assert "workflow_agent_executions" not in {row[0] for row in tables}
