"""Per-ticker lane stages: researcher through appraiser and final rating."""

from __future__ import annotations

import asyncio
from datetime import date
from typing import TYPE_CHECKING, Any, Protocol

from backend.db.models import AgentNameDb, ExecutionStatusDb
from backend.dev import mock_conversation_messages, mock_outputs
from backend.pipeline.llm_config import PipelineLlmConfig, pipeline_llm_config
from discount_analyst.agents.appraiser.appraiser import create_appraiser_agent
from discount_analyst.agents.appraiser.schema import AppraiserInput, AppraiserOutput
from discount_analyst.agents.appraiser.system_prompt import (
    SYSTEM_PROMPT as APPRAISER_SYSTEM_PROMPT,
)
from discount_analyst.agents.appraiser.user_prompt import (
    create_user_prompt as create_appraiser_user_prompt,
)
from discount_analyst.agents.common.ai_logging import AI_LOGFIRE
from discount_analyst.agents.common.terminal_run import run_agent_with_terminal
from discount_analyst.agents.common_prompts.current_date import with_current_date
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
from discount_analyst.agents.strategist.schema import MispricingThesis
from discount_analyst.agents.strategist.strategist import create_strategist_agent
from discount_analyst.agents.strategist.system_prompt import (
    SYSTEM_PROMPT as STRATEGIST_SYSTEM_PROMPT,
)
from discount_analyst.agents.strategist.user_prompt import (
    create_user_prompt as create_strategist_user_prompt,
)
from discount_analyst.agents.surveyor.schema import SurveyorLaneContext
from discount_analyst.integrations.terminal import TerminalRuntimeConfig
from discount_analyst.pipeline.builders import (
    build_rating_table_decision,
    build_sentinel_rejection,
    verdict_from_decision,
)
from backend.crud.run_executions import update_ticker_run_completion
from discount_analyst.models.model_name import ModelName
from discount_analyst.rating.margin_of_safety import MarginOfSafetyAssessment

if TYPE_CHECKING:
    from common.config import Settings


class TickerLaneStageHost(Protocol):
    @property
    def settings(self) -> Settings: ...

    async def db(self, fn: Any, *args: Any, **kwargs: Any) -> Any: ...

    async def recompute(self, workflow_run_id: str) -> None: ...

    def cached_terminal_runtime(self) -> TerminalRuntimeConfig: ...

    async def get_exec_id(self, run_id: str, agent_name: str) -> str | None: ...

    async def get_agent_status(self, run_id: str, agent_name: str) -> str | None: ...

    async def load_completed_agent_output_json(
        self, *, run_id: str, agent_name: str
    ) -> str | None: ...

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
    ) -> None: ...

    async def complete_exec_with_conversation(
        self,
        *,
        execution_id: str,
        system_prompt: str,
        output_json: str | None,
        messages: list[Any] | None = None,
        messages_json: str | None = None,
    ) -> None: ...


class TickerLaneStage:
    """Runs researcher → strategist → sentinel → appraiser for one ticker lane."""

    async def run_downstream_from_researcher(
        self,
        host: TickerLaneStageHost,
        *,
        workflow_run_id: str,
        run_id: str,
        lane_context: SurveyorLaneContext,
        is_mock: bool,
        is_existing_position: bool,
    ) -> None:
        research_out, thesis, evaluation = await self.run_research_strategist_sentinel(
            host,
            workflow_run_id=workflow_run_id,
            run_id=run_id,
            lane_context=lane_context,
            is_mock=is_mock,
        )
        if not sentinel_proceeds_to_valuation(evaluation):
            AI_LOGFIRE.info(
                "Sentinel gate did not pass; skipping valuation stages",
                workflow_run_id=workflow_run_id,
                run_id=run_id,
                ticker=lane_context.ticker,
            )
            await self.apply_sentinel_rejection(
                host,
                workflow_run_id=workflow_run_id,
                run_id=run_id,
                thesis=thesis,
                evaluation=evaluation,
                is_existing_position=is_existing_position,
            )
            return
        AI_LOGFIRE.info(
            "Sentinel gate passed; continuing to appraiser",
            workflow_run_id=workflow_run_id,
            run_id=run_id,
            ticker=lane_context.ticker,
        )
        await self.run_appraiser_final_rating(
            host,
            workflow_run_id=workflow_run_id,
            run_id=run_id,
            lane_context=lane_context,
            research_out=research_out,
            thesis=thesis,
            evaluation=evaluation,
            is_mock=is_mock,
            is_existing_position=is_existing_position,
        )

    async def run_research_strategist_sentinel(
        self,
        host: TickerLaneStageHost,
        *,
        workflow_run_id: str,
        run_id: str,
        lane_context: SurveyorLaneContext,
        is_mock: bool,
    ) -> tuple[Any, Any, Any]:
        llm = pipeline_llm_config(host.settings, is_mock=is_mock)
        research_out = await self._run_researcher(
            host,
            workflow_run_id=workflow_run_id,
            run_id=run_id,
            lane_context=lane_context,
            is_mock=is_mock,
            llm=llm,
        )
        thesis = await self._run_strategist(
            host,
            workflow_run_id=workflow_run_id,
            run_id=run_id,
            lane_context=lane_context,
            research_out=research_out,
            is_mock=is_mock,
            llm=llm,
        )
        evaluation = await self._run_sentinel(
            host,
            workflow_run_id=workflow_run_id,
            run_id=run_id,
            lane_context=lane_context,
            research_out=research_out,
            thesis=thesis,
            is_mock=is_mock,
            llm=llm,
        )
        return research_out, thesis, evaluation

    async def _run_researcher(
        self,
        host: TickerLaneStageHost,
        *,
        workflow_run_id: str,
        run_id: str,
        lane_context: SurveyorLaneContext,
        is_mock: bool,
        llm: PipelineLlmConfig,
    ) -> DeepResearchReport:
        research_exec_id = await host.get_exec_id(run_id, AgentNameDb.RESEARCHER.value)
        if research_exec_id is None:
            raise RuntimeError(f"Missing researcher execution for run {run_id}")
        research_status = await host.get_agent_status(
            run_id, AgentNameDb.RESEARCHER.value
        )
        if research_status == ExecutionStatusDb.COMPLETED.value:
            research_json = await host.load_completed_agent_output_json(
                run_id=run_id, agent_name=AgentNameDb.RESEARCHER.value
            )
            if research_json is None:
                raise RuntimeError(f"Missing completed researcher output for {run_id}")
            AI_LOGFIRE.info(
                "Researcher stage already completed; skipping",
                agent_name=AgentNameDb.RESEARCHER,
                workflow_run_id=workflow_run_id,
                run_id=run_id,
                ticker=lane_context.ticker,
            )
            return DeepResearchReport.model_validate_json(research_json)

        await host.mark_exec(
            execution_id=research_exec_id,
            status="running",
            started=True,
            model_name=llm.model_name,
        )
        await host.recompute(workflow_run_id)
        AI_LOGFIRE.info(
            "Researcher stage started",
            agent_name=AgentNameDb.RESEARCHER,
            workflow_run_id=workflow_run_id,
            run_id=run_id,
            ticker=lane_context.ticker,
            is_mock=is_mock,
        )
        r_mock_json: str | None = None
        if is_mock:
            await asyncio.sleep(5)
            research_out = mock_outputs.mock_deep_research(lane_context)
            r_messages = None
            r_mock_json = mock_conversation_messages.researcher_messages_json(
                ticker=lane_context.ticker
            )
        else:
            ai_cfg = llm.ai_models_config
            if ai_cfg is None:
                raise RuntimeError("Researcher LLM config missing for non-mock run")
            outcome = await run_agent_with_terminal(
                settings=host.settings,
                session_id=research_exec_id,
                runtime=host.cached_terminal_runtime(),
                build_agent=lambda t: create_researcher_agent(
                    ai_cfg,
                    use_perplexity=host.settings.use_perplexity,
                    use_mcp_financial_data=host.settings.use_mcp_financial_data,
                    terminal=t,
                ),
                user_prompt=create_researcher_user_prompt(lane_context=lane_context),
                usage_limits=ai_cfg.model.usage_limits,
            )
            research_out = outcome.output
            r_messages = list(outcome.all_messages)
            r_mock_json = None
        await host.complete_exec_with_conversation(
            execution_id=research_exec_id,
            system_prompt=with_current_date(RESEARCHER_SYSTEM_PROMPT),
            output_json=research_out.model_dump_json(),
            messages=r_messages,
            messages_json=r_mock_json,
        )
        AI_LOGFIRE.info(
            "Researcher stage completed",
            agent_name=AgentNameDb.RESEARCHER,
            workflow_run_id=workflow_run_id,
            run_id=run_id,
            ticker=lane_context.ticker,
        )
        return research_out

    async def _run_strategist(
        self,
        host: TickerLaneStageHost,
        *,
        workflow_run_id: str,
        run_id: str,
        lane_context: SurveyorLaneContext,
        research_out: DeepResearchReport,
        is_mock: bool,
        llm: PipelineLlmConfig,
    ) -> MispricingThesis:
        strategist_exec_id = await host.get_exec_id(
            run_id, AgentNameDb.STRATEGIST.value
        )
        if strategist_exec_id is None:
            raise RuntimeError(f"Missing strategist execution for run {run_id}")
        strategist_status = await host.get_agent_status(
            run_id, AgentNameDb.STRATEGIST.value
        )
        if strategist_status == ExecutionStatusDb.COMPLETED.value:
            thesis_json = await host.load_completed_agent_output_json(
                run_id=run_id, agent_name=AgentNameDb.STRATEGIST.value
            )
            if thesis_json is None:
                raise RuntimeError(f"Missing completed strategist output for {run_id}")
            AI_LOGFIRE.info(
                "Strategist stage already completed; skipping",
                agent_name=AgentNameDb.STRATEGIST,
                workflow_run_id=workflow_run_id,
                run_id=run_id,
                ticker=lane_context.ticker,
            )
            return MispricingThesis.model_validate_json(thesis_json)

        await host.mark_exec(
            execution_id=strategist_exec_id,
            status="running",
            started=True,
            model_name=llm.model_name,
        )
        await host.recompute(workflow_run_id)
        AI_LOGFIRE.info(
            "Strategist stage started",
            agent_name=AgentNameDb.STRATEGIST,
            workflow_run_id=workflow_run_id,
            run_id=run_id,
            ticker=lane_context.ticker,
            is_mock=is_mock,
        )
        s_mock_json: str | None = None
        if is_mock:
            await asyncio.sleep(5)
            thesis = mock_outputs.mock_thesis(lane_context)
            s_messages = None
            s_mock_json = mock_conversation_messages.strategist_messages_json(
                ticker=lane_context.ticker
            )
        else:
            ai_cfg = llm.ai_models_config
            if ai_cfg is None:
                raise RuntimeError("Strategist LLM config missing for non-mock run")
            outcome = await run_agent_with_terminal(
                settings=host.settings,
                session_id=strategist_exec_id,
                runtime=host.cached_terminal_runtime(),
                build_agent=lambda t: create_strategist_agent(ai_cfg, terminal=t),
                user_prompt=create_strategist_user_prompt(
                    lane_context=lane_context, deep_research=research_out
                ),
                usage_limits=ai_cfg.model.usage_limits,
            )
            thesis = outcome.output
            s_messages = list(outcome.all_messages)
            s_mock_json = None
        await host.complete_exec_with_conversation(
            execution_id=strategist_exec_id,
            system_prompt=with_current_date(STRATEGIST_SYSTEM_PROMPT),
            output_json=thesis.model_dump_json(),
            messages=s_messages,
            messages_json=s_mock_json,
        )
        AI_LOGFIRE.info(
            "Strategist stage completed",
            agent_name=AgentNameDb.STRATEGIST,
            workflow_run_id=workflow_run_id,
            run_id=run_id,
            ticker=lane_context.ticker,
        )
        return thesis

    async def _run_sentinel(
        self,
        host: TickerLaneStageHost,
        *,
        workflow_run_id: str,
        run_id: str,
        lane_context: SurveyorLaneContext,
        research_out: DeepResearchReport,
        thesis: MispricingThesis,
        is_mock: bool,
        llm: PipelineLlmConfig,
    ) -> SentinelEvaluationReport:
        sentinel_exec_id = await host.get_exec_id(run_id, AgentNameDb.SENTINEL.value)
        if sentinel_exec_id is None:
            raise RuntimeError(f"Missing sentinel execution for run {run_id}")
        sentinel_status = await host.get_agent_status(
            run_id, AgentNameDb.SENTINEL.value
        )
        if sentinel_status == ExecutionStatusDb.COMPLETED.value:
            evaluation_json = await host.load_completed_agent_output_json(
                run_id=run_id, agent_name=AgentNameDb.SENTINEL.value
            )
            if evaluation_json is None:
                raise RuntimeError(f"Missing completed sentinel output for {run_id}")
            AI_LOGFIRE.info(
                "Sentinel stage already completed; skipping",
                agent_name=AgentNameDb.SENTINEL,
                workflow_run_id=workflow_run_id,
                run_id=run_id,
                ticker=lane_context.ticker,
            )
            return SentinelEvaluationReport.model_validate_json(evaluation_json)

        await host.mark_exec(
            execution_id=sentinel_exec_id,
            status="running",
            started=True,
            model_name=llm.model_name,
        )
        await host.recompute(workflow_run_id)
        AI_LOGFIRE.info(
            "Sentinel stage started",
            agent_name=AgentNameDb.SENTINEL,
            workflow_run_id=workflow_run_id,
            run_id=run_id,
            ticker=lane_context.ticker,
            is_mock=is_mock,
        )
        n_mock_json: str | None = None
        if is_mock:
            await asyncio.sleep(5)
            evaluation = mock_outputs.mock_sentinel_evaluation(
                candidate=lane_context,
                proceed=mock_outputs.mock_sentinel_proceed_for_dashboard_lane(
                    lane_context.ticker
                ),
            )
            n_messages = None
            n_mock_json = mock_conversation_messages.sentinel_messages_json(
                ticker=lane_context.ticker
            )
        else:
            ai_cfg = llm.ai_models_config
            if ai_cfg is None:
                raise RuntimeError("Sentinel LLM config missing for non-mock run")
            outcome = await run_agent_with_terminal(
                settings=host.settings,
                session_id=sentinel_exec_id,
                runtime=host.cached_terminal_runtime(),
                build_agent=lambda t: create_sentinel_agent(ai_cfg, terminal=t),
                user_prompt=create_sentinel_user_prompt(
                    lane_context=lane_context,
                    deep_research=research_out,
                    thesis=thesis,
                ),
                usage_limits=ai_cfg.model.usage_limits,
            )
            evaluation = outcome.output
            n_messages = list(outcome.all_messages)
            n_mock_json = None
        await host.complete_exec_with_conversation(
            execution_id=sentinel_exec_id,
            system_prompt=with_current_date(SENTINEL_SYSTEM_PROMPT),
            output_json=evaluation.model_dump_json(),
            messages=n_messages,
            messages_json=n_mock_json,
        )
        AI_LOGFIRE.info(
            "Sentinel stage completed",
            agent_name=AgentNameDb.SENTINEL,
            workflow_run_id=workflow_run_id,
            run_id=run_id,
            ticker=lane_context.ticker,
        )
        return evaluation

    async def apply_sentinel_rejection(
        self,
        host: TickerLaneStageHost,
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
        for agent_name in ("appraiser",):
            execution_id = await host.get_exec_id(run_id, agent_name)
            if execution_id is not None:
                await host.mark_exec(
                    execution_id=execution_id, status="skipped", completed=True
                )
        rejection = build_sentinel_rejection(
            evaluation,
            thesis,
            is_existing_position=is_existing_position,
            decision_date=date.today().isoformat(),
        )
        verdict = verdict_from_decision(rejection)
        await host.db(
            update_ticker_run_completion,
            run_id=run_id,
            status="completed",
            final_rating=str(verdict.rating.value),
            decision_type="sentinel_rejection",
            recommended_action=verdict.recommended_action,
            final_verdict_json=verdict.model_dump_json(),
            error_message=None,
        )
        await host.recompute(workflow_run_id)

    async def run_appraiser_final_rating(
        self,
        host: TickerLaneStageHost,
        *,
        workflow_run_id: str,
        run_id: str,
        lane_context: SurveyorLaneContext,
        research_out: Any,
        thesis: Any,
        evaluation: Any,
        is_mock: bool,
        is_existing_position: bool,
    ) -> None:
        llm = pipeline_llm_config(host.settings, is_mock=is_mock)
        appraiser_exec_id = await host.get_exec_id(run_id, AgentNameDb.APPRAISER.value)
        if appraiser_exec_id is None:
            return
        appraiser_status = await host.get_agent_status(
            run_id, AgentNameDb.APPRAISER.value
        )
        if appraiser_status == ExecutionStatusDb.COMPLETED.value:
            appraiser_json = await host.load_completed_agent_output_json(
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
                ticker=lane_context.ticker,
            )
        else:
            await host.mark_exec(
                execution_id=appraiser_exec_id,
                status="running",
                started=True,
                model_name=llm.model_name,
            )
            await host.recompute(workflow_run_id)
            AI_LOGFIRE.info(
                "Appraiser stage started",
                agent_name=AgentNameDb.APPRAISER,
                workflow_run_id=workflow_run_id,
                run_id=run_id,
                ticker=lane_context.ticker,
                is_mock=is_mock,
            )
            appraiser_input = AppraiserInput(
                lane_context=lane_context,
                deep_research=research_out,
                thesis=thesis,
                evaluation=evaluation,
                risk_free_rate_pct=host.settings.risk_free_rate_pct,
            )
            a_mock_json: str | None = None
            if is_mock:
                await asyncio.sleep(5)
                appraiser_out = mock_outputs.mock_appraiser_output(lane_context)
                a_messages = None
                a_mock_json = mock_conversation_messages.appraiser_messages_json(
                    ticker=lane_context.ticker
                )
            else:
                ai_cfg = llm.ai_models_config
                if ai_cfg is None:
                    raise RuntimeError("Appraiser LLM config missing for non-mock run")
                outcome = await run_agent_with_terminal(
                    settings=host.settings,
                    session_id=appraiser_exec_id,
                    runtime=host.cached_terminal_runtime(),
                    build_agent=lambda t: create_appraiser_agent(
                        ai_cfg,
                        use_perplexity=host.settings.use_perplexity,
                        use_mcp_financial_data=host.settings.use_mcp_financial_data,
                        terminal=t,
                    ),
                    user_prompt=create_appraiser_user_prompt(
                        appraiser_input=appraiser_input
                    ),
                    usage_limits=ai_cfg.model.usage_limits,
                )
                appraiser_out = outcome.output
                a_messages = list(outcome.all_messages)
                a_mock_json = None
            await host.complete_exec_with_conversation(
                execution_id=appraiser_exec_id,
                system_prompt=with_current_date(APPRAISER_SYSTEM_PROMPT),
                output_json=appraiser_out.model_dump_json(),
                messages=a_messages,
                messages_json=a_mock_json,
            )
            AI_LOGFIRE.info(
                "Appraiser stage completed",
                agent_name=AgentNameDb.APPRAISER,
                workflow_run_id=workflow_run_id,
                run_id=run_id,
                ticker=lane_context.ticker,
            )

        if is_mock:
            await asyncio.sleep(5)
            rating_decision = mock_outputs.mock_rating_table_decision(
                lane_context,
                is_existing_position=is_existing_position,
                thesis=thesis,
                evaluation=evaluation,
            )
        else:
            mos = MarginOfSafetyAssessment.from_distribution(
                appraiser_out.valuation_distribution
            )
            rating_decision = build_rating_table_decision(
                lane_context=lane_context,
                thesis=thesis,
                evaluation=evaluation,
                margin_of_safety=mos,
                is_existing_position=is_existing_position,
                decision_date=date.today().isoformat(),
            )
        verdict = verdict_from_decision(rating_decision)
        await host.db(
            update_ticker_run_completion,
            run_id=run_id,
            status="completed",
            final_rating=str(verdict.rating.value),
            decision_type="rating_table",
            recommended_action=verdict.recommended_action,
            final_verdict_json=verdict.model_dump_json(),
            error_message=None,
        )
        await host.recompute(workflow_run_id)
        AI_LOGFIRE.info(
            "Deterministic rating table applied; ticker run finished",
            agent_name=AgentNameDb.APPRAISER,
            workflow_run_id=workflow_run_id,
            run_id=run_id,
            ticker=lane_context.ticker,
        )
