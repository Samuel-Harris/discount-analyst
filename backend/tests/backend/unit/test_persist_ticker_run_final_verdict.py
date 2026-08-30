"""Tests for ``persist_ticker_run_final_verdict`` data-quality rejection lookup."""

from sqlmodel import Session, col, select

from discount_analyst.adapters.persistence.crud.db_utils import new_id
from discount_analyst.adapters.persistence.crud.run_executions import (
    get_agent_execution_id_by_run_and_agent,
    insert_ticker_run_with_agents,
    persist_ticker_run_final_verdict,
)
from discount_analyst.adapters.persistence.crud.workflow_runs import (
    insert_workflow_run,
)
from discount_analyst.adapters.persistence.models import (
    AgentExecution,
    RunFinalDecision,
)
from discount_analyst.adapters.simulation.mock_outputs import mock_surveyor_candidate
from discount_analyst.application.decisions.builders import (
    build_data_quality_rejection,
    verdict_from_decision,
)
from discount_analyst.application.workflows.agent_lane_order import (
    PROFILER_ENTRY_AGENT_NAMES,
    SURVEYOR_ENTRY_AGENT_NAMES,
)


def _dqr_verdict_json(*, ticker: str) -> str:
    candidate = mock_surveyor_candidate(ticker=ticker)
    rejection = build_data_quality_rejection(
        candidate.to_lane_context(),
        gate_failure_reason="No confident FMP symbol match.",
        is_existing_position=False,
        decision_date="2026-08-16",
    )
    return verdict_from_decision(rejection).model_dump_json()


def _final_decision(session: Session, run_id: str) -> RunFinalDecision | None:
    return session.scalars(
        select(RunFinalDecision).where(col(RunFinalDecision.run_id) == run_id)
    ).first()


def test_persist_dqr_uses_profiler_execution_not_researcher(
    db_session: Session,
) -> None:
    workflow_run_id = new_id()
    run_id = new_id()
    insert_workflow_run(
        db_session,
        workflow_run_id=workflow_run_id,
        portfolio_tickers=["BOWL.L"],
        is_mock=True,
    )
    insert_ticker_run_with_agents(
        db_session,
        run_id=run_id,
        workflow_run_id=workflow_run_id,
        ticker="BOWL.L",
        company_name="Hollywood Bowl Group plc",
        entry_path="profiler",
        is_existing_position=True,
        is_mock=True,
        agent_names=PROFILER_ENTRY_AGENT_NAMES,
    )
    db_session.commit()

    profiler_id = get_agent_execution_id_by_run_and_agent(
        db_session, run_id=run_id, agent_name="profiler"
    )
    researcher_id = get_agent_execution_id_by_run_and_agent(
        db_session, run_id=run_id, agent_name="researcher"
    )
    assert profiler_id is not None
    assert researcher_id is not None

    persist_ticker_run_final_verdict(
        db_session,
        run_id=run_id,
        final_verdict_json=_dqr_verdict_json(ticker="BOWL.L"),
        decision_type="data_quality_rejection",
    )
    db_session.commit()

    row = _final_decision(db_session, run_id)
    assert row is not None
    assert row.decision_type.value == "data_quality_rejection"
    assert row.source_agent_execution_id == profiler_id
    assert row.source_agent_execution_id != researcher_id


def test_persist_dqr_uses_workflow_surveyor_when_no_profiler(
    db_session: Session,
) -> None:
    workflow_run_id = new_id()
    surveyor_execution_id = new_id()
    run_id = new_id()
    insert_workflow_run(
        db_session,
        workflow_run_id=workflow_run_id,
        portfolio_tickers=["CGS.L"],
        is_mock=True,
        surveyor_execution_id=surveyor_execution_id,
    )
    insert_ticker_run_with_agents(
        db_session,
        run_id=run_id,
        workflow_run_id=workflow_run_id,
        ticker="CGS.L",
        company_name="Castings",
        entry_path="surveyor",
        is_existing_position=False,
        is_mock=True,
        agent_names=SURVEYOR_ENTRY_AGENT_NAMES,
    )
    db_session.commit()

    researcher_id = get_agent_execution_id_by_run_and_agent(
        db_session, run_id=run_id, agent_name="researcher"
    )
    assert researcher_id is not None

    persist_ticker_run_final_verdict(
        db_session,
        run_id=run_id,
        final_verdict_json=_dqr_verdict_json(ticker="CGS.L"),
        decision_type="data_quality_rejection",
    )
    db_session.commit()

    row = _final_decision(db_session, run_id)
    assert row is not None
    assert row.decision_type.value == "data_quality_rejection"
    assert row.source_agent_execution_id == surveyor_execution_id
    assert row.source_agent_execution_id != researcher_id


def test_persist_dqr_skips_upsert_when_workflow_surveyor_is_absent(
    db_session: Session,
) -> None:
    workflow_run_id = new_id()
    surveyor_id, _allocator_id = insert_workflow_run(
        db_session,
        workflow_run_id=workflow_run_id,
        portfolio_tickers=["KEYS.L"],
        is_mock=True,
    )
    run_id = new_id()
    insert_ticker_run_with_agents(
        db_session,
        run_id=run_id,
        workflow_run_id=workflow_run_id,
        ticker="KEYS.L",
        company_name="Keystone Law",
        entry_path="surveyor",
        is_existing_position=False,
        is_mock=True,
        agent_names=SURVEYOR_ENTRY_AGENT_NAMES,
    )
    surveyor = db_session.get(AgentExecution, surveyor_id)
    assert surveyor is not None
    db_session.delete(surveyor)
    db_session.commit()

    persist_ticker_run_final_verdict(
        db_session,
        run_id=run_id,
        final_verdict_json=_dqr_verdict_json(ticker="KEYS.L"),
        decision_type="data_quality_rejection",
    )
    db_session.commit()

    assert _final_decision(db_session, run_id) is None
