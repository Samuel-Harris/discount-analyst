"""Profiler agent stage: run profiler, persist output, refresh company name."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any, Protocol

from discount_analyst.adapters.persistence.models import AgentNameDb
from discount_analyst.adapters.simulation import (
    mock_conversation_messages,
    mock_outputs,
)
from discount_analyst.agents.runtime.ai_logging import AI_LOGFIRE
from discount_analyst.agents.common_prompts.current_date import with_current_date
from discount_analyst.agents.runtime.terminal_run import run_agent_with_terminal
from discount_analyst.agents.profiler.profiler import create_profiler_agent
from discount_analyst.agents.profiler.system_prompt import (
    SYSTEM_PROMPT as PROFILER_SYSTEM_PROMPT,
)
from discount_analyst.agents.profiler.user_prompt import create_profiler_user_prompt
from discount_analyst.agents.surveyor.schema import SurveyorCandidate
from discount_analyst.adapters.orchestration.llm_config import pipeline_llm_config

if TYPE_CHECKING:
    from discount_analyst.config.settings import Settings
    from discount_analyst.domain.model_selection.model_name import ModelName

_PROFILER_AGENT = "profiler"


class ProfilerStageHost(Protocol):
    @property
    def settings(self) -> Settings: ...

    async def get_exec_id(self, run_id: str, agent_name: str) -> str | None: ...

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

    async def recompute(self, workflow_run_id: str) -> None: ...

    async def store_agent_conversation(
        self,
        *,
        run_id: str,
        agent_name: str,
        system_prompt: str,
        messages: list[Any] | None = None,
        messages_json: str | None = None,
    ) -> None: ...

    async def update_ticker_run_company_name(
        self, run_id: str, company_name: str
    ) -> None: ...


class ProfilerStage:
    """Runs the profiler agent for a ticker lane and persists results via the host."""

    async def run(
        self,
        host: ProfilerStageHost,
        *,
        workflow_run_id: str,
        run_id: str,
        ticker: str,
        is_mock: bool,
    ) -> SurveyorCandidate:
        settings = host.settings
        profiler_exec_id = await host.get_exec_id(run_id, _PROFILER_AGENT)
        if profiler_exec_id is None:
            raise RuntimeError(f"Missing profiler execution for run {run_id}")
        llm = pipeline_llm_config(settings, is_mock=is_mock)
        await host.mark_exec(
            execution_id=profiler_exec_id,
            status="running",
            started=True,
            model_name=llm.model_name,
        )
        await host.recompute(workflow_run_id)
        AI_LOGFIRE.info(
            "Profiler stage started",
            agent_name=AgentNameDb.PROFILER,
            workflow_run_id=workflow_run_id,
            run_id=run_id,
            ticker=ticker,
            is_mock=is_mock,
        )
        mock_msgs_json: str | None = None
        if is_mock:
            await asyncio.sleep(5)
            profiler_output = mock_outputs.mock_profiler_output(ticker=ticker)
            messages = None
            mock_msgs_json = mock_conversation_messages.profiler_messages_json(
                ticker=ticker
            )
        else:
            ai_cfg = llm.ai_models_config
            if ai_cfg is None:
                raise RuntimeError("Profiler LLM config missing for non-mock run")
            outcome = await run_agent_with_terminal(
                settings=settings,
                session_id=profiler_exec_id,
                build_agent=lambda t: create_profiler_agent(
                    ai_models_config=ai_cfg,
                    use_perplexity=settings.use_perplexity,
                    use_mcp_financial_data=settings.use_mcp_financial_data,
                    terminal=t,
                ),
                user_prompt=create_profiler_user_prompt(ticker),
                usage_limits=ai_cfg.model.usage_limits,
            )
            profiler_output = outcome.output
            messages = list(outcome.all_messages)
            mock_msgs_json = None
        await host.mark_exec(
            execution_id=profiler_exec_id,
            status="completed",
            output_json=profiler_output.model_dump_json(),
            completed=True,
        )
        await host.store_agent_conversation(
            run_id=run_id,
            agent_name=_PROFILER_AGENT,
            system_prompt=with_current_date(PROFILER_SYSTEM_PROMPT),
            messages=messages,
            messages_json=mock_msgs_json,
        )
        await host.update_ticker_run_company_name(
            run_id=run_id,
            company_name=profiler_output.candidate.company_name,
        )
        AI_LOGFIRE.info(
            "Profiler stage completed",
            agent_name=AgentNameDb.PROFILER,
            workflow_run_id=workflow_run_id,
            run_id=run_id,
            ticker=ticker,
        )
        return profiler_output.candidate
