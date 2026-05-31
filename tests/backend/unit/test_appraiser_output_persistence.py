"""Tests for Appraiser structured output persistence."""

from sqlmodel import Session, select

from backend.crud.db_utils import utc_now
from backend.crud.run_executions import complete_agent_execution_with_conversation
from backend.crud.workflow_runs import insert_workflow_run
from backend.dev.mock_outputs import mock_appraiser_output, mock_surveyor_candidate
from backend.db.models import (
    AgentExecution,
    AgentNameDb,
    AppraiserReport,
    EntryPathDb,
    ExecutionStatusDb,
    Run,
    ValuationDistribution,
    WorkflowRunStatusDb,
)


def test_complete_appraiser_execution_persists_report_and_distribution(
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
    distribution = db_session.scalars(select(ValuationDistribution)).one()
    assert report.agent_execution_id == execution_id
    assert distribution.run_id == run_id
    assert distribution.appraiser_agent_execution_id == execution_id
    assert (
        report.expected_intrinsic_value
        == output.valuation_distribution.expected_intrinsic_value
    )
    assert (
        distribution.expected_intrinsic_value
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
    distributions = db_session.scalars(select(ValuationDistribution)).all()
    assert len(reports) == 1
    assert len(distributions) == 1
    assert reports[0].summary == "Updated Appraiser distribution."
    assert distributions[0].expected_intrinsic_value == 4.2
