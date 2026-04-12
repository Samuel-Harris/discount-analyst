"""Conversation payloads for workflow-level Surveyor and ticker-scoped agents."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlmodel import Session

from backend.contracts.api import ConversationResponse
from backend.contracts.agents import slug_to_agent_name
from backend.crud.conversations import (
    get_conversation_for_run_agent,
    get_conversation_for_workflow_surveyor,
)

router = APIRouter(tags=["agents"])


def get_session(request: Request):
    session_factory = request.app.state.db_session_factory
    with session_factory() as session:
        yield session


DbSession = Annotated[Session, Depends(get_session)]


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
    run_id: str, agent_name: str, session: DbSession
) -> ConversationResponse:
    try:
        slug_to_agent_name(agent_name)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc
    row = get_conversation_for_run_agent(
        session, run_id=run_id, agent_name=agent_name.casefold()
    )
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found"
        )
    return ConversationResponse(**row)
