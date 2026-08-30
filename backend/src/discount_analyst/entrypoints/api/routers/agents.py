"""Conversation payloads for workflow-level and ticker-scoped agents."""

from __future__ import annotations

import logfire
from fastapi import APIRouter, HTTPException, status

from discount_analyst.adapters.persistence.crud.conversations import (
    get_conversation_for_run_agent,
    get_conversation_for_workflow_agent,
)
from discount_analyst.adapters.persistence.models import AgentNameDb
from discount_analyst.entrypoints.api.contracts.api import ConversationResponse
from discount_analyst.entrypoints.api.contracts.enums import (
    AgentNameSlug,
    WorkflowScopedAgentNameSlug,
)
from discount_analyst.entrypoints.api.deps import DbSession

router = APIRouter(tags=["agents"])


@router.get(
    "/workflow_runs/{workflow_run_id}/agents/{workflow_agent_name}/conversation"
)
def get_workflow_agent_conversation(
    workflow_run_id: str,
    workflow_agent_name: WorkflowScopedAgentNameSlug,
    session: DbSession,
) -> ConversationResponse:
    row = get_conversation_for_workflow_agent(
        session,
        workflow_run_id,
        agent_name=AgentNameDb(workflow_agent_name.value),
    )
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found"
        )
    logfire.debug(
        "Fetched workflow agent conversation",
        workflow_run_id=workflow_run_id,
        agent=workflow_agent_name.value,
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
