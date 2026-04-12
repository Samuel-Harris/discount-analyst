"""Conversation payloads for workflow-level Surveyor and ticker-scoped agents."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from backend.common.primitive_types import AgentNameSlug
from backend.deps import DbSession
from backend.contracts.api import ConversationResponse
from backend.contracts.agents import is_known_agent_slug
from backend.crud.conversations import (
    get_conversation_for_run_agent,
    get_conversation_for_workflow_surveyor,
)

router = APIRouter(tags=["agents"])


@router.get("/workflow_runs/{workflow_run_id}/agents/surveyor/conversation")
def get_surveyor_conversation(
    workflow_run_id: str, session: DbSession
) -> ConversationResponse:
    row = get_conversation_for_workflow_surveyor(session, workflow_run_id)
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found"
        )
    return ConversationResponse(**row)


@router.get("/runs/{run_id}/agents/{agent_name}/conversation")
def get_run_agent_conversation(
    run_id: str, agent_name: AgentNameSlug, session: DbSession
) -> ConversationResponse:
    if not is_known_agent_slug(agent_name):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown agent name: {agent_name!r}",
        )
    row = get_conversation_for_run_agent(
        session, run_id=run_id, agent_name=agent_name.casefold()
    )
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found"
        )
    return ConversationResponse(**row)
