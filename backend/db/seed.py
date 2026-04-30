"""Insert grouped mock workflow rows for local UI development and integration tests."""

from __future__ import annotations

from datetime import date

from sqlmodel import Session

from backend.crud.conversations import (
    insert_conversation_for_agent_execution,
    insert_conversation_for_workflow_agent,
)
from backend.contracts.agent_lane_order import (
    PROFILER_ENTRY_AGENT_NAMES,
    SURVEYOR_ENTRY_AGENT_NAMES,
)
from backend.crud.db_utils import new_id, utc_now_iso
from backend.crud.run_executions import (
    get_agent_execution_id_by_run_and_agent,
    get_workflow_candidate_snapshot_id,
    insert_ticker_run_with_agents,
    update_agent_execution,
    update_ticker_run_completion,
    update_workflow_agent_execution,
)
from backend.crud.workflow_runs import (
    insert_surveyor_workflow_execution,
    insert_workflow_run,
    recompute_workflow_status,
)
from backend.dev import mock_conversation_messages, mock_outputs
from discount_analyst.pipeline.builders import (
    build_sentinel_rejection,
    verdict_from_decision,
)


def seed(session: Session) -> None:
    """Populate one completed workflow with mixed profiler and surveyor lanes."""
    workflow_id = new_id()
    surveyor_exec_id = new_id()
    portfolio = ["SEED1.L", "SEED2.L"]

    insert_workflow_run(
        session,
        workflow_run_id=workflow_id,
        portfolio_tickers=portfolio,
        is_mock=True,
    )
    insert_surveyor_workflow_execution(
        session,
        execution_id=surveyor_exec_id,
        workflow_run_id=workflow_id,
    )

    surveyor_output = mock_outputs.mock_surveyor_output(extra_tickers=portfolio)
    update_workflow_agent_execution(
        session,
        execution_id=surveyor_exec_id,
        status="completed",
        started_at=utc_now_iso(),
        completed_at=utc_now_iso(),
        output_json=surveyor_output.model_dump_json(),
    )
    insert_conversation_for_workflow_agent(
        session,
        conversation_id=new_id(),
        workflow_agent_execution_id=surveyor_exec_id,
        system_prompt="seed surveyor system",
        messages=None,
        messages_json=mock_conversation_messages.surveyor_messages_json(),
    )

    # Lane A: profiler entry with arbiter completion.
    run_a_id = new_id()
    insert_ticker_run_with_agents(
        session,
        run_id=run_a_id,
        workflow_run_id=workflow_id,
        ticker="SEED1.L",
        company_name="SEED1.L",
        entry_path="profiler",
        is_existing_position=True,
        is_mock=True,
        agent_names=PROFILER_ENTRY_AGENT_NAMES,
    )
    profiler_exec_id = get_agent_execution_id_by_run_and_agent(
        session, run_id=run_a_id, agent_name="profiler"
    )
    if profiler_exec_id is not None:
        profiler_output = mock_outputs.mock_profiler_output(ticker="SEED1.L")
        update_agent_execution(
            session,
            execution_id=profiler_exec_id,
            status="completed",
            started_at=utc_now_iso(),
            completed_at=utc_now_iso(),
            output_json=profiler_output.model_dump_json(),
        )
        insert_conversation_for_agent_execution(
            session,
            conversation_id=new_id(),
            agent_execution_id=profiler_exec_id,
            system_prompt="seed profiler system",
            messages=None,
            messages_json=mock_conversation_messages.profiler_messages_json(
                ticker="SEED1.L"
            ),
        )

    for agent_name in ("researcher", "strategist", "sentinel", "appraiser", "arbiter"):
        exec_id = get_agent_execution_id_by_run_and_agent(
            session, run_id=run_a_id, agent_name=agent_name
        )
        if exec_id is None:
            continue
        update_agent_execution(
            session,
            execution_id=exec_id,
            status="completed",
            started_at=utc_now_iso(),
            completed_at=utc_now_iso(),
        )

    candidate_a = mock_outputs.mock_surveyor_candidate(
        ticker="SEED1.L", company_name="Seed One plc"
    )
    arbiter_decision = mock_outputs.mock_arbiter_decision(
        candidate_a, is_existing_position=True
    )
    arbiter_verdict = verdict_from_decision(arbiter_decision)
    update_ticker_run_completion(
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
    surveyor_snapshot_id = get_workflow_candidate_snapshot_id(
        session, workflow_execution_id=surveyor_exec_id, ticker="SEED2.L"
    )
    run_b_id = new_id()
    insert_ticker_run_with_agents(
        session,
        run_id=run_b_id,
        workflow_run_id=workflow_id,
        ticker="SEED2.L",
        company_name="Seed Two plc",
        entry_path="surveyor",
        is_existing_position=False,
        is_mock=True,
        agent_names=SURVEYOR_ENTRY_AGENT_NAMES,
        candidate_snapshot_id=surveyor_snapshot_id,
    )

    for agent_name, status in (
        ("researcher", "completed"),
        ("strategist", "completed"),
        ("sentinel", "completed"),
        ("appraiser", "skipped"),
        ("arbiter", "skipped"),
    ):
        exec_id = get_agent_execution_id_by_run_and_agent(
            session, run_id=run_b_id, agent_name=agent_name
        )
        if exec_id is None:
            continue
        update_agent_execution(
            session,
            execution_id=exec_id,
            status=status,
            started_at=utc_now_iso(),
            completed_at=utc_now_iso(),
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
    update_ticker_run_completion(
        session,
        run_id=run_b_id,
        status="completed",
        final_rating=rejection_verdict.rating.value,
        decision_type="sentinel_rejection",
        recommended_action=rejection_verdict.recommended_action,
        final_verdict_json=rejection_verdict.model_dump_json(),
        error_message=None,
    )

    recompute_workflow_status(session, workflow_id)
    session.commit()
