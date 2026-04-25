"""Tests for dashboard conversation persistence."""

import json

from sqlmodel import Session, select

from backend.crud.conversations import (
    build_messages_json,
    message_part_kind_from_raw,
    replace_conversation_messages,
)
from backend.db.models import (
    AgentConversation,
    AgentConversationMessagePart,
    MessagePartKindDb,
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
