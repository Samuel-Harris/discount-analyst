"""Workflow-level Allocator: size the book after every ticker lane is terminal."""

from __future__ import annotations

import asyncio
from datetime import date
from typing import TYPE_CHECKING, Any, Protocol

from sqlmodel import Session

from discount_analyst.adapters.orchestration.llm_config import (
    PipelineLlmConfig,
    pipeline_llm_config,
)
from discount_analyst.adapters.persistence.crud.allocation_lane_bundles import (
    load_completed_lane_bundles,
)
from discount_analyst.adapters.persistence.crud.db_utils import new_id, utc_now_iso
from discount_analyst.adapters.persistence.crud.portfolio_allocations import (
    persist_portfolio_allocation,
)
from discount_analyst.adapters.persistence.crud.run_executions import (
    complete_agent_execution_with_conversation,
    get_workflow_allocator_execution,
    update_agent_execution,
)
from discount_analyst.adapters.persistence.crud.workflow_runs import (
    list_ticker_runs_for_workflow,
)
from discount_analyst.adapters.persistence.models import (
    AgentNameDb,
    ExecutionStatusDb,
    WorkflowRunStatusDb,
)
from discount_analyst.adapters.simulation import (
    mock_conversation_messages,
    mock_outputs,
)
from discount_analyst.adapters.simulation.equal_weight_snapshot import (
    equal_weight_existing_snapshot,
)
from discount_analyst.agents.allocator.allocator import create_allocator_agent
from discount_analyst.agents.allocator.schema import AllocatorInput, AllocatorProposal
from discount_analyst.agents.allocator.system_prompt import (
    SYSTEM_PROMPT as ALLOCATOR_SYSTEM_PROMPT,
)
from discount_analyst.agents.allocator.user_prompt import create_user_prompt
from discount_analyst.agents.common_prompts.current_date import with_current_date
from discount_analyst.agents.runtime.ai_logging import AI_LOGFIRE
from discount_analyst.agents.runtime.streamed_agent_run import run_streamed_agent
from discount_analyst.application.allocations.assemble import (
    assemble_allocator_input,
    source_run_ids_by_ticker,
)
from discount_analyst.application.allocations.finalise import (
    finalise_allocator_proposal,
)
from discount_analyst.application.allocations.skip_reasons import (
    LANES_NOT_ALL_COMPLETED,
)
from discount_analyst.application.workflows.agent_errors import (
    extract_agent_error_message,
)
from discount_analyst.domain.allocations.allocation import (
    PortfolioAllocation as DomainPortfolioAllocation,
)
from discount_analyst.domain.allocations.snapshot import CurrentPortfolioSnapshot

if TYPE_CHECKING:
    from discount_analyst.config.settings import Settings


class AllocatorStageHost(Protocol):
    @property
    def settings(self) -> Settings: ...

    async def db(self, fn: Any, *args: Any, **kwargs: Any) -> Any: ...

    async def recompute(self, workflow_run_id: str) -> None: ...


class AllocatorStage:
    """Runs the workflow-level Allocator after every ticker lane is terminal."""

    async def run(
        self,
        host: AllocatorStageHost,
        *,
        workflow_run_id: str,
        is_mock: bool,
    ) -> None:
        execution = await host.db(_allocator_execution_id_and_status, workflow_run_id)
        if execution is None:
            AI_LOGFIRE.debug(
                "No allocator execution for workflow; skipping allocator branch",
                workflow_run_id=workflow_run_id,
            )
            return
        execution_id, status = execution
        if status == ExecutionStatusDb.COMPLETED.value:
            AI_LOGFIRE.info(
                "Allocator branch already completed; skipping",
                agent_name=AgentNameDb.ALLOCATOR,
                workflow_run_id=workflow_run_id,
            )
            return
        if status == ExecutionStatusDb.SKIPPED.value:
            AI_LOGFIRE.info(
                "Allocator branch already skipped; leaving skip in place",
                agent_name=AgentNameDb.ALLOCATOR,
                workflow_run_id=workflow_run_id,
            )
            return

        ticker_runs = await host.db(list_ticker_runs_for_workflow, workflow_run_id)
        if any(
            run["status"] != WorkflowRunStatusDb.COMPLETED.value for run in ticker_runs
        ):
            AI_LOGFIRE.info(
                "Allocator skipped because a ticker lane is not completed",
                agent_name=AgentNameDb.ALLOCATOR,
                workflow_run_id=workflow_run_id,
            )
            await host.db(
                update_agent_execution,
                execution_id=execution_id,
                status="skipped",
                error_message=LANES_NOT_ALL_COMPLETED,
                completed_at=utc_now_iso(),
            )
            await host.recompute(workflow_run_id)
            return

        try:
            llm = pipeline_llm_config(host.settings, is_mock=is_mock)
            AI_LOGFIRE.info(
                "Allocator branch started",
                agent_name=AgentNameDb.ALLOCATOR,
                workflow_run_id=workflow_run_id,
                is_mock=is_mock,
            )
            await host.db(
                update_agent_execution,
                execution_id=execution_id,
                status="running",
                started_at=utc_now_iso(),
                model_name=llm.model_name,
            )
            await host.recompute(workflow_run_id)

            snapshot = await host.db(
                load_dashboard_portfolio_snapshot,
                workflow_run_id,
                is_mock,
            )
            if snapshot is None:
                raise RuntimeError("Current portfolio snapshot is missing.")

            bundles = await host.db(load_completed_lane_bundles, workflow_run_id)
            allocator_input = assemble_allocator_input(bundles, snapshot, date.today())
            agent_result = await self._run_allocator_agent(
                allocator_input=allocator_input,
                is_mock=is_mock,
                llm=llm,
            )
            allocation = finalise_allocator_proposal(
                agent_result.proposal,
                allocator_input,
                source_run_ids_by_ticker(bundles),
            )
            await host.db(
                persist_completed_allocator_execution,
                execution_id=execution_id,
                system_prompt=with_current_date(ALLOCATOR_SYSTEM_PROMPT),
                messages=agent_result.messages,
                messages_json=agent_result.messages_json,
                allocation=allocation,
            )
            AI_LOGFIRE.info(
                "Allocator branch completed",
                agent_name=AgentNameDb.ALLOCATOR,
                workflow_run_id=workflow_run_id,
                position_count=len(allocation.positions),
            )
        except Exception as exc:  # noqa: BLE001
            error_msg = extract_agent_error_message(exc)
            AI_LOGFIRE.exception(
                "Allocator branch failed",
                agent_name=AgentNameDb.ALLOCATOR,
                workflow_run_id=workflow_run_id,
                allocator_execution_id=execution_id,
                error_message=error_msg,
            )
            await host.db(
                update_agent_execution,
                execution_id=execution_id,
                status="failed",
                error_message=error_msg,
                completed_at=utc_now_iso(),
            )
            raise
        finally:
            await host.recompute(workflow_run_id)

    async def _run_allocator_agent(
        self,
        *,
        allocator_input: AllocatorInput,
        is_mock: bool,
        llm: PipelineLlmConfig,
    ) -> _AllocatorRunResult:
        if is_mock:
            await asyncio.sleep(5)
            return _AllocatorRunResult(
                proposal=mock_outputs.mock_allocator_proposal(allocator_input),
                messages=None,
                messages_json=mock_conversation_messages.allocator_messages_json(),
            )

        ai_cfg = llm.ai_models_config
        if ai_cfg is None:
            raise RuntimeError("Allocator LLM config missing for non-mock run")
        agent = create_allocator_agent(ai_models_config=ai_cfg)
        outcome = await run_streamed_agent(
            agent=agent,
            user_prompt=create_user_prompt(allocator_input=allocator_input),
            usage_limits=ai_cfg.model.usage_limits,
        )
        return _AllocatorRunResult(
            proposal=outcome.output,
            messages=list(outcome.all_messages),
            messages_json=None,
        )


class _AllocatorRunResult:
    __slots__ = ("proposal", "messages", "messages_json")

    def __init__(
        self,
        *,
        proposal: AllocatorProposal,
        messages: list[Any] | None,
        messages_json: str | None,
    ) -> None:
        self.proposal = proposal
        self.messages = messages
        self.messages_json = messages_json


def persist_completed_allocator_execution(
    session: Session,
    *,
    execution_id: str,
    system_prompt: str,
    messages: list[Any] | None,
    messages_json: str | None,
    allocation: DomainPortfolioAllocation,
) -> None:
    persist_portfolio_allocation(
        session, agent_execution_id=execution_id, allocation=allocation
    )
    complete_agent_execution_with_conversation(
        session,
        execution_id=execution_id,
        conversation_id=new_id(),
        system_prompt=system_prompt,
        output_json=None,
        completed_at=utc_now_iso(),
        messages=messages,
        messages_json=messages_json,
    )


def _allocator_execution_id_and_status(
    session: Session, workflow_run_id: str
) -> tuple[str, str] | None:
    execution = get_workflow_allocator_execution(session, workflow_run_id)
    if execution is None:
        return None
    return execution.id, execution.status.value


def load_dashboard_portfolio_snapshot(
    session: Session, workflow_run_id: str, is_mock: bool
) -> CurrentPortfolioSnapshot | None:
    if not is_mock:
        return None
    ticker_runs = list_ticker_runs_for_workflow(session, workflow_run_id)
    existing = tuple(
        run["ticker"] for run in ticker_runs if run["is_existing_position"]
    )
    return equal_weight_existing_snapshot(existing, as_of=date.today())
