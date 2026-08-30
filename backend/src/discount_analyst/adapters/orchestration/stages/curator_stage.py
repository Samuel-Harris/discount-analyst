"""Workflow-level Curator: size the book after every ticker lane is terminal."""

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
    get_workflow_curator_execution,
    update_agent_execution,
)
from discount_analyst.adapters.persistence.crud.workflow_investment_theses import (
    persist_chosen_position_theses,
)
from discount_analyst.adapters.persistence.crud.workflow_runs import (
    list_ticker_runs_for_workflow,
)
from discount_analyst.adapters.persistence.models import (
    AgentExecution,
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
from discount_analyst.agents.curator.curator import create_curator_agent
from discount_analyst.agents.curator.schema import CuratorInput, CuratorProposal
from discount_analyst.agents.curator.system_prompt import (
    SYSTEM_PROMPT as CURATOR_SYSTEM_PROMPT,
)
from discount_analyst.agents.curator.user_prompt import create_user_prompt
from discount_analyst.agents.common_prompts.current_date import with_current_date
from discount_analyst.agents.runtime.ai_logging import AI_LOGFIRE
from discount_analyst.agents.runtime.streamed_agent_run import run_streamed_agent
from discount_analyst.application.allocations.assemble import (
    assemble_curator_input,
    source_run_ids_by_ticker,
)
from discount_analyst.application.allocations.finalise import (
    finalise_curator_proposal,
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


class CuratorStageHost(Protocol):
    @property
    def settings(self) -> Settings: ...

    async def db(self, fn: Any, *args: Any, **kwargs: Any) -> Any: ...

    async def recompute(self, workflow_run_id: str) -> None: ...


class CuratorStage:
    """Runs the workflow-level Curator after every ticker lane is terminal."""

    async def run(
        self,
        host: CuratorStageHost,
        *,
        workflow_run_id: str,
        is_mock: bool,
    ) -> None:
        execution = await host.db(_curator_execution_id_and_status, workflow_run_id)
        if execution is None:
            AI_LOGFIRE.debug(
                "No curator execution for workflow; skipping curator branch",
                workflow_run_id=workflow_run_id,
            )
            return
        execution_id, status = execution
        if status == ExecutionStatusDb.COMPLETED.value:
            AI_LOGFIRE.info(
                "Curator branch already completed; skipping",
                agent_name=AgentNameDb.CURATOR,
                workflow_run_id=workflow_run_id,
            )
            return
        if status == ExecutionStatusDb.SKIPPED.value:
            AI_LOGFIRE.info(
                "Curator branch already skipped; leaving skip in place",
                agent_name=AgentNameDb.CURATOR,
                workflow_run_id=workflow_run_id,
            )
            return

        ticker_runs = await host.db(list_ticker_runs_for_workflow, workflow_run_id)
        if any(
            run["status"] != WorkflowRunStatusDb.COMPLETED.value for run in ticker_runs
        ):
            AI_LOGFIRE.info(
                "Curator skipped because a ticker lane is not completed",
                agent_name=AgentNameDb.CURATOR,
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
                "Curator branch started",
                agent_name=AgentNameDb.CURATOR,
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
            curator_input = assemble_curator_input(bundles, snapshot, date.today())
            agent_result = await self._run_curator_agent(
                curator_input=curator_input,
                is_mock=is_mock,
                llm=llm,
            )
            allocation = finalise_curator_proposal(
                agent_result.proposal,
                curator_input,
                source_run_ids_by_ticker(bundles),
            )
            await host.db(
                persist_completed_curator_execution,
                execution_id=execution_id,
                system_prompt=with_current_date(CURATOR_SYSTEM_PROMPT),
                messages=agent_result.messages,
                messages_json=agent_result.messages_json,
                allocation=allocation,
            )
            AI_LOGFIRE.info(
                "Curator branch completed",
                agent_name=AgentNameDb.CURATOR,
                workflow_run_id=workflow_run_id,
                position_count=len(allocation.positions),
            )
        except Exception as exc:  # noqa: BLE001
            error_msg = extract_agent_error_message(exc)
            AI_LOGFIRE.exception(
                "Curator branch failed",
                agent_name=AgentNameDb.CURATOR,
                workflow_run_id=workflow_run_id,
                curator_execution_id=execution_id,
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

    async def _run_curator_agent(
        self,
        *,
        curator_input: CuratorInput,
        is_mock: bool,
        llm: PipelineLlmConfig,
    ) -> _CuratorRunResult:
        if is_mock:
            await asyncio.sleep(5)
            return _CuratorRunResult(
                proposal=mock_outputs.mock_curator_proposal(curator_input),
                messages=None,
                messages_json=mock_conversation_messages.curator_messages_json(
                    user_prompt=create_user_prompt(curator_input=curator_input),
                ),
            )

        ai_cfg = llm.ai_models_config
        if ai_cfg is None:
            raise RuntimeError("Curator LLM config missing for non-mock run")
        agent = create_curator_agent(ai_models_config=ai_cfg)
        outcome = await run_streamed_agent(
            agent=agent,
            user_prompt=create_user_prompt(curator_input=curator_input),
            usage_limits=ai_cfg.model.usage_limits,
        )
        return _CuratorRunResult(
            proposal=outcome.output,
            messages=list(outcome.all_messages),
            messages_json=None,
        )


class _CuratorRunResult:
    __slots__ = ("proposal", "messages", "messages_json")

    def __init__(
        self,
        *,
        proposal: CuratorProposal,
        messages: list[Any] | None,
        messages_json: str | None,
    ) -> None:
        self.proposal = proposal
        self.messages = messages
        self.messages_json = messages_json


def persist_completed_curator_execution(
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
    execution = session.get(AgentExecution, execution_id)
    if execution is None or execution.workflow_run_id is None:
        msg = f"Curator execution {execution_id} is missing a workflow parent."
        raise ValueError(msg)
    persist_chosen_position_theses(
        session,
        workflow_run_id=execution.workflow_run_id,
        allocation=allocation,
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


def _curator_execution_id_and_status(
    session: Session, workflow_run_id: str
) -> tuple[str, str] | None:
    execution = get_workflow_curator_execution(session, workflow_run_id)
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
