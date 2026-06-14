"""Orchestrate Surveyor + per-ticker pipelines and persist dashboard state."""

from __future__ import annotations

import asyncio
from types import SimpleNamespace
from typing import Any, cast

from discount_analyst.agents.common.ai_logging import AI_LOGFIRE

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
    insert_ticker_run_with_agents,
    mark_lane_abort,
    update_agent_execution,
    update_ticker_run_company_name,
    update_ticker_run_completion,
)
from backend.crud.workflow_runs import (
    cancel_unfinished_workflow_children,
    cancel_workflow_run,
    get_workflow_run_inputs,
    list_ticker_runs_for_workflow,
    recompute_workflow_status,
    set_workflow_error,
)
from backend.pipeline.agent_errors import extract_agent_error_message
from backend.pipeline.ports import ProfilerStagePort
from backend.pipeline.stages.profiler_stage import ProfilerStage
from backend.pipeline.stages.surveyor_stage import SurveyorStage
from backend.pipeline.stages.ticker_lane_stage import TickerLaneStage
from common.config import Settings
from discount_analyst.integrations.terminal import TerminalRuntimeConfig
from backend.db.session import SessionFactory
from discount_analyst.agents.surveyor.schema import SurveyorCandidate
from discount_analyst.models.model_name import ModelName


class WorkflowTaskAlreadyActiveError(RuntimeError):
    """Raised when a workflow already has an active background task."""


class DashboardPipelineRunner:
    def __init__(self, session_factory: SessionFactory, settings: Settings) -> None:
        self._session_factory = session_factory
        self._settings = settings
        self._lock = asyncio.Lock()
        self._profiler_stage = ProfilerStage()
        self._surveyor_stage = SurveyorStage()
        self._ticker_lane_stage = TickerLaneStage()
        self._terminal_runtime: TerminalRuntimeConfig | None = None

        async def _profiler_port_get_agent_execution_id(
            run_id: str, agent_name: str
        ) -> str | None:
            return await self.get_exec_id(run_id, agent_name)

        async def _profiler_port_mark_agent_execution(
            *,
            execution_id: str,
            status: str,
            output_json: str | None = None,
            started: bool = False,
            completed: bool = False,
            error_message: str | None = None,
            model_name: ModelName | None = None,
        ) -> None:
            await self.mark_exec(
                execution_id=execution_id,
                status=status,
                output_json=output_json,
                started=started,
                completed=completed,
                error_message=error_message,
                model_name=model_name,
            )

        async def _profiler_port_recompute(workflow_run_id: str) -> None:
            await self.recompute(workflow_run_id)

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
            await self.db(
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

    @property
    def settings(self) -> Settings:
        return self._settings

    def cached_terminal_runtime(self) -> TerminalRuntimeConfig:
        if self._terminal_runtime is None:
            self._terminal_runtime = TerminalRuntimeConfig.from_settings(self._settings)
        return self._terminal_runtime

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
        exists = await self.db(cancel_workflow_run, workflow_run_id)
        if not exists:
            return False
        task = self._workflow_tasks.get(workflow_run_id)
        if task is not None and not task.done():
            task.cancel()
        return True

    async def db(self, fn: Any, *args: Any, **kwargs: Any) -> Any:
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

    async def recompute(self, workflow_run_id: str) -> None:
        await self.db(recompute_workflow_status, workflow_run_id)

    async def get_exec_id(self, run_id: str, agent_name: str) -> str | None:
        return await self.db(
            get_agent_execution_id_by_run_and_agent,
            run_id=run_id,
            agent_name=agent_name,
        )

    async def get_agent_status(self, run_id: str, agent_name: str) -> str | None:
        return await self.db(
            get_agent_execution_status_by_run_and_agent,
            run_id=run_id,
            agent_name=agent_name,
        )

    async def load_completed_agent_output_json(
        self, *, run_id: str, agent_name: str
    ) -> str | None:
        return await self.db(
            get_completed_agent_output_json,
            run_id=run_id,
            agent_name=agent_name,
        )

    async def mark_exec(
        self,
        *,
        execution_id: str,
        status: str,
        output_json: str | None = None,
        started: bool = False,
        completed: bool = False,
        error_message: str | None = None,
        model_name: ModelName | None = None,
    ) -> None:
        await self.db(
            update_agent_execution,
            execution_id=execution_id,
            status=status,
            output_json=output_json,
            started_at=utc_now_iso() if started else None,
            completed_at=utc_now_iso() if completed else None,
            error_message=error_message,
            model_name=model_name,
        )

    async def complete_exec_with_conversation(
        self,
        *,
        execution_id: str,
        system_prompt: str,
        output_json: str | None,
        messages: list[Any] | None = None,
        messages_json: str | None = None,
    ) -> None:
        await self.db(
            complete_agent_execution_with_conversation,
            execution_id=execution_id,
            conversation_id=new_id(),
            system_prompt=system_prompt,
            output_json=output_json,
            completed_at=utc_now_iso(),
            messages=messages,
            messages_json=messages_json,
        )

    async def complete_workflow_exec_with_conversation(
        self,
        *,
        execution_id: str,
        system_prompt: str,
        output_json: str | None,
        messages: list[Any] | None = None,
        messages_json: str | None = None,
    ) -> None:
        await self.db(
            complete_workflow_agent_execution_with_conversation,
            execution_id=execution_id,
            conversation_id=new_id(),
            system_prompt=system_prompt,
            output_json=output_json,
            completed_at=utc_now_iso(),
            messages=messages,
            messages_json=messages_json,
        )

    async def _load_candidate_for_run(self, run_id: str) -> SurveyorCandidate | None:
        return await self.db(get_candidate_for_run, run_id=run_id)

    async def _mark_lane_abort(self, *, run_id: str, error_message: str) -> None:
        await self.db(mark_lane_abort, run_id=run_id, error_message=error_message)

    async def _store_conversation(
        self,
        *,
        run_id: str,
        agent_name: str,
        system_prompt: str,
        messages: list[Any] | None = None,
        messages_json: str | None = None,
    ) -> None:
        execution_id = await self.get_exec_id(run_id, agent_name)
        if execution_id is None:
            return
        await self.db(
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
            inputs = await self.db(get_workflow_run_inputs, workflow_run_id)
            if inputs is None:
                AI_LOGFIRE.debug(
                    "Workflow run inputs missing; skipping execution",
                    workflow_run_id=workflow_run_id,
                )
                return
            portfolio_tickers, is_mock = inputs
            portfolio_fold = {t.casefold() for t in portfolio_tickers}
            initial_runs = await self.db(list_ticker_runs_for_workflow, workflow_run_id)
            AI_LOGFIRE.info(
                "Workflow branches prepared",
                workflow_run_id=workflow_run_id,
                portfolio_ticker_count=len(portfolio_tickers),
                ticker_run_count=len(initial_runs),
                is_mock=is_mock,
            )
            await self._surveyor_stage.run(
                self,
                workflow_run_id=workflow_run_id,
                portfolio_fold=portfolio_fold,
                is_mock=is_mock,
            )
            ticker_runs = await self.db(list_ticker_runs_for_workflow, workflow_run_id)
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
            error_msg = extract_agent_error_message(exc)
            AI_LOGFIRE.exception(
                "Workflow execution failed",
                workflow_run_id=workflow_run_id,
                error_message=error_msg,
            )
            await self.db(set_workflow_error, workflow_run_id, error_msg)
            await self.db(cancel_unfinished_workflow_children, workflow_run_id)
        finally:
            await self.recompute(workflow_run_id)

    async def spawn_surveyor_discovered_run(
        self,
        *,
        workflow_run_id: str,
        candidate: SurveyorCandidate,
        is_mock: bool,
        candidate_snapshot_id: str | None,
    ) -> None:
        run_id = new_id()
        await self.db(
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
        await self.recompute(workflow_run_id)
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
            await self._ticker_lane_stage.run_downstream_from_researcher(
                self,
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
            error_msg = extract_agent_error_message(exc)
            AI_LOGFIRE.exception(
                "Profiler entry pipeline failed",
                entry_path=AgentNameDb.PROFILER,
                workflow_run_id=workflow_run_id,
                run_id=run_id,
                ticker=ticker,
                error_message=error_msg,
            )
            await self._mark_lane_abort(run_id=run_id, error_message=error_msg)
            await self.db(
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
            await self.recompute(workflow_run_id)

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
        status = await self.get_agent_status(run_id, AgentNameDb.PROFILER.value)
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
            await self._ticker_lane_stage.run_downstream_from_researcher(
                self,
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
            error_msg = extract_agent_error_message(exc)
            AI_LOGFIRE.exception(
                "Surveyor entry pipeline failed",
                entry_path=AgentNameDb.SURVEYOR,
                workflow_run_id=workflow_run_id,
                run_id=run_id,
                ticker=candidate.ticker,
                error_message=error_msg,
            )
            await self._mark_lane_abort(run_id=run_id, error_message=error_msg)
            await self.db(
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
            await self.recompute(workflow_run_id)
