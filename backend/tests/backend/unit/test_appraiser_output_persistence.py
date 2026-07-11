"""Tests for Appraiser structured output persistence."""

from sqlmodel import Session, select

from discount_analyst.adapters.persistence.crud.db_utils import utc_now
from discount_analyst.adapters.persistence.crud.run_executions import (
    complete_agent_execution_with_conversation,
    get_appraiser_report_for_run,
)
from discount_analyst.adapters.persistence.crud.workflow_runs import insert_workflow_run
from discount_analyst.adapters.simulation.mock_outputs import (
    mock_appraiser_output,
    mock_surveyor_candidate,
)
from discount_analyst.adapters.persistence.models import (
    AgentExecution,
    AgentNameDb,
    AppraiserReport,
    EntryPathDb,
    ExecutionStatusDb,
    Run,
    WorkflowRunStatusDb,
)


def test_complete_appraiser_execution_persists_single_report(
    db_session: Session,
) -> None:
    workflow_run_id = "workflow-1"
    run_id = "run-1"
    execution_id = "appraiser-exec-1"
    candidate = mock_surveyor_candidate(ticker="ABC.L", company_name="ABC plc")
    output = mock_appraiser_output(candidate)

    insert_workflow_run(
        db_session,
        workflow_run_id=workflow_run_id,
        portfolio_tickers=["ABC.L"],
        is_mock=True,
    )
    db_session.add(
        Run(
            id=run_id,
            workflow_run_id=workflow_run_id,
            candidate_snapshot_id=None,
            ticker=candidate.ticker,
            company_name=candidate.company_name,
            started_at=utc_now(),
            completed_at=None,
            entry_path=EntryPathDb.PROFILER,
            is_existing_position=True,
            status=WorkflowRunStatusDb.RUNNING,
            is_mock=True,
            error_message=None,
            final_rating=None,
            decision_type=None,
            recommended_action=None,
        )
    )
    db_session.add(
        AgentExecution(
            id=execution_id,
            run_id=run_id,
            agent_name=AgentNameDb.APPRAISER,
            status=ExecutionStatusDb.RUNNING,
            started_at=utc_now(),
            completed_at=None,
            error_message=None,
        )
    )
    db_session.commit()

    complete_agent_execution_with_conversation(
        db_session,
        execution_id=execution_id,
        conversation_id="conversation-1",
        system_prompt="System prompt",
        output_json=output.model_dump_json(),
        completed_at=utc_now().isoformat(),
    )
    db_session.commit()

    report = db_session.scalars(select(AppraiserReport)).one()
    assert report.agent_execution_id == execution_id
    assert (
        report.expected_intrinsic_value
        == output.valuation_distribution.expected_intrinsic_value
    )

    updated_distribution = output.valuation_distribution.model_copy(
        update={"expected_intrinsic_value": 4.2}
    )
    updated_output = output.model_copy(
        update={
            "summary": "Updated Appraiser distribution.",
            "valuation_distribution": updated_distribution,
        },
    )
    complete_agent_execution_with_conversation(
        db_session,
        execution_id=execution_id,
        conversation_id="conversation-2",
        system_prompt="System prompt",
        output_json=updated_output.model_dump_json(),
        completed_at=utc_now().isoformat(),
    )
    db_session.commit()

    reports = db_session.scalars(select(AppraiserReport)).all()
    assert len(reports) == 1
    assert reports[0].summary == "Updated Appraiser distribution."
    assert reports[0].expected_intrinsic_value == 4.2


def test_get_appraiser_report_for_run_joins_appraiser_execution(
    db_session: Session,
) -> None:
    workflow_run_id = "workflow-2"
    run_id = "run-2"
    appraiser_execution_id = "appraiser-exec-2"
    researcher_execution_id = "researcher-exec-2"
    candidate = mock_surveyor_candidate(ticker="XYZ.L", company_name="XYZ plc")
    output = mock_appraiser_output(candidate)

    insert_workflow_run(
        db_session,
        workflow_run_id=workflow_run_id,
        portfolio_tickers=["XYZ.L"],
        is_mock=True,
    )
    db_session.add(
        Run(
            id=run_id,
            workflow_run_id=workflow_run_id,
            candidate_snapshot_id=None,
            ticker=candidate.ticker,
            company_name=candidate.company_name,
            started_at=utc_now(),
            completed_at=None,
            entry_path=EntryPathDb.PROFILER,
            is_existing_position=False,
            status=WorkflowRunStatusDb.RUNNING,
            is_mock=True,
            error_message=None,
            final_rating=None,
            decision_type=None,
            recommended_action=None,
        )
    )
    for exec_id, agent in (
        (researcher_execution_id, AgentNameDb.RESEARCHER),
        (appraiser_execution_id, AgentNameDb.APPRAISER),
    ):
        db_session.add(
            AgentExecution(
                id=exec_id,
                run_id=run_id,
                agent_name=agent,
                status=ExecutionStatusDb.COMPLETED,
                started_at=utc_now(),
                completed_at=utc_now(),
                error_message=None,
            )
        )
    db_session.commit()

    complete_agent_execution_with_conversation(
        db_session,
        execution_id=appraiser_execution_id,
        conversation_id="conversation-appraiser",
        system_prompt="System prompt",
        output_json=output.model_dump_json(),
        completed_at=utc_now().isoformat(),
    )
    db_session.commit()

    report = get_appraiser_report_for_run(db_session, run_id=run_id)
    assert report is not None
    assert report.agent_execution_id == appraiser_execution_id
    assert report.ticker == candidate.ticker
