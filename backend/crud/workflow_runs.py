"""WorkflowRun-level queries and mutations (portfolio, status, list/detail)."""

from __future__ import annotations

from typing import Any

from sqlalchemy import case, desc, func
from sqlmodel import Session, col, select

from backend.contracts.workflow_rows import (
    AgentExecutionRow,
    SurveyorExecutionRow,
    TickerRunRow,
    WorkflowRunDetailRecord,
    WorkflowRunHeaderRow,
    WorkflowRunListRow,
)
from backend.crud.db_utils import (
    ACTIVE_EXECUTION_STATUSES,
    TERMINAL_EXECUTION_STATUSES,
    new_id,
    utc_now,
)
from backend.db.models import (
    AgentExecution,
    AgentNameDb,
    EntryPathDb,
    ExecutionStatusDb,
    Run,
    WorkflowAgentExecution,
    WorkflowRun,
    WorkflowRunPortfolioTicker,
    WorkflowRunStatusDb,
)


def get_workflow_run_inputs(
    session: Session, workflow_run_id: str
) -> tuple[list[str], bool] | None:
    wf = session.get(WorkflowRun, workflow_run_id)
    if wf is None:
        return None
    tickers = list(
        session.scalars(
            select(WorkflowRunPortfolioTicker)
            .where(col(WorkflowRunPortfolioTicker.workflow_run_id) == workflow_run_id)
            .order_by(col(WorkflowRunPortfolioTicker.sort_order))
        )
    )
    return [t.ticker for t in tickers], wf.is_mock


def list_profiler_runs_for_workflow(
    session: Session, workflow_run_id: str
) -> list[tuple[str, str]]:
    rows = list(
        session.scalars(
            select(Run)
            .where(
                col(Run.workflow_run_id) == workflow_run_id,
                col(Run.entry_path) == EntryPathDb.PROFILER,
            )
            .order_by(col(Run.started_at))
        )
    )
    return [(row.id, row.ticker) for row in rows]


def recompute_workflow_status(session: Session, workflow_run_id: str) -> None:
    wf = session.get(WorkflowRun, workflow_run_id)
    if wf is None:
        return

    surveyor = session.scalars(
        select(WorkflowAgentExecution).where(
            col(WorkflowAgentExecution.workflow_run_id) == workflow_run_id,
            col(WorkflowAgentExecution.agent_name) == AgentNameDb.SURVEYOR,
        )
    ).first()
    runs = list(
        session.scalars(select(Run).where(col(Run.workflow_run_id) == workflow_run_id))
    )

    new_status: WorkflowRunStatusDb | None = None
    if surveyor is None:
        new_status = WorkflowRunStatusDb.RUNNING
    elif surveyor.status.value == ExecutionStatusDb.FAILED.value:
        new_status = WorkflowRunStatusDb.FAILED
    elif surveyor.status.value in ACTIVE_EXECUTION_STATUSES:
        new_status = WorkflowRunStatusDb.RUNNING
    elif not runs:
        if surveyor.status.value in TERMINAL_EXECUTION_STATUSES:
            new_status = WorkflowRunStatusDb.COMPLETED
    else:
        statuses = [r.status.value for r in runs]
        if WorkflowRunStatusDb.FAILED.value in statuses:
            new_status = WorkflowRunStatusDb.FAILED
        elif WorkflowRunStatusDb.RUNNING.value in statuses:
            new_status = WorkflowRunStatusDb.RUNNING
        elif all(s == WorkflowRunStatusDb.COMPLETED.value for s in statuses):
            new_status = WorkflowRunStatusDb.COMPLETED
        else:
            new_status = WorkflowRunStatusDb.RUNNING

    if new_status is None:
        return

    wf.status = new_status
    if new_status == WorkflowRunStatusDb.RUNNING:
        wf.completed_at = None
    else:
        wf.completed_at = utc_now()
    session.add(wf)
    session.commit()


def insert_workflow_run(
    session: Session,
    *,
    workflow_run_id: str,
    portfolio_tickers: list[str],
    is_mock: bool,
) -> None:
    session.add(
        WorkflowRun(
            id=workflow_run_id,
            started_at=utc_now(),
            completed_at=None,
            status=WorkflowRunStatusDb.RUNNING,
            is_mock=is_mock,
            error_message=None,
        )
    )
    for idx, ticker in enumerate(portfolio_tickers):
        session.add(
            WorkflowRunPortfolioTicker(
                id=new_id(),
                workflow_run_id=workflow_run_id,
                sort_order=idx,
                ticker=ticker,
            )
        )
    session.commit()


def insert_surveyor_workflow_execution(
    session: Session,
    *,
    execution_id: str,
    workflow_run_id: str,
) -> None:
    session.add(
        WorkflowAgentExecution(
            id=execution_id,
            workflow_run_id=workflow_run_id,
            agent_name=AgentNameDb.SURVEYOR,
            status=ExecutionStatusDb.PENDING,
            started_at=None,
            completed_at=None,
            error_message=None,
        )
    )
    session.commit()


def list_workflow_runs(session: Session) -> list[WorkflowRunListRow]:
    stmt: Any = (  # pyright: ignore[reportUnknownVariableType, reportUnknownMemberType]
        select(  # pyright: ignore[reportCallIssue, reportUnknownMemberType]
            WorkflowRun.id,
            WorkflowRun.started_at,
            WorkflowRun.completed_at,
            WorkflowRun.status,
            WorkflowRun.is_mock,
            WorkflowRun.error_message,
            func.count(col(Run.id)),
            func.sum(
                case(
                    (col(Run.status) == WorkflowRunStatusDb.COMPLETED, 1),
                    else_=0,
                )
            ),
            func.sum(case((col(Run.status) == WorkflowRunStatusDb.FAILED, 1), else_=0)),
        )
        .select_from(WorkflowRun)
        .join(
            Run,
            col(Run.workflow_run_id) == col(WorkflowRun.id),
            isouter=True,
        )
        .group_by(WorkflowRun.id)
        .order_by(desc(col(WorkflowRun.started_at)))
    )
    rows: list[Any] = list(session.exec(stmt))  # pyright: ignore[reportUnknownArgumentType]
    out: list[WorkflowRunListRow] = []
    for r in rows:
        row: WorkflowRunListRow = {
            "id": r[0],
            "started_at": r[1],
            "completed_at": r[2],
            "status": r[3].value,
            "is_mock": bool(r[4]),
            "error_message": r[5],
            "ticker_run_count": int(r[6] or 0),
            "completed_ticker_run_count": int(r[7] or 0),
            "failed_ticker_run_count": int(r[8] or 0),
        }
        out.append(row)
    return out


def get_workflow_run_row(
    session: Session, workflow_run_id: str
) -> WorkflowRunHeaderRow | None:
    wf = session.get(WorkflowRun, workflow_run_id)
    if wf is None:
        return None
    tickers = list(
        session.scalars(
            select(WorkflowRunPortfolioTicker)
            .where(col(WorkflowRunPortfolioTicker.workflow_run_id) == workflow_run_id)
            .order_by(col(WorkflowRunPortfolioTicker.sort_order))
        )
    )
    header: WorkflowRunHeaderRow = {
        "id": wf.id,
        "started_at": wf.started_at,
        "completed_at": wf.completed_at,
        "status": wf.status.value,
        "is_mock": wf.is_mock,
        "error_message": wf.error_message,
        "portfolio_tickers": [t.ticker for t in tickers],
    }
    return header


def fetch_workflow_detail(
    session: Session, workflow_run_id: str
) -> WorkflowRunDetailRecord | None:
    wf = get_workflow_run_row(session, workflow_run_id)
    if wf is None:
        return None

    se = session.scalars(
        select(WorkflowAgentExecution).where(
            col(WorkflowAgentExecution.workflow_run_id) == workflow_run_id,
            col(WorkflowAgentExecution.agent_name) == AgentNameDb.SURVEYOR,
        )
    ).first()
    surveyor_execution: SurveyorExecutionRow | None = None
    if se is not None:
        surveyor_execution = {
            "id": se.id,
            "agent_name": se.agent_name.value,
            "status": se.status.value,
            "started_at": se.started_at,
            "completed_at": se.completed_at,
        }

    agent_order = {
        AgentNameDb.PROFILER.value: 0,
        AgentNameDb.RESEARCHER.value: 1,
        AgentNameDb.STRATEGIST.value: 2,
        AgentNameDb.SENTINEL.value: 3,
        AgentNameDb.APPRAISER.value: 4,
        AgentNameDb.ARBITER.value: 5,
    }

    runs = list(
        session.scalars(
            select(Run)
            .where(col(Run.workflow_run_id) == workflow_run_id)
            .order_by(col(Run.started_at))
        )
    )
    runs_out: list[TickerRunRow] = []
    for rr in runs:
        agents = list(
            session.scalars(
                select(AgentExecution).where(col(AgentExecution.run_id) == rr.id)
            )
        )
        agents_sorted = sorted(
            agents, key=lambda a: agent_order.get(a.agent_name.value, 99)
        )
        agent_rows: list[AgentExecutionRow] = [
            {
                "id": a.id,
                "agent_name": a.agent_name.value,
                "status": a.status.value,
                "started_at": a.started_at,
                "completed_at": a.completed_at,
            }
            for a in agents_sorted
        ]
        runs_out.append(
            {
                "id": rr.id,
                "ticker": rr.ticker,
                "company_name": rr.company_name,
                "entry_path": rr.entry_path.value,
                "status": rr.status.value,
                "final_rating": rr.final_rating,
                "decision_type": rr.decision_type.value if rr.decision_type else None,
                "agent_executions": agent_rows,
            }
        )

    detail: WorkflowRunDetailRecord = {
        **wf,
        "surveyor_execution": surveyor_execution,
        "runs": runs_out,
    }
    return detail


def delete_workflow_run_if_mock(session: Session, workflow_run_id: str) -> bool:
    wf = session.get(WorkflowRun, workflow_run_id)
    if wf is None or not wf.is_mock:
        return False
    session.delete(wf)
    session.commit()
    return True


def workflow_run_exists(session: Session, workflow_run_id: str) -> bool:
    return session.get(WorkflowRun, workflow_run_id) is not None


def get_latest_portfolio_tickers(session: Session) -> list[str] | None:
    workflow = session.scalars(
        select(WorkflowRun).order_by(desc(col(WorkflowRun.started_at)))
    ).first()
    if workflow is None:
        return None
    rows = list(
        session.scalars(
            select(WorkflowRunPortfolioTicker)
            .where(col(WorkflowRunPortfolioTicker.workflow_run_id) == workflow.id)
            .order_by(col(WorkflowRunPortfolioTicker.sort_order))
        )
    )
    return [r.ticker for r in rows]


def set_workflow_error(session: Session, workflow_run_id: str, message: str) -> None:
    wf = session.get(WorkflowRun, workflow_run_id)
    if wf is None:
        return
    wf.status = WorkflowRunStatusDb.FAILED
    wf.error_message = message
    wf.completed_at = utc_now()
    session.add(wf)
    session.commit()
