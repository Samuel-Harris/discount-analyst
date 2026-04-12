"""End-to-end mock pipeline persistence (no live LLM calls)."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from backend.settings import DashboardSettings
from backend.crud import repository as repo
from backend.crud.repository import PROFILER_ENTRY_AGENT_NAMES, new_id
from backend.db.session import create_dashboard_engine, create_session_factory
from backend.db.migrate import migrate_to_head
from backend.pipeline import DashboardPipelineRunner


@pytest.mark.asyncio
async def test_mock_workflow_completes_profiler_and_surveyor(tmp_path) -> None:
    db_path = tmp_path / "w.sqlite"
    settings = DashboardSettings(database_path=db_path)
    engine = create_dashboard_engine(settings)
    migrate_to_head(str(engine.url))
    session_factory = create_session_factory(engine)

    wf = new_id()
    survey = new_id()
    portfolio = ["M1.L"]
    with session_factory() as session:
        repo.insert_workflow_run(
            session, workflow_run_id=wf, portfolio_tickers=portfolio, is_mock=True
        )
        repo.insert_surveyor_workflow_execution(
            session, execution_id=survey, workflow_run_id=wf
        )
    run_id = new_id()
    with session_factory() as session:
        repo.insert_ticker_run_with_agents(
            session,
            run_id=run_id,
            workflow_run_id=wf,
            ticker="M1.L",
            company_name="M1.L",
            entry_path="profiler",
            is_existing_position=False,
            is_mock=True,
            agent_names=PROFILER_ENTRY_AGENT_NAMES,
        )

    runner = DashboardPipelineRunner(session_factory, settings)
    with patch("asyncio.sleep", new=AsyncMock()):
        await runner.execute_workflow(wf)

    with session_factory() as session:
        detail = repo.fetch_workflow_detail(session, wf)
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
        conv = repo.get_conversation_for_workflow_surveyor(session, wf)
    assert conv is not None
