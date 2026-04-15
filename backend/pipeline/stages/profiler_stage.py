"""Profiler agent stage: run profiler, persist output, refresh company name."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

import logfire

from backend.dev import mock_conversation_messages, mock_outputs
from backend.pipeline.ports import ProfilerStagePort
from discount_analyst.agents.common.streamed_agent_run import run_streamed_agent
from discount_analyst.agents.profiler.profiler import create_profiler_agent
from discount_analyst.agents.profiler.system_prompt import (
    SYSTEM_PROMPT as PROFILER_SYSTEM_PROMPT,
)
from discount_analyst.agents.profiler.user_prompt import create_profiler_user_prompt
from discount_analyst.agents.surveyor.schema import SurveyorCandidate
from discount_analyst.config.ai_models_config import AIModelsConfig

if TYPE_CHECKING:
    from backend.settings.config import DashboardSettings

_PROFILER_AGENT = "profiler"


class ProfilerStage:
    """Runs the profiler agent for a ticker lane and persists results via a port."""

    async def run(
        self,
        port: ProfilerStagePort,
        settings: DashboardSettings,
        *,
        workflow_run_id: str,
        run_id: str,
        ticker: str,
        is_mock: bool,
    ) -> SurveyorCandidate:
        profiler_exec_id = await port.get_agent_execution_id(run_id, _PROFILER_AGENT)
        if profiler_exec_id is None:
            raise RuntimeError(f"Missing profiler execution for run {run_id}")
        await port.mark_agent_execution(
            execution_id=profiler_exec_id, status="running", started=True
        )
        await port.recompute_workflow_status(workflow_run_id)
        logfire.info(
            "Profiler stage started",
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
            ai_cfg = AIModelsConfig(model_name=settings.default_model)
            agent = create_profiler_agent(
                ai_models_config=ai_cfg,
                use_perplexity=settings.use_perplexity,
                use_mcp_financial_data=settings.use_mcp_financial_data,
            )
            outcome = await run_streamed_agent(
                agent=agent,
                user_prompt=create_profiler_user_prompt(ticker),
                usage_limits=ai_cfg.model.usage_limits,
            )
            profiler_output = outcome.output
            messages = list(outcome.all_messages)
            mock_msgs_json = None
        await port.mark_agent_execution(
            execution_id=profiler_exec_id,
            status="completed",
            output_json=profiler_output.model_dump_json(),
            completed=True,
        )
        await port.store_agent_conversation(
            run_id=run_id,
            agent_name=_PROFILER_AGENT,
            system_prompt=PROFILER_SYSTEM_PROMPT,
            messages=messages,
            messages_json=mock_msgs_json,
        )
        await port.update_ticker_run_company_name(
            run_id=run_id,
            company_name=profiler_output.candidate.company_name,
        )
        logfire.info(
            "Profiler stage completed",
            workflow_run_id=workflow_run_id,
            run_id=run_id,
            ticker=ticker,
        )
        return profiler_output.candidate
