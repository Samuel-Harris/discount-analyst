"""Surveyor workflow branch: run surveyor agent and spawn discovered ticker lanes."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any, Protocol

from backend.crud.db_utils import utc_now_iso
from backend.crud.run_executions import (
    get_workflow_candidate_snapshot_id,
    get_workflow_surveyor_execution_id,
    get_workflow_surveyor_execution_status,
    update_agent_execution,
)
from backend.db.models import AgentNameDb, ExecutionStatusDb
from backend.dev import mock_conversation_messages, mock_outputs
from backend.pipeline.agent_errors import extract_agent_error_message
from backend.pipeline.llm_config import PipelineLlmConfig, pipeline_llm_config
from discount_analyst.agents.common.ai_logging import AI_LOGFIRE
from discount_analyst.agents.common.terminal_run import run_agent_with_terminal
from discount_analyst.agents.common_prompts.current_date import with_current_date
from discount_analyst.agents.surveyor.schema import SurveyorCandidate
from discount_analyst.agents.surveyor.surveyor import create_surveyor_agent
from discount_analyst.agents.surveyor.system_prompt import (
    SYSTEM_PROMPT as SURVEYOR_SYSTEM_PROMPT,
)
from discount_analyst.agents.surveyor.user_prompt import (
    USER_PROMPT as SURVEYOR_USER_PROMPT,
)
from discount_analyst.integrations.terminal import TerminalRuntimeConfig

if TYPE_CHECKING:
    from common.config import Settings


class SurveyorStageHost(Protocol):
    @property
    def settings(self) -> Settings: ...

    async def db(self, fn: Any, *args: Any, **kwargs: Any) -> Any: ...

    async def recompute(self, workflow_run_id: str) -> None: ...

    def cached_terminal_runtime(self) -> TerminalRuntimeConfig: ...

    async def complete_workflow_exec_with_conversation(
        self,
        *,
        execution_id: str,
        system_prompt: str,
        output_json: str | None,
        messages: list[Any] | None = None,
        messages_json: str | None = None,
    ) -> None: ...

    async def spawn_surveyor_discovered_run(
        self,
        *,
        workflow_run_id: str,
        candidate: SurveyorCandidate,
        is_mock: bool,
        candidate_snapshot_id: str | None,
    ) -> None: ...


class SurveyorStage:
    """Runs the workflow-level Surveyor agent and spawns lanes for discoveries."""

    async def run(
        self,
        host: SurveyorStageHost,
        *,
        workflow_run_id: str,
        portfolio_fold: set[str],
        is_mock: bool,
    ) -> None:
        surveyor_exec_id = await host.db(
            get_workflow_surveyor_execution_id, workflow_run_id
        )
        if surveyor_exec_id is None:
            AI_LOGFIRE.debug(
                "No surveyor execution for workflow; skipping surveyor branch",
                workflow_run_id=workflow_run_id,
            )
            return
        surveyor_status = await host.db(
            get_workflow_surveyor_execution_status, workflow_run_id
        )
        if surveyor_status == ExecutionStatusDb.COMPLETED.value:
            AI_LOGFIRE.info(
                "Surveyor branch already completed; skipping",
                agent_name=AgentNameDb.SURVEYOR,
                workflow_run_id=workflow_run_id,
            )
            return
        try:
            llm = pipeline_llm_config(host.settings, is_mock=is_mock)
            AI_LOGFIRE.info(
                "Surveyor branch started",
                agent_name=AgentNameDb.SURVEYOR,
                workflow_run_id=workflow_run_id,
                is_mock=is_mock,
            )
            await host.db(
                update_agent_execution,
                execution_id=surveyor_exec_id,
                status="running",
                started_at=utc_now_iso(),
                model_name=llm.model_name,
            )
            await host.recompute(workflow_run_id)
            surveyor_output = await self._run_surveyor_agent(
                host,
                execution_id=surveyor_exec_id,
                portfolio_fold=portfolio_fold,
                is_mock=is_mock,
                llm=llm,
            )
            await host.complete_workflow_exec_with_conversation(
                execution_id=surveyor_exec_id,
                system_prompt=with_current_date(SURVEYOR_SYSTEM_PROMPT),
                output_json=surveyor_output.output_json,
                messages=surveyor_output.messages,
                messages_json=surveyor_output.messages_json,
            )
            for candidate in surveyor_output.candidates:
                if candidate.ticker.casefold() in portfolio_fold:
                    continue
                snapshot_id = await host.db(
                    get_workflow_candidate_snapshot_id,
                    workflow_execution_id=surveyor_exec_id,
                    ticker=candidate.ticker,
                )
                await host.spawn_surveyor_discovered_run(
                    workflow_run_id=workflow_run_id,
                    candidate=candidate,
                    is_mock=is_mock,
                    candidate_snapshot_id=snapshot_id,
                )
            AI_LOGFIRE.info(
                "Surveyor branch completed",
                agent_name=AgentNameDb.SURVEYOR,
                workflow_run_id=workflow_run_id,
                discovered_candidates=len(surveyor_output.candidates),
            )
        except Exception as exc:  # noqa: BLE001
            error_msg = extract_agent_error_message(exc)
            AI_LOGFIRE.exception(
                "Surveyor branch failed",
                agent_name=AgentNameDb.SURVEYOR,
                workflow_run_id=workflow_run_id,
                surveyor_execution_id=surveyor_exec_id,
                error_message=error_msg,
            )
            await host.db(
                update_agent_execution,
                execution_id=surveyor_exec_id,
                status="failed",
                error_message=error_msg,
                completed_at=utc_now_iso(),
            )
            raise
        finally:
            await host.recompute(workflow_run_id)

    async def _run_surveyor_agent(
        self,
        host: SurveyorStageHost,
        *,
        execution_id: str,
        portfolio_fold: set[str],
        is_mock: bool,
        llm: PipelineLlmConfig,
    ) -> _SurveyorRunResult:
        if is_mock:
            await asyncio.sleep(5)
            surveyor_output = mock_outputs.mock_surveyor_dashboard_discoveries(
                portfolio_fold, limit=3
            )
            return _SurveyorRunResult(
                candidates=surveyor_output.candidates,
                output_json=surveyor_output.model_dump_json(),
                messages=None,
                messages_json=mock_conversation_messages.surveyor_messages_json(),
            )

        ai_cfg = llm.ai_models_config
        if ai_cfg is None:
            raise RuntimeError("Surveyor LLM config missing for non-mock run")
        outcome = await run_agent_with_terminal(
            settings=host.settings,
            session_id=execution_id,
            runtime=host.cached_terminal_runtime(),
            build_agent=lambda t: create_surveyor_agent(
                ai_models_config=ai_cfg,
                use_perplexity=host.settings.use_perplexity,
                use_mcp_financial_data=host.settings.use_mcp_financial_data,
                terminal=t,
            ),
            user_prompt=SURVEYOR_USER_PROMPT,
            usage_limits=ai_cfg.model.usage_limits,
        )
        return _SurveyorRunResult(
            candidates=outcome.output.candidates,
            output_json=outcome.output.model_dump_json(),
            messages=list(outcome.all_messages),
            messages_json=None,
        )


class _SurveyorRunResult:
    __slots__ = ("candidates", "output_json", "messages", "messages_json")

    def __init__(
        self,
        *,
        candidates: list[SurveyorCandidate],
        output_json: str,
        messages: list[Any] | None,
        messages_json: str | None,
    ) -> None:
        self.candidates = candidates
        self.output_json = output_json
        self.messages = messages
        self.messages_json = messages_json
