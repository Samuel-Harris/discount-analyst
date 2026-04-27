"""Orchestrate Surveyor + per-ticker pipelines and persist dashboard state."""

from __future__ import annotations

import asyncio
from datetime import date
from types import SimpleNamespace
from typing import Any, cast

from pydantic_ai.exceptions import UnexpectedModelBehavior

from discount_analyst.agents.common.ai_logging import AI_LOGFIRE

from backend.crud.agent_output_persistence import insert_dcf_valuation
from backend.db.models import (
    AgentNameDb,
    EntryPathDb,
    ExecutionStatusDb,
    WorkflowRunStatusDb,
)
from backend.crud.conversations import (
    insert_conversation_for_agent_execution,
)
from backend.contracts.agent_lane_order import SURVEYOR_ENTRY_AGENT_NAMES
from backend.crud.db_utils import new_id, utc_now_iso
from backend.crud.run_executions import (
    complete_agent_execution_with_conversation,
    complete_workflow_agent_execution_with_conversation,
    get_agent_execution_id_by_run_and_agent,
    get_agent_execution_status_by_run_and_agent,
    get_candidate_for_run,
    get_completed_agent_output_json,
    get_dcf_valuation_for_run,
    get_workflow_candidate_snapshot_id,
    get_workflow_surveyor_execution_id,
    get_workflow_surveyor_execution_status,
    insert_ticker_run_with_agents,
    mark_lane_abort,
    update_agent_execution,
    update_ticker_run_company_name,
    update_ticker_run_completion,
    update_workflow_agent_execution,
)
from backend.crud.workflow_runs import (
    cancel_unfinished_workflow_children,
    cancel_workflow_run,
    get_workflow_run_inputs,
    list_ticker_runs_for_workflow,
    recompute_workflow_status,
    set_workflow_error,
)
from backend.pipeline.ports import ProfilerStagePort
from backend.pipeline.stages.profiler_stage import ProfilerStage
from backend.dev import mock_conversation_messages, mock_outputs
from common.config import Settings
from backend.db.session import SessionFactory
from discount_analyst.agents.appraiser.appraiser import create_appraiser_agent
from discount_analyst.agents.appraiser.schema import AppraiserInput, AppraiserOutput
from discount_analyst.agents.appraiser.system_prompt import (
    SYSTEM_PROMPT as APPRAISER_SYSTEM_PROMPT,
)
from discount_analyst.agents.appraiser.user_prompt import (
    create_user_prompt as create_appraiser_user_prompt,
)
from discount_analyst.agents.arbiter.arbiter import create_arbiter_agent
from discount_analyst.agents.arbiter.schema import ArbiterInput, ValuationResult
from discount_analyst.agents.arbiter.system_prompt import (
    SYSTEM_PROMPT as ARBITER_SYSTEM_PROMPT,
)
from discount_analyst.agents.arbiter.user_prompt import (
    create_user_prompt as create_arbiter_user_prompt,
)
from discount_analyst.agents.common.streamed_agent_run import run_streamed_agent
from discount_analyst.agents.researcher.researcher import create_researcher_agent
from discount_analyst.agents.researcher.schema import DeepResearchReport
from discount_analyst.agents.researcher.system_prompt import (
    SYSTEM_PROMPT as RESEARCHER_SYSTEM_PROMPT,
)
from discount_analyst.agents.researcher.user_prompt import (
    create_user_prompt as create_researcher_user_prompt,
)
from discount_analyst.agents.sentinel.schema import sentinel_proceeds_to_valuation
from discount_analyst.agents.sentinel.schema import (
    EvaluationReport as SentinelEvaluationReport,
)
from discount_analyst.agents.sentinel.sentinel import create_sentinel_agent
from discount_analyst.agents.sentinel.system_prompt import (
    SYSTEM_PROMPT as SENTINEL_SYSTEM_PROMPT,
)
from discount_analyst.agents.sentinel.user_prompt import (
    create_user_prompt as create_sentinel_user_prompt,
)
from discount_analyst.agents.strategist.strategist import create_strategist_agent
from discount_analyst.agents.strategist.schema import MispricingThesis
from discount_analyst.agents.strategist.system_prompt import (
    SYSTEM_PROMPT as STRATEGIST_SYSTEM_PROMPT,
)
from discount_analyst.agents.strategist.user_prompt import (
    create_user_prompt as create_strategist_user_prompt,
)
from discount_analyst.agents.surveyor.schema import SurveyorCandidate
from discount_analyst.agents.surveyor.surveyor import create_surveyor_agent
from discount_analyst.agents.surveyor.system_prompt import (
    SYSTEM_PROMPT as SURVEYOR_SYSTEM_PROMPT,
)
from discount_analyst.agents.surveyor.user_prompt import (
    USER_PROMPT as SURVEYOR_USER_PROMPT,
)
from discount_analyst.config.ai_models_config import AIModelsConfig
from discount_analyst.pipeline.builders import (
    build_sentinel_rejection,
    verdict_from_decision,
)
from discount_analyst.valuation.data_types import (
    DCFAnalysisParameters,
    DCFAnalysisResult,
)
from discount_analyst.valuation.dcf_analysis import DCFAnalysis

from backend.contracts.stock_run_args import StockRunArgs


def _extract_agent_error_message(exc: BaseException) -> str:
    """Extract a user-friendly error message, especially for tool failures.

    UnexpectedModelBehavior wraps the underlying cause (e.g., ModelRetry with
    a 402 Payment Required from FMP). This extracts the root cause message.
    """
    if isinstance(exc, UnexpectedModelBehavior):
        # Check for chained cause (e.g., ModelRetry from MCP tool failure)
        cause = exc.__cause__
        if cause is not None:
            cause_msg = str(cause)
            # Surface common billing/quota errors more clearly
            if "402" in cause_msg:
                return f"API quota exceeded (402 Payment Required): {cause_msg}"
            if "401" in cause_msg:
                return f"API authentication failed (401): {cause_msg}"
            if "403" in cause_msg:
                return f"API access denied (403 Forbidden): {cause_msg}"
            return f"Tool failure: {cause_msg}"
        return str(exc)
    return str(exc)


class WorkflowTaskAlreadyActiveError(RuntimeError):
    """Raised when a workflow already has an active background task."""


class DashboardPipelineRunner:
    def __init__(self, session_factory: SessionFactory, settings: Settings) -> None:
        self._session_factory = session_factory
        self._settings = settings
        self._lock = asyncio.Lock()
        self._profiler_stage = ProfilerStage()

        async def _profiler_port_get_agent_execution_id(
            run_id: str, agent_name: str
        ) -> str | None:
            return await self._get_exec_id(run_id, agent_name)

        async def _profiler_port_mark_agent_execution(
            *,
            execution_id: str,
            status: str,
            output_json: str | None = None,
            started: bool = False,
            completed: bool = False,
            error_message: str | None = None,
        ) -> None:
            await self._mark_exec(
                execution_id=execution_id,
                status=status,
                output_json=output_json,
                started=started,
                completed=completed,
                error_message=error_message,
            )

        async def _profiler_port_recompute(workflow_run_id: str) -> None:
            await self._recompute(workflow_run_id)

        async def _profiler_port_store_conversation(
            *,
            run_id: str,
            agent_name: str,
            system_prompt: str,
            messages: list[Any] | None = None,
            messages_json: str | None = None,
        ) -> None:
            await self._store_conversation(
                run_id=run_id,
                agent_name=agent_name,
                system_prompt=system_prompt,
                messages=messages,
                messages_json=messages_json,
            )

        async def _profiler_port_update_company_name(
            run_id: str, company_name: str
        ) -> None:
            await self._db(
                update_ticker_run_company_name,
                run_id=run_id,
                company_name=company_name,
            )

        self._profiler_port_adapter = cast(
            ProfilerStagePort,
            SimpleNamespace(
                get_agent_execution_id=_profiler_port_get_agent_execution_id,
                mark_agent_execution=_profiler_port_mark_agent_execution,
                recompute_workflow_status=_profiler_port_recompute,
                store_agent_conversation=_profiler_port_store_conversation,
                update_ticker_run_company_name=_profiler_port_update_company_name,
            ),
        )
        self._background_tasks: set[asyncio.Task[None]] = set()
        self._workflow_tasks: dict[str, asyncio.Task[None]] = {}

    def has_active_workflow_task(self, workflow_run_id: str) -> bool:
        task = self._workflow_tasks.get(workflow_run_id)
        return task is not None and not task.done()

    def schedule_workflow_execution(self, workflow_run_id: str) -> asyncio.Task[None]:
        """Run ``execute_workflow`` in the background; log unexpected task failures."""
        if self.has_active_workflow_task(workflow_run_id):
            raise WorkflowTaskAlreadyActiveError(workflow_run_id)
        task = asyncio.create_task(
            self.execute_workflow(workflow_run_id),
            name=f"workflow:{workflow_run_id}",
        )
        self._background_tasks.add(task)
        self._workflow_tasks[workflow_run_id] = task

        def _on_done(t: asyncio.Task[None]) -> None:
            self._background_tasks.discard(t)
            if self._workflow_tasks.get(workflow_run_id) is t:
                self._workflow_tasks.pop(workflow_run_id, None)
            if t.cancelled():
                AI_LOGFIRE.info(
                    "Background workflow execution cancelled",
                    workflow_run_id=workflow_run_id,
                )
                return
            exc = t.exception()
            if exc is not None:
                AI_LOGFIRE.exception(
                    "Background workflow task raised (unhandled inside coroutine)",
                    workflow_run_id=workflow_run_id,
                )

        task.add_done_callback(_on_done)
        AI_LOGFIRE.debug(
            "Background workflow execution task scheduled",
            workflow_run_id=workflow_run_id,
            task_name=task.get_name(),
        )
        return task

    async def cancel_workflow_execution(self, workflow_run_id: str) -> bool:
        exists = await self._db(cancel_workflow_run, workflow_run_id)
        if not exists:
            return False
        task = self._workflow_tasks.get(workflow_run_id)
        if task is not None and not task.done():
            task.cancel()
        return True

    async def _db(self, fn: Any, *args: Any, **kwargs: Any) -> Any:
        def _run() -> Any:
            with self._session_factory() as session:
                try:
                    result = fn(session, *args, **kwargs)
                    session.commit()
                    return result
                except Exception:
                    session.rollback()
                    raise

        async with self._lock:
            return await asyncio.to_thread(_run)

    async def _recompute(self, workflow_run_id: str) -> None:
        await self._db(recompute_workflow_status, workflow_run_id)

    async def _get_exec_id(self, run_id: str, agent_name: str) -> str | None:
        return await self._db(
            get_agent_execution_id_by_run_and_agent,
            run_id=run_id,
            agent_name=agent_name,
        )

    async def _get_agent_status(self, run_id: str, agent_name: str) -> str | None:
        return await self._db(
            get_agent_execution_status_by_run_and_agent,
            run_id=run_id,
            agent_name=agent_name,
        )

    async def _load_candidate_for_run(self, run_id: str) -> SurveyorCandidate | None:
        return await self._db(get_candidate_for_run, run_id=run_id)

    async def _load_completed_agent_output_json(
        self, *, run_id: str, agent_name: str
    ) -> str | None:
        return await self._db(
            get_completed_agent_output_json,
            run_id=run_id,
            agent_name=agent_name,
        )

    async def _load_dcf_valuation(self, *, run_id: str) -> DCFAnalysisResult | None:
        return await self._db(get_dcf_valuation_for_run, run_id=run_id)

    async def _mark_exec(
        self,
        *,
        execution_id: str,
        status: str,
        output_json: str | None = None,
        started: bool = False,
        completed: bool = False,
        error_message: str | None = None,
    ) -> None:
        await self._db(
            update_agent_execution,
            execution_id=execution_id,
            status=status,
            output_json=output_json,
            started_at=utc_now_iso() if started else None,
            completed_at=utc_now_iso() if completed else None,
            error_message=error_message,
        )

    async def _complete_exec_with_conversation(
        self,
        *,
        execution_id: str,
        system_prompt: str,
        output_json: str | None,
        messages: list[Any] | None = None,
        messages_json: str | None = None,
    ) -> None:
        await self._db(
            complete_agent_execution_with_conversation,
            execution_id=execution_id,
            conversation_id=new_id(),
            system_prompt=system_prompt,
            output_json=output_json,
            completed_at=utc_now_iso(),
            messages=messages,
            messages_json=messages_json,
        )

    async def _complete_workflow_exec_with_conversation(
        self,
        *,
        execution_id: str,
        system_prompt: str,
        output_json: str | None,
        messages: list[Any] | None = None,
        messages_json: str | None = None,
    ) -> None:
        await self._db(
            complete_workflow_agent_execution_with_conversation,
            execution_id=execution_id,
            conversation_id=new_id(),
            system_prompt=system_prompt,
            output_json=output_json,
            completed_at=utc_now_iso(),
            messages=messages,
            messages_json=messages_json,
        )

    async def _mark_lane_abort(self, *, run_id: str, error_message: str) -> None:
        await self._db(mark_lane_abort, run_id=run_id, error_message=error_message)

    async def _store_conversation(
        self,
        *,
        run_id: str,
        agent_name: str,
        system_prompt: str,
        messages: list[Any] | None = None,
        messages_json: str | None = None,
    ) -> None:
        execution_id = await self._get_exec_id(run_id, agent_name)
        if execution_id is None:
            return
        await self._db(
            insert_conversation_for_agent_execution,
            conversation_id=new_id(),
            agent_execution_id=execution_id,
            system_prompt=system_prompt,
            messages=messages,
            messages_json=messages_json,
        )

    async def execute_workflow(self, workflow_run_id: str) -> None:
        AI_LOGFIRE.info("Workflow execution started", workflow_run_id=workflow_run_id)
        try:
            inputs = await self._db(get_workflow_run_inputs, workflow_run_id)
            if inputs is None:
                AI_LOGFIRE.debug(
                    "Workflow run inputs missing; skipping execution",
                    workflow_run_id=workflow_run_id,
                )
                return
            portfolio_tickers, is_mock = inputs
            portfolio_fold = {t.casefold() for t in portfolio_tickers}
            initial_runs = await self._db(
                list_ticker_runs_for_workflow, workflow_run_id
            )
            AI_LOGFIRE.info(
                "Workflow branches prepared",
                workflow_run_id=workflow_run_id,
                portfolio_ticker_count=len(portfolio_tickers),
                ticker_run_count=len(initial_runs),
                is_mock=is_mock,
            )
            # Run strictly one branch at a time (low provider rate limits).
            await self._surveyor_branch(workflow_run_id, portfolio_fold, is_mock)
            ticker_runs = await self._db(list_ticker_runs_for_workflow, workflow_run_id)
            for run in ticker_runs:
                if run["status"] != WorkflowRunStatusDb.RUNNING.value:
                    continue
                if run["entry_path"] == EntryPathDb.PROFILER.value:
                    await self._profiler_entry_pipeline(
                        workflow_run_id=workflow_run_id,
                        run_id=run["id"],
                        ticker=run["ticker"],
                        is_mock=is_mock,
                    )
                    continue
                candidate = await self._load_candidate_for_run(run["id"])
                if candidate is None:
                    raise RuntimeError(
                        f"Missing candidate snapshot for surveyor run {run['id']}"
                    )
                await self._surveyor_entry_pipeline(
                    workflow_run_id=workflow_run_id,
                    run_id=run["id"],
                    candidate=candidate,
                    is_mock=is_mock,
                )
            AI_LOGFIRE.info(
                "Workflow execution finished",
                workflow_run_id=workflow_run_id,
            )
        except asyncio.CancelledError:
            AI_LOGFIRE.info(
                "Workflow execution cancelled",
                workflow_run_id=workflow_run_id,
            )
            raise
        except Exception as exc:  # noqa: BLE001
            error_msg = _extract_agent_error_message(exc)
            AI_LOGFIRE.exception(
                "Workflow execution failed",
                workflow_run_id=workflow_run_id,
                error_message=error_msg,
            )
            await self._db(set_workflow_error, workflow_run_id, error_msg)
            await self._db(cancel_unfinished_workflow_children, workflow_run_id)
        finally:
            await self._recompute(workflow_run_id)

    async def _surveyor_branch(
        self, workflow_run_id: str, portfolio_fold: set[str], is_mock: bool
    ) -> None:
        surveyor_exec_id = await self._db(
            get_workflow_surveyor_execution_id, workflow_run_id
        )
        if surveyor_exec_id is None:
            AI_LOGFIRE.debug(
                "No surveyor execution for workflow; skipping surveyor branch",
                workflow_run_id=workflow_run_id,
            )
            return
        surveyor_status = await self._db(
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
            AI_LOGFIRE.info(
                "Surveyor branch started",
                agent_name=AgentNameDb.SURVEYOR,
                workflow_run_id=workflow_run_id,
                is_mock=is_mock,
            )
            await self._db(
                update_workflow_agent_execution,
                execution_id=surveyor_exec_id,
                status="running",
                started_at=utc_now_iso(),
            )
            await self._recompute(workflow_run_id)
            surveyor_messages_json: str | None = None
            if is_mock:
                await asyncio.sleep(5)
                surveyor_output = mock_outputs.mock_surveyor_dashboard_discoveries(
                    portfolio_fold, limit=3
                )
                messages: list[Any] | None = None
                surveyor_messages_json = (
                    mock_conversation_messages.surveyor_messages_json()
                )
            else:
                ai_cfg = AIModelsConfig(model_name=self._settings.default_model)
                agent = create_surveyor_agent(
                    ai_models_config=ai_cfg,
                    use_perplexity=self._settings.use_perplexity,
                    use_mcp_financial_data=self._settings.use_mcp_financial_data,
                )
                outcome = await run_streamed_agent(
                    agent=agent,
                    user_prompt=SURVEYOR_USER_PROMPT,
                    usage_limits=ai_cfg.model.usage_limits,
                )
                surveyor_output = outcome.output
                messages = list(outcome.all_messages)
                surveyor_messages_json = None
            await self._complete_workflow_exec_with_conversation(
                execution_id=surveyor_exec_id,
                system_prompt=SURVEYOR_SYSTEM_PROMPT,
                output_json=surveyor_output.model_dump_json(),
                messages=messages,
                messages_json=surveyor_messages_json,
            )
            for candidate in surveyor_output.candidates:
                # Portfolio names already have Profiler ticker runs; skip duplicates.
                if candidate.ticker.casefold() in portfolio_fold:
                    continue
                snapshot_id = await self._db(
                    get_workflow_candidate_snapshot_id,
                    workflow_execution_id=surveyor_exec_id,
                    ticker=candidate.ticker,
                )
                await self._spawn_surveyor_discovered_run(
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
            error_msg = _extract_agent_error_message(exc)
            AI_LOGFIRE.exception(
                "Surveyor branch failed",
                agent_name=AgentNameDb.SURVEYOR,
                workflow_run_id=workflow_run_id,
                surveyor_execution_id=surveyor_exec_id,
                error_message=error_msg,
            )
            await self._db(
                update_workflow_agent_execution,
                execution_id=surveyor_exec_id,
                status="failed",
                error_message=error_msg,
                completed_at=utc_now_iso(),
            )
            raise
        finally:
            await self._recompute(workflow_run_id)

    async def _spawn_surveyor_discovered_run(
        self,
        *,
        workflow_run_id: str,
        candidate: SurveyorCandidate,
        is_mock: bool,
        candidate_snapshot_id: str | None,
    ) -> None:
        run_id = new_id()
        await self._db(
            insert_ticker_run_with_agents,
            run_id=run_id,
            workflow_run_id=workflow_run_id,
            ticker=candidate.ticker,
            company_name=candidate.company_name,
            entry_path=AgentNameDb.SURVEYOR,
            is_existing_position=False,
            is_mock=is_mock,
            agent_names=SURVEYOR_ENTRY_AGENT_NAMES,
            candidate_snapshot_id=candidate_snapshot_id,
        )
        await self._recompute(workflow_run_id)
        await self._surveyor_entry_pipeline(
            workflow_run_id=workflow_run_id,
            run_id=run_id,
            candidate=candidate,
            is_mock=is_mock,
        )

    async def _profiler_entry_pipeline(
        self, *, workflow_run_id: str, run_id: str, ticker: str, is_mock: bool
    ) -> None:
        AI_LOGFIRE.info(
            "Profiler entry pipeline started",
            entry_path=AgentNameDb.PROFILER,
            workflow_run_id=workflow_run_id,
            run_id=run_id,
            ticker=ticker,
            is_mock=is_mock,
        )
        try:
            candidate = await self._run_or_load_profiler_stage(
                workflow_run_id=workflow_run_id,
                run_id=run_id,
                ticker=ticker,
                is_mock=is_mock,
            )
            await self._run_downstream_from_researcher(
                workflow_run_id=workflow_run_id,
                run_id=run_id,
                candidate=candidate,
                is_mock=is_mock,
                is_existing_position=True,
            )
            AI_LOGFIRE.info(
                "Profiler entry pipeline completed",
                entry_path=AgentNameDb.PROFILER,
                workflow_run_id=workflow_run_id,
                run_id=run_id,
                ticker=ticker,
            )
        except Exception as exc:  # noqa: BLE001
            error_msg = _extract_agent_error_message(exc)
            AI_LOGFIRE.exception(
                "Profiler entry pipeline failed",
                entry_path=AgentNameDb.PROFILER,
                workflow_run_id=workflow_run_id,
                run_id=run_id,
                ticker=ticker,
                error_message=error_msg,
            )
            await self._mark_lane_abort(run_id=run_id, error_message=error_msg)
            await self._db(
                update_ticker_run_completion,
                run_id=run_id,
                status="failed",
                final_rating=None,
                decision_type=None,
                recommended_action=None,
                final_verdict_json=None,
                error_message=error_msg,
            )
        finally:
            await self._recompute(workflow_run_id)

    async def _run_profiler_stage(
        self, *, workflow_run_id: str, run_id: str, ticker: str, is_mock: bool
    ) -> SurveyorCandidate:
        return await self._profiler_stage.run(
            self._profiler_port_adapter,
            self._settings,
            workflow_run_id=workflow_run_id,
            run_id=run_id,
            ticker=ticker,
            is_mock=is_mock,
        )

    async def _run_or_load_profiler_stage(
        self, *, workflow_run_id: str, run_id: str, ticker: str, is_mock: bool
    ) -> SurveyorCandidate:
        status = await self._get_agent_status(run_id, AgentNameDb.PROFILER.value)
        if status == ExecutionStatusDb.COMPLETED.value:
            candidate = await self._load_candidate_for_run(run_id)
            if candidate is None:
                raise RuntimeError(f"Missing profiler candidate for run {run_id}")
            AI_LOGFIRE.info(
                "Profiler stage already completed; skipping",
                agent_name=AgentNameDb.PROFILER,
                workflow_run_id=workflow_run_id,
                run_id=run_id,
                ticker=ticker,
            )
            return candidate
        return await self._run_profiler_stage(
            workflow_run_id=workflow_run_id,
            run_id=run_id,
            ticker=ticker,
            is_mock=is_mock,
        )

    async def _surveyor_entry_pipeline(
        self,
        *,
        workflow_run_id: str,
        run_id: str,
        candidate: SurveyorCandidate,
        is_mock: bool,
    ) -> None:
        AI_LOGFIRE.info(
            "Surveyor entry pipeline started",
            entry_path=AgentNameDb.SURVEYOR,
            workflow_run_id=workflow_run_id,
            run_id=run_id,
            ticker=candidate.ticker,
            is_mock=is_mock,
        )
        try:
            await self._run_downstream_from_researcher(
                workflow_run_id=workflow_run_id,
                run_id=run_id,
                candidate=candidate,
                is_mock=is_mock,
                is_existing_position=False,
            )
            AI_LOGFIRE.info(
                "Surveyor entry pipeline completed",
                entry_path=AgentNameDb.SURVEYOR,
                workflow_run_id=workflow_run_id,
                run_id=run_id,
                ticker=candidate.ticker,
            )
        except Exception as exc:  # noqa: BLE001
            error_msg = _extract_agent_error_message(exc)
            AI_LOGFIRE.exception(
                "Surveyor entry pipeline failed",
                entry_path=AgentNameDb.SURVEYOR,
                workflow_run_id=workflow_run_id,
                run_id=run_id,
                ticker=candidate.ticker,
                error_message=error_msg,
            )
            await self._mark_lane_abort(run_id=run_id, error_message=error_msg)
            await self._db(
                update_ticker_run_completion,
                run_id=run_id,
                status="failed",
                final_rating=None,
                decision_type=None,
                recommended_action=None,
                final_verdict_json=None,
                error_message=error_msg,
            )
        finally:
            await self._recompute(workflow_run_id)

    async def _run_downstream_from_researcher(
        self,
        *,
        workflow_run_id: str,
        run_id: str,
        candidate: SurveyorCandidate,
        is_mock: bool,
        is_existing_position: bool,
    ) -> None:
        research_out, thesis, evaluation = await self._run_research_strategist_sentinel(
            workflow_run_id=workflow_run_id,
            run_id=run_id,
            candidate=candidate,
            is_mock=is_mock,
        )
        if not sentinel_proceeds_to_valuation(evaluation):
            AI_LOGFIRE.info(
                "Sentinel gate did not pass; skipping valuation stages",
                workflow_run_id=workflow_run_id,
                run_id=run_id,
                ticker=candidate.ticker,
            )
            await self._apply_sentinel_rejection(
                workflow_run_id=workflow_run_id,
                run_id=run_id,
                thesis=thesis,
                evaluation=evaluation,
                is_existing_position=is_existing_position,
            )
            return
        AI_LOGFIRE.info(
            "Sentinel gate passed; continuing to appraiser and DCF",
            workflow_run_id=workflow_run_id,
            run_id=run_id,
            ticker=candidate.ticker,
        )
        await self._run_appraiser_arbiter(
            workflow_run_id=workflow_run_id,
            run_id=run_id,
            candidate=candidate,
            research_out=research_out,
            thesis=thesis,
            evaluation=evaluation,
            is_mock=is_mock,
            is_existing_position=is_existing_position,
        )

    async def _run_research_strategist_sentinel(
        self,
        *,
        workflow_run_id: str,
        run_id: str,
        candidate: SurveyorCandidate,
        is_mock: bool,
    ) -> tuple[Any, Any, Any]:
        research_exec_id = await self._get_exec_id(run_id, AgentNameDb.RESEARCHER.value)
        if research_exec_id is None:
            raise RuntimeError(f"Missing researcher execution for run {run_id}")
        research_status = await self._get_agent_status(
            run_id, AgentNameDb.RESEARCHER.value
        )
        if research_status == ExecutionStatusDb.COMPLETED.value:
            research_json = await self._load_completed_agent_output_json(
                run_id=run_id, agent_name=AgentNameDb.RESEARCHER.value
            )
            if research_json is None:
                raise RuntimeError(f"Missing completed researcher output for {run_id}")
            research_out = DeepResearchReport.model_validate_json(research_json)
            AI_LOGFIRE.info(
                "Researcher stage already completed; skipping",
                agent_name=AgentNameDb.RESEARCHER,
                workflow_run_id=workflow_run_id,
                run_id=run_id,
                ticker=candidate.ticker,
            )
        else:
            await self._mark_exec(
                execution_id=research_exec_id, status="running", started=True
            )
            await self._recompute(workflow_run_id)
            AI_LOGFIRE.info(
                "Researcher stage started",
                agent_name=AgentNameDb.RESEARCHER,
                workflow_run_id=workflow_run_id,
                run_id=run_id,
                ticker=candidate.ticker,
                is_mock=is_mock,
            )
            r_mock_json: str | None = None
            if is_mock:
                await asyncio.sleep(5)
                research_out = mock_outputs.mock_deep_research(candidate)
                r_messages = None
                r_mock_json = mock_conversation_messages.researcher_messages_json(
                    ticker=candidate.ticker
                )
            else:
                ai_cfg = AIModelsConfig(model_name=self._settings.default_model)
                agent = create_researcher_agent(
                    ai_cfg,
                    use_perplexity=self._settings.use_perplexity,
                    use_mcp_financial_data=self._settings.use_mcp_financial_data,
                )
                outcome = await run_streamed_agent(
                    agent=agent,
                    user_prompt=create_researcher_user_prompt(
                        surveyor_candidate=candidate
                    ),
                    usage_limits=ai_cfg.model.usage_limits,
                )
                research_out = outcome.output
                r_messages = list(outcome.all_messages)
                r_mock_json = None
            await self._complete_exec_with_conversation(
                execution_id=research_exec_id,
                system_prompt=RESEARCHER_SYSTEM_PROMPT,
                output_json=research_out.model_dump_json(),
                messages=r_messages,
                messages_json=r_mock_json,
            )
            AI_LOGFIRE.info(
                "Researcher stage completed",
                agent_name=AgentNameDb.RESEARCHER,
                workflow_run_id=workflow_run_id,
                run_id=run_id,
                ticker=candidate.ticker,
            )

        strategist_exec_id = await self._get_exec_id(
            run_id, AgentNameDb.STRATEGIST.value
        )
        if strategist_exec_id is None:
            raise RuntimeError(f"Missing strategist execution for run {run_id}")
        strategist_status = await self._get_agent_status(
            run_id, AgentNameDb.STRATEGIST.value
        )
        if strategist_status == ExecutionStatusDb.COMPLETED.value:
            thesis_json = await self._load_completed_agent_output_json(
                run_id=run_id, agent_name=AgentNameDb.STRATEGIST.value
            )
            if thesis_json is None:
                raise RuntimeError(f"Missing completed strategist output for {run_id}")
            thesis = MispricingThesis.model_validate_json(thesis_json)
            AI_LOGFIRE.info(
                "Strategist stage already completed; skipping",
                agent_name=AgentNameDb.STRATEGIST,
                workflow_run_id=workflow_run_id,
                run_id=run_id,
                ticker=candidate.ticker,
            )
        else:
            await self._mark_exec(
                execution_id=strategist_exec_id, status="running", started=True
            )
            await self._recompute(workflow_run_id)
            AI_LOGFIRE.info(
                "Strategist stage started",
                agent_name=AgentNameDb.STRATEGIST,
                workflow_run_id=workflow_run_id,
                run_id=run_id,
                ticker=candidate.ticker,
                is_mock=is_mock,
            )
            s_mock_json: str | None = None
            if is_mock:
                await asyncio.sleep(5)
                thesis = mock_outputs.mock_thesis(candidate)
                s_messages = None
                s_mock_json = mock_conversation_messages.strategist_messages_json(
                    ticker=candidate.ticker
                )
            else:
                ai_cfg = AIModelsConfig(model_name=self._settings.default_model)
                agent = create_strategist_agent(ai_cfg)
                outcome = await run_streamed_agent(
                    agent=agent,
                    user_prompt=create_strategist_user_prompt(
                        surveyor_candidate=candidate, deep_research=research_out
                    ),
                    usage_limits=ai_cfg.model.usage_limits,
                )
                thesis = outcome.output
                s_messages = list(outcome.all_messages)
                s_mock_json = None
            await self._complete_exec_with_conversation(
                execution_id=strategist_exec_id,
                system_prompt=STRATEGIST_SYSTEM_PROMPT,
                output_json=thesis.model_dump_json(),
                messages=s_messages,
                messages_json=s_mock_json,
            )
            AI_LOGFIRE.info(
                "Strategist stage completed",
                agent_name=AgentNameDb.STRATEGIST,
                workflow_run_id=workflow_run_id,
                run_id=run_id,
                ticker=candidate.ticker,
            )

        sentinel_exec_id = await self._get_exec_id(run_id, AgentNameDb.SENTINEL.value)
        if sentinel_exec_id is None:
            raise RuntimeError(f"Missing sentinel execution for run {run_id}")
        sentinel_status = await self._get_agent_status(
            run_id, AgentNameDb.SENTINEL.value
        )
        if sentinel_status == ExecutionStatusDb.COMPLETED.value:
            evaluation_json = await self._load_completed_agent_output_json(
                run_id=run_id, agent_name=AgentNameDb.SENTINEL.value
            )
            if evaluation_json is None:
                raise RuntimeError(f"Missing completed sentinel output for {run_id}")
            evaluation = SentinelEvaluationReport.model_validate_json(evaluation_json)
            AI_LOGFIRE.info(
                "Sentinel stage already completed; skipping",
                agent_name=AgentNameDb.SENTINEL,
                workflow_run_id=workflow_run_id,
                run_id=run_id,
                ticker=candidate.ticker,
            )
        else:
            await self._mark_exec(
                execution_id=sentinel_exec_id, status="running", started=True
            )
            await self._recompute(workflow_run_id)
            AI_LOGFIRE.info(
                "Sentinel stage started",
                agent_name=AgentNameDb.SENTINEL,
                workflow_run_id=workflow_run_id,
                run_id=run_id,
                ticker=candidate.ticker,
                is_mock=is_mock,
            )
            n_mock_json: str | None = None
            if is_mock:
                await asyncio.sleep(5)
                evaluation = mock_outputs.mock_sentinel_evaluation(
                    candidate=candidate,
                    proceed=mock_outputs.mock_sentinel_proceed_for_dashboard_lane(
                        candidate.ticker
                    ),
                )
                n_messages = None
                n_mock_json = mock_conversation_messages.sentinel_messages_json(
                    ticker=candidate.ticker
                )
            else:
                ai_cfg = AIModelsConfig(model_name=self._settings.default_model)
                agent = create_sentinel_agent(ai_cfg)
                outcome = await run_streamed_agent(
                    agent=agent,
                    user_prompt=create_sentinel_user_prompt(
                        surveyor_candidate=candidate,
                        deep_research=research_out,
                        thesis=thesis,
                    ),
                    usage_limits=ai_cfg.model.usage_limits,
                )
                evaluation = outcome.output
                n_messages = list(outcome.all_messages)
                n_mock_json = None
            await self._complete_exec_with_conversation(
                execution_id=sentinel_exec_id,
                system_prompt=SENTINEL_SYSTEM_PROMPT,
                output_json=evaluation.model_dump_json(),
                messages=n_messages,
                messages_json=n_mock_json,
            )
            AI_LOGFIRE.info(
                "Sentinel stage completed",
                agent_name=AgentNameDb.SENTINEL,
                workflow_run_id=workflow_run_id,
                run_id=run_id,
                ticker=candidate.ticker,
            )
        return research_out, thesis, evaluation

    async def _apply_sentinel_rejection(
        self,
        *,
        workflow_run_id: str,
        run_id: str,
        thesis: Any,
        evaluation: Any,
        is_existing_position: bool,
    ) -> None:
        AI_LOGFIRE.info(
            "Applying sentinel rejection verdict",
            workflow_run_id=workflow_run_id,
            run_id=run_id,
        )
        for agent_name in ("appraiser", "arbiter"):
            execution_id = await self._get_exec_id(run_id, agent_name)
            if execution_id is not None:
                await self._mark_exec(
                    execution_id=execution_id, status="skipped", completed=True
                )
        rejection = build_sentinel_rejection(
            evaluation,
            thesis,
            is_existing_position=is_existing_position,
            decision_date=date.today().isoformat(),
        )
        verdict = verdict_from_decision(rejection)
        await self._db(
            update_ticker_run_completion,
            run_id=run_id,
            status="completed",
            final_rating=str(verdict.rating.value),
            decision_type="sentinel_rejection",
            recommended_action=verdict.recommended_action,
            final_verdict_json=verdict.model_dump_json(),
            error_message=None,
        )
        await self._recompute(workflow_run_id)

    async def _run_appraiser_arbiter(
        self,
        *,
        workflow_run_id: str,
        run_id: str,
        candidate: SurveyorCandidate,
        research_out: Any,
        thesis: Any,
        evaluation: Any,
        is_mock: bool,
        is_existing_position: bool,
    ) -> None:
        appraiser_exec_id = await self._get_exec_id(run_id, AgentNameDb.APPRAISER.value)
        if appraiser_exec_id is None:
            return
        stock_args = StockRunArgs(
            surveyor_candidate=candidate,
            risk_free_rate=self._settings.risk_free_rate,
            model=self._settings.default_model,
        )
        appraiser_status = await self._get_agent_status(
            run_id, AgentNameDb.APPRAISER.value
        )
        if appraiser_status == ExecutionStatusDb.COMPLETED.value:
            appraiser_json = await self._load_completed_agent_output_json(
                run_id=run_id, agent_name=AgentNameDb.APPRAISER.value
            )
            if appraiser_json is None:
                raise RuntimeError(f"Missing completed appraiser output for {run_id}")
            appraiser_out = AppraiserOutput.model_validate_json(appraiser_json)
            AI_LOGFIRE.info(
                "Appraiser stage already completed; skipping",
                agent_name=AgentNameDb.APPRAISER,
                workflow_run_id=workflow_run_id,
                run_id=run_id,
                ticker=candidate.ticker,
            )
        else:
            await self._mark_exec(
                execution_id=appraiser_exec_id, status="running", started=True
            )
            await self._recompute(workflow_run_id)
            AI_LOGFIRE.info(
                "Appraiser stage started",
                agent_name=AgentNameDb.APPRAISER,
                workflow_run_id=workflow_run_id,
                run_id=run_id,
                ticker=candidate.ticker,
                is_mock=is_mock,
            )
            appraiser_input = AppraiserInput(
                stock_candidate=candidate,
                deep_research=research_out,
                thesis=thesis,
                evaluation=evaluation,
                risk_free_rate=self._settings.risk_free_rate,
            )
            a_mock_json: str | None = None
            if is_mock:
                await asyncio.sleep(5)
                appraiser_out = mock_outputs.mock_appraiser_output(candidate)
                a_messages = None
                a_mock_json = mock_conversation_messages.appraiser_messages_json(
                    ticker=candidate.ticker
                )
            else:
                ai_cfg = AIModelsConfig(model_name=self._settings.default_model)
                agent = create_appraiser_agent(
                    ai_cfg,
                    use_perplexity=self._settings.use_perplexity,
                    use_mcp_financial_data=self._settings.use_mcp_financial_data,
                )
                outcome = await run_streamed_agent(
                    agent=agent,
                    user_prompt=create_appraiser_user_prompt(
                        appraiser_input=appraiser_input
                    ),
                    usage_limits=ai_cfg.model.usage_limits,
                )
                appraiser_out = outcome.output
                a_messages = list(outcome.all_messages)
                a_mock_json = None
            await self._complete_exec_with_conversation(
                execution_id=appraiser_exec_id,
                system_prompt=APPRAISER_SYSTEM_PROMPT,
                output_json=appraiser_out.model_dump_json(),
                messages=a_messages,
                messages_json=a_mock_json,
            )
            AI_LOGFIRE.info(
                "Appraiser stage completed; running DCF",
                agent_name=AgentNameDb.APPRAISER,
                workflow_run_id=workflow_run_id,
                run_id=run_id,
                ticker=candidate.ticker,
            )

        dcf_result = (
            await self._load_dcf_valuation(run_id=run_id)
            if appraiser_status == ExecutionStatusDb.COMPLETED.value
            else None
        )
        persist_dcf_result = dcf_result is None
        dcf_error: str | None = None
        if dcf_result is None:
            dcf_result, dcf_error = await self._run_dcf(
                stock_args,
                appraiser_out,
                workflow_run_id=workflow_run_id,
                run_id=run_id,
                ticker=candidate.ticker,
            )
        if dcf_result is None:
            AI_LOGFIRE.warning(
                "DCF valuation failed or produced no result; skipping arbiter",
                workflow_run_id=workflow_run_id,
                run_id=run_id,
                ticker=candidate.ticker,
                error=dcf_error,
            )
            await self._db(
                update_ticker_run_completion,
                run_id=run_id,
                status="failed",
                final_rating=None,
                decision_type=None,
                recommended_action=None,
                final_verdict_json=None,
                error_message=dcf_error or "DCF failed",
            )
            arbiter_exec_id = await self._get_exec_id(run_id, AgentNameDb.ARBITER.value)
            if arbiter_exec_id is not None:
                await self._mark_exec(
                    execution_id=arbiter_exec_id, status="skipped", completed=True
                )
            await self._recompute(workflow_run_id)
            return
        if persist_dcf_result:
            await self._db(
                insert_dcf_valuation,
                run_id=run_id,
                appraiser_agent_execution_id=appraiser_exec_id,
                dcf_result=dcf_result,
            )
        arbiter_exec_id = await self._get_exec_id(run_id, AgentNameDb.ARBITER.value)
        if arbiter_exec_id is None:
            return
        arbiter_status = await self._get_agent_status(run_id, AgentNameDb.ARBITER.value)
        if arbiter_status == ExecutionStatusDb.COMPLETED.value:
            AI_LOGFIRE.info(
                "Arbiter stage already completed; skipping",
                agent_name=AgentNameDb.ARBITER,
                workflow_run_id=workflow_run_id,
                run_id=run_id,
                ticker=candidate.ticker,
            )
            return
        await self._mark_exec(
            execution_id=arbiter_exec_id, status="running", started=True
        )
        await self._recompute(workflow_run_id)
        AI_LOGFIRE.info(
            "Arbiter stage started",
            agent_name=AgentNameDb.ARBITER,
            workflow_run_id=workflow_run_id,
            run_id=run_id,
            ticker=candidate.ticker,
            is_mock=is_mock,
        )
        b_mock_json: str | None = None
        if is_mock:
            await asyncio.sleep(5)
            arbiter_decision = mock_outputs.mock_arbiter_decision(
                candidate, is_existing_position=is_existing_position
            )
            b_messages = None
            b_mock_json = mock_conversation_messages.arbiter_messages_json(
                ticker=candidate.ticker
            )
        else:
            ai_cfg = AIModelsConfig(model_name=self._settings.default_model)
            agent = create_arbiter_agent(ai_cfg)
            arbiter_input = ArbiterInput(
                stock_candidate=candidate,
                deep_research=research_out,
                thesis=thesis,
                evaluation=evaluation,
                valuation=ValuationResult(
                    appraiser_output=appraiser_out, dcf_result=dcf_result
                ),
                risk_free_rate=self._settings.risk_free_rate,
                is_existing_position=is_existing_position,
            )
            outcome = await run_streamed_agent(
                agent=agent,
                user_prompt=create_arbiter_user_prompt(arbiter_input=arbiter_input),
                usage_limits=ai_cfg.model.usage_limits,
            )
            arbiter_decision = outcome.output.model_copy(
                update={"decision_date": date.today().isoformat()}
            )
            b_messages = list(outcome.all_messages)
            b_mock_json = None
        await self._complete_exec_with_conversation(
            execution_id=arbiter_exec_id,
            system_prompt=ARBITER_SYSTEM_PROMPT,
            output_json=arbiter_decision.model_dump_json(),
            messages=b_messages,
            messages_json=b_mock_json,
        )
        verdict = verdict_from_decision(arbiter_decision)
        await self._db(
            update_ticker_run_completion,
            run_id=run_id,
            status="completed",
            final_rating=str(verdict.rating.value),
            decision_type="arbiter",
            recommended_action=verdict.recommended_action,
            final_verdict_json=verdict.model_dump_json(),
            error_message=None,
        )
        await self._recompute(workflow_run_id)
        AI_LOGFIRE.info(
            "Arbiter stage completed; ticker run finished",
            agent_name=AgentNameDb.ARBITER,
            workflow_run_id=workflow_run_id,
            run_id=run_id,
            ticker=candidate.ticker,
        )

    async def _run_dcf(
        self,
        stock_args: StockRunArgs,
        appraiser_out: Any,
        *,
        workflow_run_id: str,
        run_id: str,
        ticker: str,
    ) -> tuple[Any, str | None]:
        def _sync_dcf() -> tuple[Any, str | None]:
            params = DCFAnalysisParameters(
                stock_data=appraiser_out.stock_data,
                stock_assumptions=appraiser_out.stock_assumptions,
                risk_free_rate=stock_args.risk_free_rate,
            )
            try:
                return DCFAnalysis(params).dcf_analysis(), None
            except Exception as exc:  # noqa: BLE001
                AI_LOGFIRE.exception(
                    "DCF analysis raised",
                    workflow_run_id=workflow_run_id,
                    run_id=run_id,
                    ticker=ticker,
                )
                return None, str(exc)

        return await asyncio.to_thread(_sync_dcf)
