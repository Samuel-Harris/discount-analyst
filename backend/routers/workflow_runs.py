"""Grouped workflow run list, detail, create, and mock-only delete."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status

from discount_analyst.agents.common.ai_logging import AI_LOGFIRE

from backend.contracts.api import (
    CreateWorkflowRunRequest,
    CreateWorkflowRunResponse,
    ProfilerRunCreated,
    WorkflowRunDetailResponse,
    WorkflowRunListItem,
)
from backend.deps import DbSession
from backend.contracts.agent_lane_order import PROFILER_ENTRY_AGENT_NAMES
from backend.crud.db_utils import new_id
from backend.crud.run_executions import (
    NoFailedAgentsToRetryError,
    RetryWorkflowRunNotFoundError,
    RetryWorkflowRunNotTerminalError,
    insert_ticker_run_with_agents,
    prepare_retry_failed_agents,
)
from backend.crud.workflow_runs import (
    delete_workflow_run_if_mock,
    fetch_workflow_detail,
    insert_surveyor_workflow_execution,
    insert_workflow_run,
    list_workflow_runs as list_workflow_runs_from_db,
    workflow_run_exists,
)
from backend.pipeline.sqlmodel_runner import (
    DashboardPipelineRunner,
    WorkflowTaskAlreadyActiveError,
)
from backend.serialisation.workflows import workflow_detail, workflow_list_item
from common.config import Settings

router = APIRouter(tags=["workflow_runs"])


def get_runner(request: Request) -> DashboardPipelineRunner:
    return request.app.state.pipeline_runner


def get_settings(request: Request) -> Settings:
    return request.app.state.settings


Runner = Annotated[DashboardPipelineRunner, Depends(get_runner)]
SettingsDep = Annotated[Settings, Depends(get_settings)]


@router.get("")
def list_workflow_runs(session: DbSession) -> list[WorkflowRunListItem]:
    rows = list_workflow_runs_from_db(session)
    AI_LOGFIRE.debug("Listed workflow runs", count=len(rows))
    return [workflow_list_item(r) for r in rows]


@router.get("/{workflow_run_id}")
def get_workflow_run(
    workflow_run_id: str, session: DbSession
) -> WorkflowRunDetailResponse:
    d = fetch_workflow_detail(session, workflow_run_id)
    if d is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Workflow run not found"
        )
    AI_LOGFIRE.debug("Fetched workflow run detail", workflow_run_id=workflow_run_id)
    return workflow_detail(d)


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_workflow_run(
    body: CreateWorkflowRunRequest,
    session: DbSession,
    runner: Runner,
    settings: SettingsDep,
) -> CreateWorkflowRunResponse:
    workflow_run_id = new_id()
    surveyor_exec_id = new_id()
    is_mock = True if settings.deploy_env == "DEV" else body.is_mock
    AI_LOGFIRE.info(
        "Creating workflow run",
        workflow_run_id=workflow_run_id,
        portfolio_ticker_count=len(body.portfolio_tickers),
        is_mock=is_mock,
    )
    insert_workflow_run(
        session,
        workflow_run_id=workflow_run_id,
        portfolio_tickers=body.portfolio_tickers,
        is_mock=is_mock,
    )
    insert_surveyor_workflow_execution(
        session,
        execution_id=surveyor_exec_id,
        workflow_run_id=workflow_run_id,
    )
    profiler_created: list[ProfilerRunCreated] = []
    for raw_ticker in body.portfolio_tickers:
        ticker = raw_ticker.strip()
        if not ticker:
            continue
        run_id = new_id()
        insert_ticker_run_with_agents(
            session,
            run_id=run_id,
            workflow_run_id=workflow_run_id,
            ticker=ticker,
            company_name=ticker,
            entry_path="profiler",
            is_existing_position=True,
            is_mock=is_mock,
            agent_names=PROFILER_ENTRY_AGENT_NAMES,
        )
        profiler_created.append(ProfilerRunCreated(run_id=run_id, ticker=ticker))

    session.commit()

    resp = CreateWorkflowRunResponse(
        workflow_run_id=workflow_run_id,
        profiler_runs=profiler_created,
        surveyor_started=True,
    )
    runner.schedule_workflow_execution(workflow_run_id)
    AI_LOGFIRE.info(
        "Background workflow execution task scheduled",
        workflow_run_id=workflow_run_id,
    )
    return resp


@router.post("/{workflow_run_id}/cancel", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_workflow_run(
    workflow_run_id: str, session: DbSession, runner: Runner
) -> None:
    if not workflow_run_exists(session, workflow_run_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Workflow run not found"
        )
    await runner.cancel_workflow_execution(workflow_run_id)
    AI_LOGFIRE.info(
        "Workflow run cancellation requested", workflow_run_id=workflow_run_id
    )


@router.post(
    "/{workflow_run_id}/retry_failed_agents",
    status_code=status.HTTP_202_ACCEPTED,
)
async def retry_failed_agents(
    workflow_run_id: str, session: DbSession, runner: Runner
) -> None:
    if runner.has_active_workflow_task(workflow_run_id):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Workflow run is already active",
        )
    try:
        preparation = prepare_retry_failed_agents(session, workflow_run_id)
        session.commit()
    except RetryWorkflowRunNotFoundError as exc:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Workflow run not found"
        ) from exc
    except RetryWorkflowRunNotTerminalError as exc:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Workflow run is not terminal",
        ) from exc
    except NoFailedAgentsToRetryError as exc:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No failed agents to retry",
        ) from exc
    try:
        runner.schedule_workflow_execution(workflow_run_id)
    except WorkflowTaskAlreadyActiveError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Workflow run is already active",
        ) from exc
    AI_LOGFIRE.info(
        "Workflow failed-agent retry scheduled",
        workflow_run_id=workflow_run_id,
        surveyor_reset=preparation.surveyor_reset,
        lane_reset_count=preparation.lane_reset_count,
        agent_execution_reset_count=preparation.agent_execution_reset_count,
    )


@router.delete("/{workflow_run_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_workflow_run(workflow_run_id: str, session: DbSession) -> None:
    ok = delete_workflow_run_if_mock(session, workflow_run_id)
    if not ok:
        if not workflow_run_exists(session, workflow_run_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Workflow run not found"
            )
        AI_LOGFIRE.warning(
            "Delete workflow run forbidden (non-mock run)",
            workflow_run_id=workflow_run_id,
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only mock workflow runs can be deleted",
        )
