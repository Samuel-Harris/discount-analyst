"""Insert grouped mock workflow rows for local UI development and integration tests."""

from __future__ import annotations

from datetime import date

from sqlmodel import Session

from backend.dev import mock_outputs
from backend.crud import repository as repo
from discount_analyst.pipeline.builders import (
    build_sentinel_rejection,
    verdict_from_decision,
)


def seed(session: Session) -> None:
    """Populate one completed workflow with mixed profiler and surveyor lanes."""
    workflow_id = repo.new_id()
    surveyor_exec_id = repo.new_id()
    portfolio = ["SEED1.L", "SEED2.L"]

    repo.insert_workflow_run(
        session,
        workflow_run_id=workflow_id,
        portfolio_tickers=portfolio,
        is_mock=True,
    )
    repo.insert_surveyor_workflow_execution(
        session,
        execution_id=surveyor_exec_id,
        workflow_run_id=workflow_id,
    )

    surveyor_output = mock_outputs.mock_surveyor_output(extra_tickers=portfolio)
    repo.update_workflow_agent_execution(
        session,
        execution_id=surveyor_exec_id,
        status="completed",
        started_at=repo.utc_now_iso(),
        completed_at=repo.utc_now_iso(),
        output_json=surveyor_output.model_dump_json(),
    )
    repo.insert_conversation_for_workflow_agent(
        session,
        conversation_id=repo.new_id(),
        workflow_agent_execution_id=surveyor_exec_id,
        system_prompt="seed surveyor system",
        messages=[],
    )

    # Lane A: profiler entry with arbiter completion.
    run_a_id = repo.new_id()
    repo.insert_ticker_run_with_agents(
        session,
        run_id=run_a_id,
        workflow_run_id=workflow_id,
        ticker="SEED1.L",
        company_name="SEED1.L",
        entry_path="profiler",
        is_existing_position=False,
        is_mock=True,
        agent_names=repo.PROFILER_ENTRY_AGENT_NAMES,
    )
    profiler_exec_id = repo.get_agent_execution_id_by_run_and_agent(
        session, run_id=run_a_id, agent_name="profiler"
    )
    if profiler_exec_id is not None:
        profiler_output = mock_outputs.mock_profiler_output(ticker="SEED1.L")
        repo.update_agent_execution(
            session,
            execution_id=profiler_exec_id,
            status="completed",
            started_at=repo.utc_now_iso(),
            completed_at=repo.utc_now_iso(),
            output_json=profiler_output.model_dump_json(),
        )
        repo.insert_conversation_for_agent_execution(
            session,
            conversation_id=repo.new_id(),
            agent_execution_id=profiler_exec_id,
            system_prompt="seed profiler system",
            messages=[],
        )

    for agent_name in ("researcher", "strategist", "sentinel", "appraiser", "arbiter"):
        exec_id = repo.get_agent_execution_id_by_run_and_agent(
            session, run_id=run_a_id, agent_name=agent_name
        )
        if exec_id is None:
            continue
        repo.update_agent_execution(
            session,
            execution_id=exec_id,
            status="completed",
            started_at=repo.utc_now_iso(),
            completed_at=repo.utc_now_iso(),
        )

    candidate_a = mock_outputs.mock_surveyor_candidate(
        ticker="SEED1.L", company_name="Seed One plc"
    )
    arbiter_decision = mock_outputs.mock_arbiter_decision(
        candidate_a, is_existing_position=False
    )
    arbiter_verdict = verdict_from_decision(arbiter_decision)
    repo.update_ticker_run_completion(
        session,
        run_id=run_a_id,
        status="completed",
        final_rating=arbiter_verdict.rating.value,
        decision_type="arbiter",
        recommended_action=arbiter_verdict.recommended_action,
        final_verdict_json=arbiter_verdict.model_dump_json(),
        error_message=None,
    )

    # Lane B: surveyor entry with sentinel rejection path.
    candidate_b = mock_outputs.mock_surveyor_candidate(
        ticker="SEED2.L", company_name="Seed Two plc"
    )
    surveyor_snapshot_id = repo.get_workflow_candidate_snapshot_id(
        session, workflow_execution_id=surveyor_exec_id, ticker="SEED2.L"
    )
    run_b_id = repo.new_id()
    repo.insert_ticker_run_with_agents(
        session,
        run_id=run_b_id,
        workflow_run_id=workflow_id,
        ticker="SEED2.L",
        company_name="Seed Two plc",
        entry_path="surveyor",
        is_existing_position=False,
        is_mock=True,
        agent_names=repo.SURVEYOR_ENTRY_AGENT_NAMES,
        candidate_snapshot_id=surveyor_snapshot_id,
    )

    for agent_name, status in (
        ("researcher", "completed"),
        ("strategist", "completed"),
        ("sentinel", "completed"),
        ("appraiser", "skipped"),
        ("arbiter", "skipped"),
    ):
        exec_id = repo.get_agent_execution_id_by_run_and_agent(
            session, run_id=run_b_id, agent_name=agent_name
        )
        if exec_id is None:
            continue
        repo.update_agent_execution(
            session,
            execution_id=exec_id,
            status=status,
            started_at=repo.utc_now_iso(),
            completed_at=repo.utc_now_iso(),
        )

    thesis_b = mock_outputs.mock_thesis(candidate_b)
    evaluation_b = mock_outputs.mock_sentinel_evaluation(
        candidate=candidate_b, proceed=False
    )
    rejection_b = build_sentinel_rejection(
        evaluation=evaluation_b,
        thesis=thesis_b,
        is_existing_position=False,
        decision_date=date.today().isoformat(),
    )
    rejection_verdict = verdict_from_decision(rejection_b)
    repo.update_ticker_run_completion(
        session,
        run_id=run_b_id,
        status="completed",
        final_rating=rejection_verdict.rating.value,
        decision_type="sentinel_rejection",
        recommended_action=rejection_verdict.recommended_action,
        final_verdict_json=rejection_verdict.model_dump_json(),
        error_message=None,
    )

    repo.recompute_workflow_status(session, workflow_id)
