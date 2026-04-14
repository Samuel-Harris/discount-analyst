"""Grouped workflow run list, detail, create, and mock-only delete."""

from __future__ import annotations

import asyncio
from typing import Annotated

import logfire
from fastapi import APIRouter, Depends, HTTPException, Request, status

from backend.contracts.api import (
    CreateWorkflowRunRequest,
    CreateWorkflowRunResponse,
    ProfilerRunCreated,
    WorkflowRunDetailResponse,
    WorkflowRunListItem,
)
from backend.deps import DbSession
from backend.crud.db_utils import new_id
from backend.crud.run_executions import (
    PROFILER_ENTRY_AGENT_NAMES,
    insert_ticker_run_with_agents,
)
from backend.crud.workflow_runs import (
    delete_workflow_run_if_mock,
    fetch_workflow_detail,
    insert_surveyor_workflow_execution,
    insert_workflow_run,
    list_workflow_runs as list_workflow_runs_from_db,
    workflow_run_exists,
)
from backend.pipeline.sqlmodel_runner import DashboardPipelineRunner
from backend.serialisation.workflows import workflow_detail, workflow_list_item
from backend.settings.config import DashboardSettings

router = APIRouter(tags=["workflow_runs"])


def get_runner(request: Request) -> DashboardPipelineRunner:
    return request.app.state.pipeline_runner


def get_settings(request: Request) -> DashboardSettings:
    return request.app.state.settings


Runner = Annotated[DashboardPipelineRunner, Depends(get_runner)]
Settings = Annotated[DashboardSettings, Depends(get_settings)]


@router.get("")
def list_workflow_runs(session: DbSession) -> list[WorkflowRunListItem]:
    rows = list_workflow_runs_from_db(session)
    logfire.debug("Listed workflow runs", count=len(rows))
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
    logfire.debug("Fetched workflow run detail", workflow_run_id=workflow_run_id)
    return workflow_detail(d)


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_workflow_run(
    body: CreateWorkflowRunRequest,
    session: DbSession,
    runner: Runner,
    settings: Settings,
) -> CreateWorkflowRunResponse:
    workflow_run_id = new_id()
    surveyor_exec_id = new_id()
    is_mock = True if settings.deploy_env == "DEV" else body.is_mock
    logfire.info(
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

    resp = CreateWorkflowRunResponse(
        workflow_run_id=workflow_run_id,
        profiler_runs=profiler_created,
        surveyor_started=True,
    )
    asyncio.create_task(runner.execute_workflow(workflow_run_id))
    logfire.info(
        "Background workflow execution task scheduled",
        workflow_run_id=workflow_run_id,
    )
    return resp


@router.delete("/{workflow_run_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_workflow_run(workflow_run_id: str, session: DbSession) -> None:
    ok = delete_workflow_run_if_mock(session, workflow_run_id)
    if not ok:
        if not workflow_run_exists(session, workflow_run_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Workflow run not found"
            )
        logfire.warning(
            "Delete workflow run forbidden (non-mock run)",
            workflow_run_id=workflow_run_id,
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only mock workflow runs can be deleted",
        )
