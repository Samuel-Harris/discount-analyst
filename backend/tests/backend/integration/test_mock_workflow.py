"""End-to-end mock pipeline persistence (no live LLM calls)."""

from __future__ import annotations

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from sqlmodel import Session, col, select

from discount_analyst.adapters.persistence.crud.conversations import (
    get_conversation_for_run_agent,
    get_conversation_for_workflow_agent,
)
from discount_analyst.adapters.persistence.crud import run_executions as runs
from discount_analyst.adapters.persistence.crud import workflow_runs as workflow_crud
from discount_analyst.adapters.persistence.crud.portfolio_allocations import (
    get_portfolio_allocation_for_workflow,
)
from discount_analyst.adapters.persistence.crud.db_utils import new_id
from discount_analyst.adapters.persistence.migrate import migrate_to_head
from discount_analyst.adapters.persistence.models import (
    AgentExecution,
    AgentNameDb,
    ExecutionStatusDb,
    Run,
    WorkflowInvestmentThesis,
    WorkflowInvestmentThesisOriginDb,
    WorkflowRun,
    WorkflowRunStatusDb,
)
from discount_analyst.adapters.simulation import mock_outputs
from discount_analyst.agents.strategist.schema import MispricingThesis
from discount_analyst.application.workflows.agent_lane_order import (
    PROFILER_ENTRY_AGENT_NAMES,
)
from discount_analyst.adapters.persistence.session import (
    SessionFactory,
    create_dashboard_engine,
    create_session_factory,
)
from discount_analyst.adapters.observability.logging import (
    configure_dashboard_observability,
)
from discount_analyst.adapters.orchestration.sqlmodel_runner import (
    DashboardPipelineRunner,
)
from discount_analyst.config.testing_settings import dashboard_settings_for_tests
from discount_analyst.agents.appraiser.system_prompt import (
    SYSTEM_PROMPT as APPRAISER_SYSTEM_PROMPT,
)
from discount_analyst.agents.common_prompts.current_date import with_current_date
from discount_analyst.agents.surveyor.schema import SurveyorOutput


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
            surveyor_execution_id=survey,
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
    assert detail["status"] == "completed"
    surveyor_execution = detail["surveyor_execution"]
    assert surveyor_execution is not None
    assert surveyor_execution["status"] == "completed"
    assert surveyor_execution["model_name"] is None
    curator_execution = detail["curator_execution"]
    assert curator_execution is not None
    assert curator_execution["status"] == "completed"
    surveyor_lanes = [r for r in detail["runs"] if r["entry_path"] == "surveyor"]
    profiler_lanes = [r for r in detail["runs"] if r["entry_path"] == "profiler"]
    assert len(profiler_lanes) == 1
    assert len(surveyor_lanes) == 3
    assert len(detail["runs"]) == 4
    surveyor_decisions = {r["decision_type"] for r in surveyor_lanes}
    assert "sentinel_rejection" in surveyor_decisions
    assert "rating_table" in surveyor_decisions
    profiler_run = profiler_lanes[0]
    assert profiler_run["status"] == "completed"
    for a in profiler_run["agent_executions"]:
        assert a["status"] in ("completed", "skipped")
        assert a["model_name"] is None

    with session_factory() as session:
        surveyor_conv = get_conversation_for_workflow_agent(
            session, workflow_run_id, agent_name=AgentNameDb.SURVEYOR
        )
        allocation = get_portfolio_allocation_for_workflow(session, workflow_run_id)
    assert surveyor_conv is not None
    assert allocation is not None
    equity = sum(position.target_weight_pct for position in allocation.positions)
    assert abs(equity + allocation.cash.target_weight_pct - 100.0) <= 0.05
    for position in allocation.positions:
        if position.policy.kind == "forced_zero":
            assert position.target_weight_pct == 0.0
            assert position.acceptable_weight_high_pct == 0.0


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
            surveyor_execution_id=surveyor_execution_id,
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
        patch("asyncio.sleep", new=AsyncMock()),
        patch(
            "discount_analyst.adapters.orchestration.stages.surveyor_stage.mock_outputs.mock_surveyor_dashboard_discoveries",
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
    curator_execution = detail["curator_execution"]
    assert curator_execution is not None
    assert curator_execution["status"] == "cancelled"

    with session_factory() as session:
        snapshots = list(
            session.scalars(
                select(WorkflowInvestmentThesis).where(
                    col(WorkflowInvestmentThesis.workflow_run_id) == workflow_run_id
                )
            )
        )
    assert snapshots == []

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
    with patch("asyncio.sleep", new=_blocking_sleep):
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


@pytest.mark.asyncio
async def test_appraiser_conversation_failure_does_not_leave_appraiser_completed(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "appraiser_conversation_fail.sqlite"
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

    original_insert = runs.insert_conversation_for_agent_execution

    def _fail_appraiser_conversation(
        session: Session,
        *,
        conversation_id: str,
        agent_execution_id: str,
        system_prompt: str,
        messages_json: str | None = None,
        assistant_response: str | None = None,
        messages: list[object] | None = None,
    ) -> None:
        if system_prompt == with_current_date(APPRAISER_SYSTEM_PROMPT):
            raise KeyError("builtin-tool-call")
        original_insert(
            session,
            conversation_id=conversation_id,
            agent_execution_id=agent_execution_id,
            system_prompt=system_prompt,
            messages_json=messages_json,
            assistant_response=assistant_response,
            messages=messages,
        )

    runner = DashboardPipelineRunner(session_factory, settings)
    with (
        patch("asyncio.sleep", new=AsyncMock()),
        patch(
            "discount_analyst.adapters.orchestration.stages.surveyor_stage.mock_outputs.mock_surveyor_dashboard_discoveries",
            return_value=SurveyorOutput.model_construct(candidates=[]),
        ),
        patch(
            "discount_analyst.adapters.orchestration.stages.ticker_lane_stage.mock_outputs.mock_sentinel_proceed_for_dashboard_lane",
            return_value=True,
        ),
        patch(
            "discount_analyst.adapters.persistence.crud.run_executions.insert_conversation_for_agent_execution",
            side_effect=_fail_appraiser_conversation,
        ),
    ):
        await runner.execute_workflow(workflow_run_id)

    with session_factory() as session:
        detail = workflow_crud.fetch_workflow_detail(session, workflow_run_id)
    assert detail is not None
    assert detail["status"] == "failed"
    profiler_lane = next(
        run for run in detail["runs"] if run["entry_path"] == "profiler"
    )
    statuses = {
        row["agent_name"]: row["status"] for row in profiler_lane["agent_executions"]
    }
    assert profiler_lane["status"] == "failed"
    assert statuses["appraiser"] == "failed"


@pytest.mark.asyncio
async def test_lane_abort_marks_unreached_downstream_agents_skipped(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "downstream_skips.sqlite"
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

    def _researcher_failure(candidate: object) -> object:
        del candidate
        raise RuntimeError("researcher validation failed")

    runner = DashboardPipelineRunner(session_factory, settings)
    with (
        patch("asyncio.sleep", new=AsyncMock()),
        patch(
            "discount_analyst.adapters.orchestration.stages.surveyor_stage.mock_outputs.mock_surveyor_dashboard_discoveries",
            return_value=SurveyorOutput.model_construct(candidates=[]),
        ),
        patch.object(
            mock_outputs, "mock_deep_research", side_effect=_researcher_failure
        ),
    ):
        await runner.execute_workflow(workflow_run_id)

    with session_factory() as session:
        detail = workflow_crud.fetch_workflow_detail(session, workflow_run_id)
    assert detail is not None
    assert detail["status"] == "failed"
    profiler_lane = next(
        run for run in detail["runs"] if run["entry_path"] == "profiler"
    )
    statuses = {
        row["agent_name"]: row["status"] for row in profiler_lane["agent_executions"]
    }
    assert statuses["profiler"] == "completed"
    assert statuses["researcher"] == "failed"
    assert statuses["strategist"] == "skipped"
    assert statuses["sentinel"] == "skipped"
    assert statuses["appraiser"] == "skipped"
    curator_execution = detail["curator_execution"]
    assert curator_execution is not None
    assert curator_execution["status"] == "skipped"


@pytest.mark.asyncio
async def test_retry_resume_skips_completed_surveyor_without_duplicate_lanes(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "resume_without_duplicate_surveyor.sqlite"
    settings = dashboard_settings_for_tests(database_path=db_path)
    configure_dashboard_observability(settings)
    engine = create_dashboard_engine(settings)
    migrate_to_head(str(engine.url))
    session_factory = create_session_factory(engine)

    workflow_run_id = new_id()
    surveyor_execution_id = new_id()
    portfolio = ["M1.L"]
    profiler_run_id = new_id()
    with session_factory() as session:
        workflow_crud.insert_workflow_run(
            session,
            workflow_run_id=workflow_run_id,
            portfolio_tickers=portfolio,
            is_mock=True,
            surveyor_execution_id=surveyor_execution_id,
        )
        runs.insert_ticker_run_with_agents(
            session,
            run_id=profiler_run_id,
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
        original_surveyor_lane_ids = {
            row["id"] for row in detail["runs"] if row["entry_path"] == "surveyor"
        }
        assert len(original_surveyor_lane_ids) == 3

        workflow = session.get(WorkflowRun, workflow_run_id)
        run = session.get(Run, profiler_run_id)
        assert workflow is not None
        assert run is not None
        workflow.status = WorkflowRunStatusDb.COMPLETED
        workflow.completed_at = None
        run.status = WorkflowRunStatusDb.FAILED
        run.completed_at = None
        run.error_message = "researcher failed"
        session.add(workflow)
        session.add(run)
        for agent_name, status in (
            ("researcher", ExecutionStatusDb.FAILED),
            ("strategist", ExecutionStatusDb.SKIPPED),
            ("sentinel", ExecutionStatusDb.SKIPPED),
            ("appraiser", ExecutionStatusDb.SKIPPED),
        ):
            execution_id = runs.get_agent_execution_id_by_run_and_agent(
                session, run_id=profiler_run_id, agent_name=agent_name
            )
            assert execution_id is not None
            execution = session.get(AgentExecution, execution_id)
            assert execution is not None
            execution.status = status
            execution.error_message = (
                "researcher failed" if status == ExecutionStatusDb.FAILED else None
            )
            session.add(execution)
        runs.prepare_retry_failed_agents(session, workflow_run_id)
        session.commit()

    with (
        patch("asyncio.sleep", new=AsyncMock()),
        patch(
            "discount_analyst.adapters.orchestration.stages.surveyor_stage.mock_outputs.mock_surveyor_dashboard_discoveries",
            side_effect=AssertionError("surveyor should not rerun on lane retry"),
        ),
    ):
        await runner.execute_workflow(workflow_run_id)

    with session_factory() as session:
        detail = workflow_crud.fetch_workflow_detail(session, workflow_run_id)
    assert detail is not None
    assert detail["surveyor_execution"] is not None
    assert detail["surveyor_execution"]["status"] == "completed"
    current_surveyor_lane_ids = {
        row["id"] for row in detail["runs"] if row["entry_path"] == "surveyor"
    }
    assert current_surveyor_lane_ids == original_surveyor_lane_ids
    profiler_lane = next(row for row in detail["runs"] if row["id"] == profiler_run_id)
    assert profiler_lane["status"] == "completed"


def _bootstrap_mock_workflow(
    session_factory: SessionFactory,
    *,
    workflow_run_id: str,
    portfolio: list[str],
) -> None:
    with session_factory() as session:
        workflow_crud.insert_workflow_run(
            session,
            workflow_run_id=workflow_run_id,
            portfolio_tickers=portfolio,
            is_mock=True,
        )
        runs.insert_ticker_run_with_agents(
            session,
            run_id=new_id(),
            workflow_run_id=workflow_run_id,
            ticker=portfolio[0],
            company_name=portfolio[0],
            entry_path="profiler",
            is_existing_position=True,
            is_mock=True,
            agent_names=PROFILER_ENTRY_AGENT_NAMES,
        )
        session.commit()


@pytest.mark.asyncio
async def test_second_mock_workflow_keeps_snapshotted_thesis(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "two_run.sqlite"
    settings = dashboard_settings_for_tests(database_path=db_path)
    configure_dashboard_observability(settings)
    engine = create_dashboard_engine(settings)
    migrate_to_head(str(engine.url))
    session_factory = create_session_factory(engine)
    portfolio = ["M1.L"]
    first_workflow_id = new_id()
    _bootstrap_mock_workflow(
        session_factory, workflow_run_id=first_workflow_id, portfolio=portfolio
    )
    runner = DashboardPipelineRunner(session_factory, settings)
    with patch("asyncio.sleep", new=AsyncMock()):
        await runner.execute_workflow(first_workflow_id)

    with session_factory() as session:
        first_snapshots = list(
            session.scalars(
                select(WorkflowInvestmentThesis).where(
                    col(WorkflowInvestmentThesis.workflow_run_id) == first_workflow_id
                )
            )
        )
    assert first_snapshots
    assert {row.origin for row in first_snapshots} == {
        WorkflowInvestmentThesisOriginDb.REPLACED
    }
    chosen = first_snapshots[0]
    prior_argument = chosen.mispricing_argument
    prior_ticker = chosen.ticker

    second_workflow_id = new_id()
    _bootstrap_mock_workflow(
        session_factory, workflow_run_id=second_workflow_id, portfolio=portfolio
    )
    with patch("asyncio.sleep", new=AsyncMock()):
        await runner.execute_workflow(second_workflow_id)

    with session_factory() as session:
        second_run = session.scalars(
            select(Run).where(
                col(Run.workflow_run_id) == second_workflow_id,
                col(Run.ticker) == prior_ticker,
            )
        ).one()
        strategist_conv = get_conversation_for_run_agent(
            session, run_id=second_run.id, agent_name=AgentNameDb.STRATEGIST.value
        )
        curator_conv = get_conversation_for_workflow_agent(
            session, second_workflow_id, agent_name=AgentNameDb.CURATOR
        )
        second_snapshots = list(
            session.scalars(
                select(WorkflowInvestmentThesis).where(
                    col(WorkflowInvestmentThesis.workflow_run_id) == second_workflow_id
                )
            )
        )
    assert strategist_conv is not None
    assert "<prior_mispricing_thesis>" in strategist_conv["messages_json"]
    assert prior_argument in strategist_conv["messages_json"]
    live = MispricingThesis.model_validate_json(strategist_conv["assistant_response"])
    assert live.mispricing_argument == prior_argument
    assert curator_conv is not None
    assert prior_argument in curator_conv["messages_json"]
    matching = [
        row
        for row in second_snapshots
        if row.ticker.casefold() == prior_ticker.casefold()
    ]
    assert matching
    assert matching[0].origin == WorkflowInvestmentThesisOriginDb.COPIED_PRIOR
    assert matching[0].mispricing_argument == prior_argument
