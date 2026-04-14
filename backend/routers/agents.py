"""Conversation payloads for workflow-level Surveyor and ticker-scoped agents."""

from __future__ import annotations

import logfire
from fastapi import APIRouter, HTTPException, status

from backend.deps import DbSession
from backend.contracts.api import ConversationResponse
from backend.contracts.enums import AgentNameSlug
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
    logfire.debug(
        "Fetched surveyor conversation",
        workflow_run_id=workflow_run_id,
        agent="surveyor",
    )
    return ConversationResponse(**row)


@router.get("/runs/{run_id}/agents/{agent_name}/conversation")
def get_run_agent_conversation(
    run_id: str, agent_name: AgentNameSlug, session: DbSession
) -> ConversationResponse:
    # Invalid slugs are rejected by FastAPI as 422 before this handler runs.
    row = get_conversation_for_run_agent(
        session, run_id=run_id, agent_name=agent_name.casefold()
    )
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found"
        )
    logfire.debug(
        "Fetched run agent conversation",
        run_id=run_id,
        agent_name=agent_name,
    )
    return ConversationResponse(**row)
