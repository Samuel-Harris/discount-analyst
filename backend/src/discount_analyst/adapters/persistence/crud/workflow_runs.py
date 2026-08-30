"""WorkflowRun-level queries and mutations (portfolio, status, list/detail)."""

from __future__ import annotations

from typing import Any

from sqlalchemy import case, desc, func
from sqlmodel import Session, col, select

from discount_analyst.adapters.persistence.workflow_rows import (
    AgentExecutionRow,
    CandidateGateRow,
    TickerRunRow,
    TickerRunResumeRow,
    WorkflowRunDetailRecord,
    WorkflowRunHeaderRow,
    WorkflowRunListRow,
)
from discount_analyst.adapters.persistence.crud.db_utils import (
    ACTIVE_EXECUTION_STATUSES,
    new_id,
    utc_now,
)
from discount_analyst.adapters.persistence.crud.run_executions import (
    workflow_can_retry_failed_agents,
)
from discount_analyst.application.workflows.workflow_status import (
    derive_workflow_status,
)
from discount_analyst.adapters.persistence.models import (
    AgentExecution,
    AgentNameDb,
    CandidateSnapshot,
    EntryPathDb,
    ExecutionStatusDb,
    Run,
    WorkflowRun,
    WorkflowRunPortfolioTicker,
    WorkflowRunStatusDb,
)

TERMINAL_WORKFLOW_STATUSES = frozenset(
    {
        WorkflowRunStatusDb.COMPLETED.value,
        WorkflowRunStatusDb.FAILED.value,
        WorkflowRunStatusDb.CANCELLED.value,
    }
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


def list_ticker_runs_for_workflow(
    session: Session, workflow_run_id: str
) -> list[TickerRunResumeRow]:
    rows = list(
        session.scalars(
            select(Run)
            .where(col(Run.workflow_run_id) == workflow_run_id)
            .order_by(col(Run.started_at))
        )
    )
    return [
        {
            "id": row.id,
            "ticker": row.ticker,
            "entry_path": row.entry_path.value,
            "status": row.status.value,
            "is_existing_position": row.is_existing_position,
        }
        for row in rows
    ]


def recompute_workflow_status(session: Session, workflow_run_id: str) -> None:
    wf = session.get(WorkflowRun, workflow_run_id)
    if wf is None:
        return
    if wf.status == WorkflowRunStatusDb.CANCELLED:
        return
    if wf.status == WorkflowRunStatusDb.FAILED and wf.error_message:
        return

    surveyor = _workflow_scoped_execution(
        session, workflow_run_id, AgentNameDb.SURVEYOR
    )
    allocator = _workflow_scoped_execution(
        session, workflow_run_id, AgentNameDb.ALLOCATOR
    )
    runs = list(
        session.scalars(select(Run).where(col(Run.workflow_run_id) == workflow_run_id))
    )

    derived = derive_workflow_status(
        surveyor_status=None if surveyor is None else surveyor.status.value,
        allocator_status=None if allocator is None else allocator.status.value,
        run_statuses=tuple(run.status.value for run in runs),
    )
    new_status = WorkflowRunStatusDb(derived)

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
    surveyor_execution_id: str | None = None,
    allocator_execution_id: str | None = None,
) -> tuple[str, str]:
    surveyor_id = surveyor_execution_id or new_id()
    allocator_id = allocator_execution_id or new_id()
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
    session.add(
        AgentExecution(
            id=surveyor_id,
            workflow_run_id=workflow_run_id,
            run_id=None,
            agent_name=AgentNameDb.SURVEYOR,
            status=ExecutionStatusDb.PENDING,
            started_at=None,
            completed_at=None,
            error_message=None,
        )
    )
    session.add(
        AgentExecution(
            id=allocator_id,
            workflow_run_id=workflow_run_id,
            run_id=None,
            agent_name=AgentNameDb.ALLOCATOR,
            status=ExecutionStatusDb.PENDING,
            started_at=None,
            completed_at=None,
            error_message=None,
        )
    )
    session.commit()
    return surveyor_id, allocator_id


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

    se = _workflow_scoped_execution(session, workflow_run_id, AgentNameDb.SURVEYOR)
    surveyor_execution: AgentExecutionRow | None = None
    if se is not None:
        surveyor_execution = _workflow_agent_execution_row(se)

    allocator = _workflow_scoped_execution(
        session, workflow_run_id, AgentNameDb.ALLOCATOR
    )
    allocator_execution: AgentExecutionRow | None = None
    if allocator is not None:
        allocator_execution = _workflow_agent_execution_row(allocator)

    agent_order = {
        AgentNameDb.PROFILER.value: 0,
        AgentNameDb.RESEARCHER.value: 1,
        AgentNameDb.STRATEGIST.value: 2,
        AgentNameDb.SENTINEL.value: 3,
        AgentNameDb.APPRAISER.value: 4,
    }

    runs = list(
        session.scalars(
            select(Run)
            .where(col(Run.workflow_run_id) == workflow_run_id)
            .order_by(col(Run.started_at))
        )
    )
    executions_by_run_id: dict[str, list[AgentExecution]] = {}
    runs_out: list[TickerRunRow] = []
    for run in runs:
        agents = list(
            session.scalars(
                select(AgentExecution).where(col(AgentExecution.run_id) == run.id)
            )
        )
        executions_by_run_id[run.id] = agents
        agents_sorted = sorted(
            agents, key=lambda a: agent_order.get(a.agent_name.value, 99)
        )
        agent_rows: list[AgentExecutionRow] = [
            {
                "id": agent.id,
                "agent_name": agent.agent_name.value,
                "status": agent.status.value,
                "started_at": agent.started_at,
                "completed_at": agent.completed_at,
                "model_name": agent.model_name,
            }
            for agent in agents_sorted
        ]
        candidate_gate: CandidateGateRow | None = None
        if run.candidate_snapshot_id is not None:
            snapshot = session.get(CandidateSnapshot, run.candidate_snapshot_id)
            if snapshot is not None:
                candidate_gate = {
                    "gate_status": snapshot.gate_status,
                    "source_ticker": snapshot.ticker,
                    "resolved_ticker": snapshot.resolved_ticker,
                    "gate_failure_reason": snapshot.gate_failure_reason,
                    "is_actively_trading": snapshot.is_actively_trading,
                }
        runs_out.append(
            {
                "id": run.id,
                "ticker": run.ticker,
                "company_name": run.company_name,
                "entry_path": run.entry_path.value,
                "status": run.status.value,
                "final_rating": run.final_rating,
                "decision_type": run.decision_type.value if run.decision_type else None,
                "candidate_gate": candidate_gate,
                "agent_executions": agent_rows,
            }
        )

    detail: WorkflowRunDetailRecord = {
        **wf,
        "can_retry_failed_agents": workflow_can_retry_failed_agents(
            workflow_status=WorkflowRunStatusDb(wf["status"]),
            surveyor=se,
            allocator=allocator,
            runs=runs,
            executions_by_run_id=executions_by_run_id,
        ),
        "surveyor_execution": surveyor_execution,
        "allocator_execution": allocator_execution,
        "runs": runs_out,
    }
    return detail


def _workflow_scoped_execution(
    session: Session, workflow_run_id: str, agent_name: AgentNameDb
) -> AgentExecution | None:
    return session.scalars(
        select(AgentExecution).where(
            col(AgentExecution.workflow_run_id) == workflow_run_id,
            col(AgentExecution.agent_name) == agent_name,
        )
    ).first()


def _workflow_agent_execution_row(execution: AgentExecution) -> AgentExecutionRow:
    return {
        "id": execution.id,
        "agent_name": execution.agent_name.value,
        "status": execution.status.value,
        "started_at": execution.started_at,
        "completed_at": execution.completed_at,
        "model_name": execution.model_name,
    }


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
    if wf.status == WorkflowRunStatusDb.CANCELLED:
        return
    wf.status = WorkflowRunStatusDb.FAILED
    wf.error_message = message
    wf.completed_at = utc_now()
    session.add(wf)
    session.commit()


def _cancel_unfinished_child_rows(
    session: Session, workflow_run_id: str, *, completed_at: Any
) -> None:
    workflow_scoped_executions = list(
        session.scalars(
            select(AgentExecution).where(
                col(AgentExecution.workflow_run_id) == workflow_run_id
            )
        )
    )
    for execution in workflow_scoped_executions:
        if execution.status.value not in ACTIVE_EXECUTION_STATUSES:
            continue
        execution.status = ExecutionStatusDb.CANCELLED
        execution.completed_at = completed_at
        session.add(execution)

    runs = list(
        session.scalars(select(Run).where(col(Run.workflow_run_id) == workflow_run_id))
    )
    for run in runs:
        if run.status.value != WorkflowRunStatusDb.RUNNING.value:
            continue
        run.status = WorkflowRunStatusDb.CANCELLED
        run.completed_at = completed_at
        session.add(run)

    lane_executions = list(
        session.scalars(
            select(AgentExecution)
            .join(Run, col(AgentExecution.run_id) == col(Run.id))
            .where(col(Run.workflow_run_id) == workflow_run_id)
        )
    )
    for execution in lane_executions:
        if execution.status.value not in ACTIVE_EXECUTION_STATUSES:
            continue
        execution.status = ExecutionStatusDb.CANCELLED
        execution.completed_at = completed_at
        session.add(execution)


def cancel_unfinished_workflow_children(session: Session, workflow_run_id: str) -> None:
    if session.get(WorkflowRun, workflow_run_id) is None:
        return
    _cancel_unfinished_child_rows(session, workflow_run_id, completed_at=utc_now())
    session.commit()


def cancel_workflow_run(session: Session, workflow_run_id: str) -> bool:
    wf = session.get(WorkflowRun, workflow_run_id)
    if wf is None:
        return False
    if wf.status.value in TERMINAL_WORKFLOW_STATUSES:
        return True

    completed_at = utc_now()
    _cancel_unfinished_child_rows(session, workflow_run_id, completed_at=completed_at)
    wf.status = WorkflowRunStatusDb.CANCELLED
    wf.completed_at = completed_at
    wf.error_message = None
    session.add(wf)
    session.commit()
    return True
