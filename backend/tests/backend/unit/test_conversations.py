"""Tests for dashboard conversation persistence."""

import json
from unittest.mock import patch

from pydantic_ai.messages import ModelRequest, ModelResponse, TextPart, UserPromptPart
from pydantic_ai.usage import RequestUsage
from sqlmodel import Session, col, select

from discount_analyst.adapters.persistence.crud.agent_output_persistence import (
    replace_research_report,
)
from discount_analyst.adapters.persistence.crud.candidate_snapshots import (
    candidate_to_snapshot,
)
from discount_analyst.adapters.persistence.crud.conversations import (
    assistant_response_for_run_agent,
    build_messages_json,
    insert_conversation_for_agent_execution,
    message_part_kind_from_raw,
    replace_conversation_messages,
)
from discount_analyst.adapters.persistence.crud.db_utils import utc_now
from discount_analyst.adapters.persistence.crud.workflow_runs import insert_workflow_run
from discount_analyst.adapters.simulation.mock_outputs import (
    mock_deep_research,
    mock_surveyor_candidate,
)
from discount_analyst.adapters.persistence.models import (
    AgentConversation,
    AgentExecution,
    AgentConversationMessage,
    AgentConversationMessagePart,
    AgentNameDb,
    EntryPathDb,
    ExecutionStatusDb,
    MessagePartKindDb,
    Run,
    WorkflowRunStatusDb,
)
from discount_analyst.domain.model_selection.model_name import ModelName


def test_message_part_kind_from_raw_treats_thinking_as_text() -> None:
    assert message_part_kind_from_raw("thinking") is MessagePartKindDb.TEXT


def test_replace_conversation_messages_persists_thinking_parts_as_text(
    db_session: Session,
) -> None:
    conversation = AgentConversation(
        id="conversation-1",
        agent_execution_id="agent-execution-1",
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
        agent_execution_id="agent-execution-1",
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
        agent_execution_id="agent-execution-1",
        system_prompt="System prompt",
    )
    db_session.add(conversation)
    db_session.commit()

    with patch(
        "discount_analyst.adapters.persistence.crud.conversations.logger.warning"
    ) as warning:
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


def test_replace_conversation_messages_persists_response_usage(
    db_session: Session,
) -> None:
    insert_workflow_run(
        db_session,
        workflow_run_id="workflow-usage",
        portfolio_tickers=["ABC.L"],
        is_mock=True,
    )
    execution = AgentExecution(
        id="surveyor-exec-usage",
        workflow_run_id="workflow-usage",
        agent_name=AgentNameDb.SURVEYOR,
        status=ExecutionStatusDb.COMPLETED,
        model_name=ModelName.GPT_5_6_LUNA,
    )
    conversation = AgentConversation(
        id="conversation-usage",
        agent_execution_id=execution.id,
        system_prompt="System prompt",
    )
    db_session.add(execution)
    db_session.add(conversation)
    db_session.commit()

    replace_conversation_messages(
        db_session,
        conversation_id=conversation.id,
        messages_payload=[
            {
                "kind": "request",
                "parts": [{"part_kind": "user-prompt", "content": "Analyse"}],
            },
            {
                "kind": "response",
                "parts": [{"part_kind": "text", "content": "Done"}],
                "usage": {
                    "input_tokens": 105_000,
                    "output_tokens": 20,
                    "cache_write_tokens": 0,
                    "cache_read_tokens": 1_000,
                },
            },
        ],
    )
    db_session.commit()

    stored = db_session.scalars(
        select(AgentConversationMessage).order_by(
            col(AgentConversationMessage.message_index)
        )
    ).all()
    assert stored[0].input_tokens is None
    assert stored[1].input_tokens == 105_000
    assert stored[1].output_tokens == 20
    assert stored[1].cache_read_tokens == 1_000
    assert stored[1].total_tokens == 105_020

    rebuilt = json.loads(
        build_messages_json(
            db_session, conversation.id, model_name=ModelName.GPT_5_6_LUNA
        )
    )
    assert "usage" not in rebuilt[0]
    assert rebuilt[1]["usage"] == {
        "input_tokens": 105_000,
        "output_tokens": 20,
        "cache_write_tokens": 0,
        "cache_read_tokens": 1_000,
        "total_tokens": 105_020,
        "context_window_tokens": 1_050_000,
        "context_window_used_pct": 10.0,
    }


def test_insert_conversation_persists_usage_from_model_messages(
    db_session: Session,
) -> None:
    insert_workflow_run(
        db_session,
        workflow_run_id="workflow-live-usage",
        portfolio_tickers=["ABC.L"],
        is_mock=True,
    )
    execution = AgentExecution(
        id="surveyor-exec-live-usage",
        workflow_run_id="workflow-live-usage",
        agent_name=AgentNameDb.SURVEYOR,
        status=ExecutionStatusDb.COMPLETED,
        model_name=ModelName.GPT_5_6_LUNA,
    )
    db_session.add(execution)
    db_session.commit()

    insert_conversation_for_agent_execution(
        db_session,
        conversation_id="conversation-live-usage",
        agent_execution_id=execution.id,
        system_prompt="System prompt",
        messages=[
            ModelRequest(parts=[UserPromptPart(content="Analyse")]),
            ModelResponse(
                parts=[TextPart(content="Done")],
                usage=RequestUsage(
                    input_tokens=105_000,
                    output_tokens=20,
                    cache_write_tokens=0,
                    cache_read_tokens=1_000,
                ),
            ),
        ],
    )
    db_session.commit()

    rebuilt = json.loads(
        build_messages_json(
            db_session,
            "conversation-live-usage",
            model_name=ModelName.GPT_5_6_LUNA,
        )
    )
    assert "usage" not in rebuilt[0]
    assert rebuilt[1]["usage"]["input_tokens"] == 105_000
    assert rebuilt[1]["usage"]["output_tokens"] == 20
    assert rebuilt[1]["usage"]["cache_read_tokens"] == 1_000
    assert rebuilt[1]["usage"]["total_tokens"] == 105_020
    assert rebuilt[1]["usage"]["context_window_used_pct"] == 10.0


def test_build_messages_json_omits_usage_when_tokens_were_never_stored(
    db_session: Session,
) -> None:
    conversation = AgentConversation(
        id="conversation-legacy",
        agent_execution_id="missing-execution",
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
                "parts": [{"part_kind": "text", "content": "Legacy"}],
            }
        ],
    )
    db_session.commit()

    rebuilt = json.loads(build_messages_json(db_session, conversation.id))
    assert rebuilt == [
        {
            "kind": "response",
            "parts": [{"part_kind": "text", "content": "Legacy"}],
        }
    ]
