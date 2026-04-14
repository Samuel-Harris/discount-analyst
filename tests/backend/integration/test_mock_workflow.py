"""End-to-end mock pipeline persistence (no live LLM calls)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from backend.crud import conversations as conv
from backend.crud import run_executions as runs
from backend.crud import workflow_runs as workflow_crud
from backend.crud.db_utils import new_id
from backend.crud.run_executions import PROFILER_ENTRY_AGENT_NAMES
from backend.db.migrate import migrate_to_head
from backend.db.session import create_dashboard_engine, create_session_factory
from backend.observability.logging import configure_dashboard_observability
from backend.pipeline.sqlmodel_runner import DashboardPipelineRunner
from backend.settings.config import DashboardSettings


@pytest.mark.asyncio
async def test_mock_workflow_completes_profiler_and_surveyor(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "w.sqlite"
    settings = DashboardSettings(database_path=db_path)
    configure_dashboard_observability(settings)
    engine = create_dashboard_engine(settings)
    migrate_to_head(str(engine.url))
    session_factory = create_session_factory(engine)

    workflow_run_id = new_id()
    survey = new_id()
    portfolio = ["M1.L"]
    with session_factory() as session:
        workflow_crud.insert_workflow_run(
            session,
            workflow_run_id=workflow_run_id,
            portfolio_tickers=portfolio,
            is_mock=True,
        )
        workflow_crud.insert_surveyor_workflow_execution(
            session, execution_id=survey, workflow_run_id=workflow_run_id
        )
    run_id = new_id()
    with session_factory() as session:
        runs.insert_ticker_run_with_agents(
            session,
            run_id=run_id,
            workflow_run_id=workflow_run_id,
            ticker="M1.L",
            company_name="M1.L",
            entry_path="profiler",
            is_existing_position=True,
            is_mock=True,
            agent_names=PROFILER_ENTRY_AGENT_NAMES,
        )

    runner = DashboardPipelineRunner(session_factory, settings)
    with patch("asyncio.sleep", new=AsyncMock()):
        await runner.execute_workflow(workflow_run_id)

    with session_factory() as session:
        detail = workflow_crud.fetch_workflow_detail(session, workflow_run_id)
    assert detail is not None
    assert detail["surveyor_execution"]["status"] == "completed"
    surveyor_lanes = [r for r in detail["runs"] if r["entry_path"] == "surveyor"]
    profiler_lanes = [r for r in detail["runs"] if r["entry_path"] == "profiler"]
    assert len(profiler_lanes) == 1
    assert len(surveyor_lanes) == 3
    assert len(detail["runs"]) == 4
    profiler_run = profiler_lanes[0]
    assert profiler_run["status"] == "completed"
    for a in profiler_run["agent_executions"]:
        assert a["status"] in ("completed", "skipped")

    with session_factory() as session:
        surveyor_conv = conv.get_conversation_for_workflow_surveyor(
            session, workflow_run_id
        )
    assert surveyor_conv is not None
