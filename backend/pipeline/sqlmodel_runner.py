"""Orchestrate Surveyor + per-ticker pipelines and persist dashboard state."""

from __future__ import annotations

import asyncio
from datetime import date
from typing import Any

from backend.dev import mock_outputs
from backend.settings import DashboardSettings
from backend.crud import repository as repo
from backend.crud.repository import SURVEYOR_ENTRY_AGENT_NAMES, new_id
from backend.db.session import SessionFactory
from discount_analyst.agents.appraiser.appraiser import create_appraiser_agent
from discount_analyst.agents.appraiser.schema import AppraiserInput
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
from discount_analyst.agents.profiler.profiler import create_profiler_agent
from discount_analyst.agents.profiler.system_prompt import (
    SYSTEM_PROMPT as PROFILER_SYSTEM_PROMPT,
)
from discount_analyst.agents.profiler.user_prompt import create_profiler_user_prompt
from discount_analyst.agents.researcher.researcher import create_researcher_agent
from discount_analyst.agents.researcher.system_prompt import (
    SYSTEM_PROMPT as RESEARCHER_SYSTEM_PROMPT,
)
from discount_analyst.agents.researcher.user_prompt import (
    create_user_prompt as create_researcher_user_prompt,
)
from discount_analyst.agents.sentinel.schema import sentinel_proceeds_to_valuation
from discount_analyst.agents.sentinel.sentinel import create_sentinel_agent
from discount_analyst.agents.sentinel.system_prompt import (
    SYSTEM_PROMPT as SENTINEL_SYSTEM_PROMPT,
)
from discount_analyst.agents.sentinel.user_prompt import (
    create_user_prompt as create_sentinel_user_prompt,
)
from discount_analyst.agents.strategist.strategist import create_strategist_agent
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
from discount_analyst.valuation.data_types import DCFAnalysisParameters
from discount_analyst.valuation.dcf_analysis import DCFAnalysis
from scripts.agents.run_appraiser import StockRunArgs


class DashboardPipelineRunner:
    def __init__(
        self, session_factory: SessionFactory, settings: DashboardSettings
    ) -> None:
        self._session_factory = session_factory
        self._settings = settings
        self._lock = asyncio.Lock()

    async def _db(self, fn: Any, *args: Any, **kwargs: Any) -> Any:
        def _run() -> Any:
            with self._session_factory() as session:
                return fn(session, *args, **kwargs)

        async with self._lock:
            return await asyncio.to_thread(_run)

    async def _recompute(self, workflow_run_id: str) -> None:
        await self._db(repo.recompute_workflow_status, workflow_run_id)

    async def _get_exec_id(self, run_id: str, agent_name: str) -> str | None:
        return await self._db(
            repo.get_agent_execution_id_by_run_and_agent,
            run_id=run_id,
            agent_name=agent_name,
        )

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
            repo.update_agent_execution,
            execution_id=execution_id,
            status=status,
            output_json=output_json,
            started_at=repo.utc_now_iso() if started else None,
            completed_at=repo.utc_now_iso() if completed else None,
            error_message=error_message,
        )

    async def _store_conversation(
        self,
        *,
        run_id: str,
        agent_name: str,
        system_prompt: str,
        messages: list[Any],
    ) -> None:
        execution_id = await self._get_exec_id(run_id, agent_name)
        if execution_id is None:
            return
        await self._db(
            repo.insert_conversation_for_agent_execution,
            conversation_id=new_id(),
            agent_execution_id=execution_id,
            system_prompt=system_prompt,
            messages=messages,
        )

    async def execute_workflow(self, workflow_run_id: str) -> None:
        try:
            inputs = await self._db(repo.get_workflow_run_inputs, workflow_run_id)
            if inputs is None:
                return
            portfolio_tickers, is_mock = inputs
            portfolio_fold = {t.casefold() for t in portfolio_tickers}
            profiler_runs = await self._db(
                repo.list_profiler_runs_for_workflow, workflow_run_id
            )
            tasks: list[asyncio.Task[Any]] = [
                asyncio.create_task(
                    self._surveyor_branch(workflow_run_id, portfolio_fold, is_mock)
                )
            ]
            for run_id, ticker in profiler_runs:
                tasks.append(
                    asyncio.create_task(
                        self._profiler_entry_pipeline(
                            workflow_run_id=workflow_run_id,
                            run_id=run_id,
                            ticker=ticker,
                            is_mock=is_mock,
                        )
                    )
                )
            await asyncio.gather(*tasks, return_exceptions=True)
        except Exception as exc:  # noqa: BLE001
            await self._db(repo.set_workflow_error, workflow_run_id, str(exc))
        finally:
            await self._recompute(workflow_run_id)

    async def _surveyor_branch(
        self, workflow_run_id: str, portfolio_fold: set[str], is_mock: bool
    ) -> None:
        surveyor_exec_id = await self._db(
            repo.get_workflow_surveyor_execution_id, workflow_run_id
        )
        if surveyor_exec_id is None:
            return
        try:
            await self._db(
                repo.update_workflow_agent_execution,
                execution_id=surveyor_exec_id,
                status="running",
                started_at=repo.utc_now_iso(),
            )
            await self._recompute(workflow_run_id)
            if is_mock:
                await asyncio.sleep(5)
                surveyor_output = mock_outputs.mock_surveyor_dashboard_discoveries(
                    portfolio_fold, limit=3
                )
                messages: list[Any] = []
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
            await self._db(
                repo.update_workflow_agent_execution,
                execution_id=surveyor_exec_id,
                status="completed",
                output_json=surveyor_output.model_dump_json(),
                completed_at=repo.utc_now_iso(),
            )
            await self._db(
                repo.insert_conversation_for_workflow_agent,
                conversation_id=new_id(),
                workflow_agent_execution_id=surveyor_exec_id,
                system_prompt=SURVEYOR_SYSTEM_PROMPT,
                messages=messages,
            )
            for candidate in surveyor_output.candidates:
                # Portfolio names already have Profiler ticker runs; skip duplicates.
                if candidate.ticker.casefold() in portfolio_fold:
                    continue
                snapshot_id = await self._db(
                    repo.get_workflow_candidate_snapshot_id,
                    workflow_execution_id=surveyor_exec_id,
                    ticker=candidate.ticker,
                )
                await self._spawn_surveyor_discovered_run(
                    workflow_run_id=workflow_run_id,
                    candidate=candidate,
                    is_mock=is_mock,
                    candidate_snapshot_id=snapshot_id,
                )
        except Exception as exc:  # noqa: BLE001
            await self._db(
                repo.update_workflow_agent_execution,
                execution_id=surveyor_exec_id,
                status="failed",
                error_message=str(exc),
                completed_at=repo.utc_now_iso(),
            )
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
            repo.insert_ticker_run_with_agents,
            run_id=run_id,
            workflow_run_id=workflow_run_id,
            ticker=candidate.ticker,
            company_name=candidate.company_name,
            entry_path="surveyor",
            is_existing_position=self._settings.is_existing_position,
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
        try:
            candidate = await self._run_profiler_stage(
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
            )
        except Exception as exc:  # noqa: BLE001
            await self._db(
                repo.update_ticker_run_completion,
                run_id=run_id,
                status="failed",
                final_rating=None,
                decision_type=None,
                recommended_action=None,
                final_verdict_json=None,
                error_message=str(exc),
            )
        finally:
            await self._recompute(workflow_run_id)

    async def _run_profiler_stage(
        self, *, workflow_run_id: str, run_id: str, ticker: str, is_mock: bool
    ) -> SurveyorCandidate:
        profiler_exec_id = await self._get_exec_id(run_id, "profiler")
        if profiler_exec_id is None:
            raise RuntimeError(f"Missing profiler execution for run {run_id}")
        await self._mark_exec(
            execution_id=profiler_exec_id, status="running", started=True
        )
        await self._recompute(workflow_run_id)
        if is_mock:
            await asyncio.sleep(5)
            profiler_output = mock_outputs.mock_profiler_output(ticker=ticker)
            messages: list[Any] = []
        else:
            ai_cfg = AIModelsConfig(model_name=self._settings.default_model)
            agent = create_profiler_agent(
                ai_models_config=ai_cfg,
                use_perplexity=self._settings.use_perplexity,
                use_mcp_financial_data=self._settings.use_mcp_financial_data,
            )
            outcome = await run_streamed_agent(
                agent=agent,
                user_prompt=create_profiler_user_prompt(ticker),
                usage_limits=ai_cfg.model.usage_limits,
            )
            profiler_output = outcome.output
            messages = list(outcome.all_messages)
        await self._mark_exec(
            execution_id=profiler_exec_id,
            status="completed",
            output_json=profiler_output.model_dump_json(),
            completed=True,
        )
        await self._store_conversation(
            run_id=run_id,
            agent_name="profiler",
            system_prompt=PROFILER_SYSTEM_PROMPT,
            messages=messages,
        )
        await self._db(
            repo.update_ticker_run_company_name,
            run_id=run_id,
            company_name=profiler_output.candidate.company_name,
        )
        return profiler_output.candidate

    async def _surveyor_entry_pipeline(
        self,
        *,
        workflow_run_id: str,
        run_id: str,
        candidate: SurveyorCandidate,
        is_mock: bool,
    ) -> None:
        try:
            await self._run_downstream_from_researcher(
                workflow_run_id=workflow_run_id,
                run_id=run_id,
                candidate=candidate,
                is_mock=is_mock,
            )
        except Exception as exc:  # noqa: BLE001
            await self._db(
                repo.update_ticker_run_completion,
                run_id=run_id,
                status="failed",
                final_rating=None,
                decision_type=None,
                recommended_action=None,
                final_verdict_json=None,
                error_message=str(exc),
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
    ) -> None:
        research_out, thesis, evaluation = await self._run_research_strategist_sentinel(
            workflow_run_id=workflow_run_id,
            run_id=run_id,
            candidate=candidate,
            is_mock=is_mock,
        )
        if not sentinel_proceeds_to_valuation(evaluation):
            await self._apply_sentinel_rejection(
                workflow_run_id=workflow_run_id,
                run_id=run_id,
                thesis=thesis,
                evaluation=evaluation,
            )
            return
        await self._run_appraiser_arbiter(
            workflow_run_id=workflow_run_id,
            run_id=run_id,
            candidate=candidate,
            research_out=research_out,
            thesis=thesis,
            evaluation=evaluation,
            is_mock=is_mock,
        )

    async def _run_research_strategist_sentinel(
        self,
        *,
        workflow_run_id: str,
        run_id: str,
        candidate: SurveyorCandidate,
        is_mock: bool,
    ) -> tuple[Any, Any, Any]:
        research_exec_id = await self._get_exec_id(run_id, "researcher")
        if research_exec_id is None:
            raise RuntimeError(f"Missing researcher execution for run {run_id}")
        await self._mark_exec(
            execution_id=research_exec_id, status="running", started=True
        )
        await self._recompute(workflow_run_id)
        if is_mock:
            await asyncio.sleep(5)
            research_out = mock_outputs.mock_deep_research(candidate)
            r_messages: list[Any] = []
        else:
            ai_cfg = AIModelsConfig(model_name=self._settings.default_model)
            agent = create_researcher_agent(
                ai_cfg,
                use_perplexity=self._settings.use_perplexity,
                use_mcp_financial_data=self._settings.use_mcp_financial_data,
            )
            outcome = await run_streamed_agent(
                agent=agent,
                user_prompt=create_researcher_user_prompt(surveyor_candidate=candidate),
                usage_limits=ai_cfg.model.usage_limits,
            )
            research_out = outcome.output
            r_messages = list(outcome.all_messages)
        await self._mark_exec(
            execution_id=research_exec_id,
            status="completed",
            output_json=research_out.model_dump_json(),
            completed=True,
        )
        await self._store_conversation(
            run_id=run_id,
            agent_name="researcher",
            system_prompt=RESEARCHER_SYSTEM_PROMPT,
            messages=r_messages,
        )

        strategist_exec_id = await self._get_exec_id(run_id, "strategist")
        if strategist_exec_id is None:
            raise RuntimeError(f"Missing strategist execution for run {run_id}")
        await self._mark_exec(
            execution_id=strategist_exec_id, status="running", started=True
        )
        await self._recompute(workflow_run_id)
        if is_mock:
            await asyncio.sleep(5)
            thesis = mock_outputs.mock_thesis(candidate)
            s_messages: list[Any] = []
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
        await self._mark_exec(
            execution_id=strategist_exec_id,
            status="completed",
            output_json=thesis.model_dump_json(),
            completed=True,
        )
        await self._store_conversation(
            run_id=run_id,
            agent_name="strategist",
            system_prompt=STRATEGIST_SYSTEM_PROMPT,
            messages=s_messages,
        )

        sentinel_exec_id = await self._get_exec_id(run_id, "sentinel")
        if sentinel_exec_id is None:
            raise RuntimeError(f"Missing sentinel execution for run {run_id}")
        await self._mark_exec(
            execution_id=sentinel_exec_id, status="running", started=True
        )
        await self._recompute(workflow_run_id)
        if is_mock:
            await asyncio.sleep(5)
            evaluation = mock_outputs.mock_sentinel_evaluation(
                candidate=candidate, proceed=True
            )
            n_messages: list[Any] = []
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
        await self._mark_exec(
            execution_id=sentinel_exec_id,
            status="completed",
            output_json=evaluation.model_dump_json(),
            completed=True,
        )
        await self._store_conversation(
            run_id=run_id,
            agent_name="sentinel",
            system_prompt=SENTINEL_SYSTEM_PROMPT,
            messages=n_messages,
        )
        return research_out, thesis, evaluation

    async def _apply_sentinel_rejection(
        self, *, workflow_run_id: str, run_id: str, thesis: Any, evaluation: Any
    ) -> None:
        for agent_name in ("appraiser", "arbiter"):
            execution_id = await self._get_exec_id(run_id, agent_name)
            if execution_id is not None:
                await self._mark_exec(
                    execution_id=execution_id, status="skipped", completed=True
                )
        rejection = build_sentinel_rejection(
            evaluation,
            thesis,
            is_existing_position=self._settings.is_existing_position,
            decision_date=date.today().isoformat(),
        )
        verdict = verdict_from_decision(rejection)
        await self._db(
            repo.update_ticker_run_completion,
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
    ) -> None:
        appraiser_exec_id = await self._get_exec_id(run_id, "appraiser")
        if appraiser_exec_id is None:
            return
        await self._mark_exec(
            execution_id=appraiser_exec_id, status="running", started=True
        )
        await self._recompute(workflow_run_id)
        appraiser_input = AppraiserInput(
            stock_candidate=candidate,
            deep_research=research_out,
            thesis=thesis,
            evaluation=evaluation,
            risk_free_rate=self._settings.risk_free_rate,
        )
        stock_args = StockRunArgs(
            surveyor_candidate=candidate,
            risk_free_rate=self._settings.risk_free_rate,
            model=self._settings.default_model,
        )
        if is_mock:
            await asyncio.sleep(5)
            appraiser_out = mock_outputs.mock_appraiser_output(candidate)
            a_messages: list[Any] = []
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
        await self._mark_exec(
            execution_id=appraiser_exec_id,
            status="completed",
            output_json=appraiser_out.model_dump_json(),
            completed=True,
        )
        await self._store_conversation(
            run_id=run_id,
            agent_name="appraiser",
            system_prompt=APPRAISER_SYSTEM_PROMPT,
            messages=a_messages,
        )
        dcf_result, dcf_error = await self._run_dcf(stock_args, appraiser_out)
        if dcf_result is None:
            await self._db(
                repo.update_ticker_run_completion,
                run_id=run_id,
                status="failed",
                final_rating=None,
                decision_type=None,
                recommended_action=None,
                final_verdict_json=None,
                error_message=dcf_error or "DCF failed",
            )
            arbiter_exec_id = await self._get_exec_id(run_id, "arbiter")
            if arbiter_exec_id is not None:
                await self._mark_exec(
                    execution_id=arbiter_exec_id, status="skipped", completed=True
                )
            await self._recompute(workflow_run_id)
            return
        await self._db(
            repo.insert_dcf_valuation,
            run_id=run_id,
            appraiser_agent_execution_id=appraiser_exec_id,
            dcf_result=dcf_result,
        )
        arbiter_exec_id = await self._get_exec_id(run_id, "arbiter")
        if arbiter_exec_id is None:
            return
        await self._mark_exec(
            execution_id=arbiter_exec_id, status="running", started=True
        )
        await self._recompute(workflow_run_id)
        if is_mock:
            await asyncio.sleep(5)
            arbiter_decision = mock_outputs.mock_arbiter_decision(
                candidate, is_existing_position=self._settings.is_existing_position
            )
            b_messages: list[Any] = []
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
                is_existing_position=self._settings.is_existing_position,
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
        await self._mark_exec(
            execution_id=arbiter_exec_id,
            status="completed",
            output_json=arbiter_decision.model_dump_json(),
            completed=True,
        )
        await self._store_conversation(
            run_id=run_id,
            agent_name="arbiter",
            system_prompt=ARBITER_SYSTEM_PROMPT,
            messages=b_messages,
        )
        verdict = verdict_from_decision(arbiter_decision)
        await self._db(
            repo.update_ticker_run_completion,
            run_id=run_id,
            status="completed",
            final_rating=str(verdict.rating.value),
            decision_type="arbiter",
            recommended_action=verdict.recommended_action,
            final_verdict_json=verdict.model_dump_json(),
            error_message=None,
        )
        await self._recompute(workflow_run_id)

    async def _run_dcf(
        self, stock_args: StockRunArgs, appraiser_out: Any
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
                return None, str(exc)

        return await asyncio.to_thread(_sync_dcf)
