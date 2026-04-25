"""Tests for dashboard conversation persistence."""

import json
from unittest.mock import patch

from sqlmodel import Session, select

from backend.crud.agent_output_persistence import replace_research_report
from backend.crud.candidate_snapshots import candidate_to_snapshot
from backend.crud.conversations import (
    assistant_response_for_run_agent,
    build_messages_json,
    message_part_kind_from_raw,
    replace_conversation_messages,
)
from backend.crud.db_utils import utc_now
from backend.crud.workflow_runs import insert_workflow_run
from backend.dev.mock_outputs import mock_deep_research, mock_surveyor_candidate
from backend.db.models import (
    AgentConversation,
    AgentExecution,
    AgentConversationMessagePart,
    AgentNameDb,
    EntryPathDb,
    ExecutionStatusDb,
    MessagePartKindDb,
    Run,
    WorkflowRunStatusDb,
)


def test_message_part_kind_from_raw_treats_thinking_as_text() -> None:
    assert message_part_kind_from_raw("thinking") is MessagePartKindDb.TEXT


def test_replace_conversation_messages_persists_thinking_parts_as_text(
    db_session: Session,
) -> None:
    conversation = AgentConversation(
        id="conversation-1",
        workflow_agent_execution_id="workflow-agent-execution-1",
        agent_execution_id=None,
        system_prompt="System prompt",
    )
    db_session.add(conversation)
    db_session.commit()

    replace_conversation_messages(
        db_session,
        conversation_id=conversation.id,
        messages_payload=[
            {
                "kind": "response",
                "parts": [
                    {
                        "part_kind": "thinking",
                        "content": "Private reasoning summary",
                    }
                ],
            }
        ],
    )
    db_session.commit()

    part = db_session.scalars(select(AgentConversationMessagePart)).one()
    assert part.part_kind is MessagePartKindDb.TEXT
    assert part.content_text == "Private reasoning summary"

    rebuilt = json.loads(build_messages_json(db_session, conversation.id))
    assert rebuilt == [
        {
            "kind": "response",
            "parts": [
                {
                    "part_kind": "text",
                    "content": "Private reasoning summary",
                }
            ],
        }
    ]


def test_replace_conversation_messages_persists_builtin_tool_call(
    db_session: Session,
) -> None:
    conversation = AgentConversation(
        id="conversation-1",
        workflow_agent_execution_id="workflow-agent-execution-1",
        agent_execution_id=None,
        system_prompt="System prompt",
    )
    db_session.add(conversation)
    db_session.commit()

    replace_conversation_messages(
        db_session,
        conversation_id=conversation.id,
        messages_payload=[
            {
                "kind": "response",
                "parts": [
                    {
                        "part_kind": "builtin-tool-call",
                        "tool_name": "web_search",
                        "tool_call_id": "call-1",
                        "args": {"query": "example"},
                    }
                ],
            }
        ],
    )
    db_session.commit()

    part = db_session.scalars(select(AgentConversationMessagePart)).one()
    assert part.part_kind is MessagePartKindDb.TOOL_CALL
    assert part.tool_name == "web_search"
    assert part.tool_call_id == "call-1"
    assert json.loads(part.content_text or "{}") == {"query": "example"}

    rebuilt = json.loads(build_messages_json(db_session, conversation.id))
    assert rebuilt == [
        {
            "kind": "response",
            "parts": [
                {
                    "part_kind": "tool-call",
                    "tool_name": "web_search",
                    "tool_call_id": "call-1",
                    "args": part.content_text,
                }
            ],
        }
    ]


def test_replace_conversation_messages_warns_and_persists_unknown_part_kind(
    db_session: Session,
) -> None:
    conversation = AgentConversation(
        id="conversation-1",
        workflow_agent_execution_id="workflow-agent-execution-1",
        agent_execution_id=None,
        system_prompt="System prompt",
    )
    db_session.add(conversation)
    db_session.commit()

    with patch("backend.crud.conversations.logger.warning") as warning:
        replace_conversation_messages(
            db_session,
            conversation_id=conversation.id,
            messages_payload=[
                {
                    "kind": "response",
                    "parts": [
                        {
                            "part_kind": "future-provider-part",
                            "content": {"nested": True},
                            "tool_name": "future_tool",
                        }
                    ],
                }
            ],
        )
    db_session.commit()

    part = db_session.scalars(select(AgentConversationMessagePart)).one()
    assert part.part_kind is MessagePartKindDb.UNKNOWN
    assert json.loads(part.content_text or "{}") == {
        "part_kind": "future-provider-part",
        "content": {"nested": True},
        "tool_name": "future_tool",
    }
    assert part.tool_name == "future_tool"

    warning.assert_called_once()
    assert warning.call_args.args == (
        "Persisting unknown pydantic-ai message part kind",
    )
    assert warning.call_args.kwargs["extra"]["raw_part_kind"] == "future-provider-part"
    assert warning.call_args.kwargs["extra"]["conversation_id"] == conversation.id


def test_research_report_without_candidate_persists_and_rehydrates(
    db_session: Session,
) -> None:
    workflow_run_id = "workflow-1"
    run_id = "run-1"
    execution_id = "researcher-exec-1"
    candidate = mock_surveyor_candidate(ticker="ABC.L", company_name="ABC plc")
    report = mock_deep_research(candidate)

    insert_workflow_run(
        db_session,
        workflow_run_id=workflow_run_id,
        portfolio_tickers=["ABC.L"],
        is_mock=True,
    )
    snapshot = candidate_to_snapshot(
        candidate=candidate,
        sort_order=0,
        workflow_agent_execution_id=None,
        agent_execution_id=execution_id,
    )
    db_session.add(snapshot)
    db_session.add(
        Run(
            id=run_id,
            workflow_run_id=workflow_run_id,
            candidate_snapshot_id=snapshot.id,
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
    execution = AgentExecution(
        id=execution_id,
        run_id=run_id,
        agent_name=AgentNameDb.RESEARCHER,
        status=ExecutionStatusDb.RUNNING,
        started_at=utc_now(),
        completed_at=None,
        error_message=None,
    )
    db_session.add(execution)
    db_session.commit()

    raw_report = json.loads(report.model_dump_json())
    assert "candidate" not in raw_report

    replace_research_report(db_session, execution, report.model_dump_json())
    db_session.commit()

    rehydrated = json.loads(assistant_response_for_run_agent(db_session, execution))
    assert "candidate" not in rehydrated
    assert rehydrated["executive_overview"] == report.executive_overview
    assert rehydrated["data_gaps_update"]["original_data_gaps"] == candidate.data_gaps
