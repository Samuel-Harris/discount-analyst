"""End-to-end mock pipeline persistence (no live LLM calls)."""

from __future__ import annotations

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from backend.crud import conversations as conv
from backend.crud import run_executions as runs
from backend.crud import workflow_runs as workflow_crud
from backend.crud.db_utils import new_id
from backend.contracts.agent_lane_order import PROFILER_ENTRY_AGENT_NAMES
from backend.db.migrate import migrate_to_head
from backend.db.session import create_dashboard_engine, create_session_factory
from backend.observability.logging import configure_dashboard_observability
from backend.pipeline.sqlmodel_runner import DashboardPipelineRunner
from backend.settings.testing import dashboard_settings_for_tests


@pytest.mark.asyncio
async def test_mock_workflow_completes_profiler_and_surveyor(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "w.sqlite"
    settings = dashboard_settings_for_tests(database_path=db_path)
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
        session.commit()

    runner = DashboardPipelineRunner(session_factory, settings)
    with patch("asyncio.sleep", new=AsyncMock()):
        await runner.execute_workflow(workflow_run_id)

    with session_factory() as session:
        detail = workflow_crud.fetch_workflow_detail(session, workflow_run_id)
    assert detail is not None
    surveyor_execution = detail["surveyor_execution"]
    assert surveyor_execution is not None
    assert surveyor_execution["status"] == "completed"
    surveyor_lanes = [r for r in detail["runs"] if r["entry_path"] == "surveyor"]
    profiler_lanes = [r for r in detail["runs"] if r["entry_path"] == "profiler"]
    assert len(profiler_lanes) == 1
    assert len(surveyor_lanes) == 3
    assert len(detail["runs"]) == 4
    surveyor_decisions = {r["decision_type"] for r in surveyor_lanes}
    assert "sentinel_rejection" in surveyor_decisions
    assert "arbiter" in surveyor_decisions
    profiler_run = profiler_lanes[0]
    assert profiler_run["status"] == "completed"
    for a in profiler_run["agent_executions"]:
        assert a["status"] in ("completed", "skipped")

    with session_factory() as session:
        surveyor_conv = conv.get_conversation_for_workflow_surveyor(
            session, workflow_run_id
        )
    assert surveyor_conv is not None


@pytest.mark.asyncio
async def test_surveyor_failure_stops_workflow_before_profiler_branches(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "surveyor_fail.sqlite"
    settings = dashboard_settings_for_tests(database_path=db_path)
    configure_dashboard_observability(settings)
    engine = create_dashboard_engine(settings)
    migrate_to_head(str(engine.url))
    session_factory = create_session_factory(engine)

    workflow_run_id = new_id()
    surveyor_execution_id = new_id()
    with session_factory() as session:
        workflow_crud.insert_workflow_run(
            session,
            workflow_run_id=workflow_run_id,
            portfolio_tickers=["M1.L"],
            is_mock=True,
        )
        workflow_crud.insert_surveyor_workflow_execution(
            session,
            execution_id=surveyor_execution_id,
            workflow_run_id=workflow_run_id,
        )
        runs.insert_ticker_run_with_agents(
            session,
            run_id=new_id(),
            workflow_run_id=workflow_run_id,
            ticker="M1.L",
            company_name="M1.L",
            entry_path="profiler",
            is_existing_position=True,
            is_mock=True,
            agent_names=PROFILER_ENTRY_AGENT_NAMES,
        )
        session.commit()

    runner = DashboardPipelineRunner(session_factory, settings)
    with (
        patch("backend.pipeline.sqlmodel_runner.asyncio.sleep", new=AsyncMock()),
        patch(
            "backend.pipeline.sqlmodel_runner.mock_outputs.mock_surveyor_dashboard_discoveries",
            side_effect=RuntimeError("surveyor provider failure"),
        ),
    ):
        await runner.execute_workflow(workflow_run_id)

    with session_factory() as session:
        detail = workflow_crud.fetch_workflow_detail(session, workflow_run_id)
    assert detail is not None
    assert detail["status"] == "failed"
    assert detail["error_message"] == "surveyor provider failure"
    surveyor_execution = detail["surveyor_execution"]
    assert surveyor_execution is not None
    assert surveyor_execution["status"] == "failed"

    profiler_lane = next(
        run for run in detail["runs"] if run["entry_path"] == "profiler"
    )
    assert profiler_lane["status"] == "cancelled"
    assert {row["status"] for row in profiler_lane["agent_executions"]} == {"cancelled"}


@pytest.mark.asyncio
async def test_manual_cancel_marks_workflow_and_children_cancelled(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "manual_cancel.sqlite"
    settings = dashboard_settings_for_tests(database_path=db_path)
    configure_dashboard_observability(settings)
    engine = create_dashboard_engine(settings)
    migrate_to_head(str(engine.url))
    session_factory = create_session_factory(engine)

    workflow_run_id = new_id()
    with session_factory() as session:
        workflow_crud.insert_workflow_run(
            session,
            workflow_run_id=workflow_run_id,
            portfolio_tickers=["M1.L"],
            is_mock=True,
        )
        workflow_crud.insert_surveyor_workflow_execution(
            session,
            execution_id=new_id(),
            workflow_run_id=workflow_run_id,
        )
        runs.insert_ticker_run_with_agents(
            session,
            run_id=new_id(),
            workflow_run_id=workflow_run_id,
            ticker="M1.L",
            company_name="M1.L",
            entry_path="profiler",
            is_existing_position=True,
            is_mock=True,
            agent_names=PROFILER_ENTRY_AGENT_NAMES,
        )
        session.commit()

    sleep_started = asyncio.Event()

    async def _blocking_sleep(_seconds: float) -> None:
        sleep_started.set()
        await asyncio.Event().wait()

    runner = DashboardPipelineRunner(session_factory, settings)
    with patch("backend.pipeline.sqlmodel_runner.asyncio.sleep", new=_blocking_sleep):
        task = runner.schedule_workflow_execution(workflow_run_id)
        await asyncio.wait_for(sleep_started.wait(), timeout=1.0)
        assert await runner.cancel_workflow_execution(workflow_run_id) is True
        assert await runner.cancel_workflow_execution(workflow_run_id) is True
        with pytest.raises(asyncio.CancelledError):
            await asyncio.wait_for(task, timeout=1.0)

    with session_factory() as session:
        detail = workflow_crud.fetch_workflow_detail(session, workflow_run_id)
    assert detail is not None
    assert detail["status"] == "cancelled"
    assert detail["error_message"] is None
    surveyor_execution = detail["surveyor_execution"]
    assert surveyor_execution is not None
    assert surveyor_execution["status"] == "cancelled"
    assert {run["status"] for run in detail["runs"]} == {"cancelled"}
    for run in detail["runs"]:
        assert {row["status"] for row in run["agent_executions"]} == {"cancelled"}
