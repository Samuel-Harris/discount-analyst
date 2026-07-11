"""Pre-Researcher candidate admission gate for ticker lanes."""

from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING, Any, Protocol

from discount_analyst.adapters.persistence.crud.candidate_snapshots import (
    update_candidate_snapshot_gate_results,
)
from discount_analyst.adapters.persistence.crud.run_executions import (
    get_candidate_snapshot_id_for_run,
    update_ticker_run_completion,
    update_ticker_run_ticker,
)
from discount_analyst.adapters.persistence.models import AgentNameDb
from discount_analyst.agents.runtime.ai_logging import AI_LOGFIRE
from discount_analyst.agents.surveyor.schema import (
    SurveyorCandidate,
    SurveyorLaneContext,
)
from discount_analyst.application.decisions.builders import (
    build_data_quality_rejection,
    verdict_from_decision,
)
from discount_analyst.adapters.market_data.candidate_gates import validate_candidate
from discount_analyst.application.candidates.gate_results import (
    CandidateGateResult,
    PassedCandidateGate,
    RejectedCandidateGate,
)

if TYPE_CHECKING:
    from discount_analyst.config.settings import Settings
    from discount_analyst.domain.model_selection.model_name import ModelName

_LANE_AGENT_NAMES = (
    AgentNameDb.RESEARCHER.value,
    AgentNameDb.STRATEGIST.value,
    AgentNameDb.SENTINEL.value,
    AgentNameDb.APPRAISER.value,
)


class CandidateGateStageHost(Protocol):
    @property
    def settings(self) -> Settings: ...

    async def db(self, fn: Any, *args: Any, **kwargs: Any) -> Any: ...

    async def recompute(self, workflow_run_id: str) -> None: ...

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


class CandidateGateStage:
    """Admits a candidate to the Researcher lane or completes a gate rejection."""

    async def admit(
        self,
        host: CandidateGateStageHost,
        *,
        workflow_run_id: str,
        run_id: str,
        candidate: SurveyorCandidate,
        is_mock: bool,
        is_existing_position: bool,
    ) -> SurveyorLaneContext | None:
        gate_result = await self._run_gate(
            host,
            run_id=run_id,
            candidate=candidate,
            is_mock=is_mock,
        )
        await self._persist_gate_result(host, run_id=run_id, gate_result=gate_result)

        if isinstance(gate_result, RejectedCandidateGate):
            await self._apply_rejection(
                host,
                workflow_run_id=workflow_run_id,
                run_id=run_id,
                candidate=candidate,
                gate_result=gate_result,
                is_existing_position=is_existing_position,
            )
            return None

        await self._apply_resolved_ticker(
            host,
            run_id=run_id,
            candidate=candidate,
            gate_result=gate_result,
        )
        return gate_result.lane_context

    async def _run_gate(
        self,
        host: CandidateGateStageHost,
        *,
        run_id: str,
        candidate: SurveyorCandidate,
        is_mock: bool,
    ) -> CandidateGateResult:
        if is_mock:
            return PassedCandidateGate(
                source_ticker=candidate.ticker,
                resolved_ticker=candidate.ticker,
                resolution_notes="Mock run: gate skipped.",
                is_actively_trading=True,
                data_source="mock",
                lane_context=candidate.to_lane_context(),
            )
        return await validate_candidate(
            candidate,
            fmp_api_key=host.settings.fmp.api_key,
            eodhd_api_key=host.settings.eodhd.api_key,
            eodhd_disabled=host.settings.eodhd.disabled,
        )

    async def _persist_gate_result(
        self,
        host: CandidateGateStageHost,
        *,
        run_id: str,
        gate_result: CandidateGateResult,
    ) -> None:
        snapshot_id = await host.db(get_candidate_snapshot_id_for_run, run_id=run_id)
        if snapshot_id is None:
            return
        await host.db(
            update_candidate_snapshot_gate_results,
            snapshot_id=snapshot_id,
            gate_result=gate_result,
        )

    async def _apply_resolved_ticker(
        self,
        host: CandidateGateStageHost,
        *,
        run_id: str,
        candidate: SurveyorCandidate,
        gate_result: PassedCandidateGate,
    ) -> None:
        if gate_result.resolved_ticker == candidate.ticker:
            return
        await host.db(
            update_ticker_run_ticker,
            run_id=run_id,
            ticker=gate_result.resolved_ticker,
        )

    async def _apply_rejection(
        self,
        host: CandidateGateStageHost,
        *,
        workflow_run_id: str,
        run_id: str,
        candidate: SurveyorCandidate,
        gate_result: RejectedCandidateGate,
        is_existing_position: bool,
    ) -> None:
        AI_LOGFIRE.info(
            "Applying data quality rejection verdict",
            workflow_run_id=workflow_run_id,
            run_id=run_id,
            ticker=candidate.ticker,
        )
        for agent_name in _LANE_AGENT_NAMES:
            execution_id = await host.get_exec_id(run_id, agent_name)
            if execution_id is not None:
                await host.mark_exec(
                    execution_id=execution_id,
                    status="skipped",
                    completed=True,
                )
        rejection = build_data_quality_rejection(
            candidate.to_lane_context(),
            gate_failure_reason=gate_result.gate_failure_reason,
            is_existing_position=is_existing_position,
            decision_date=date.today().isoformat(),
        )
        verdict = verdict_from_decision(rejection)
        await host.db(
            update_ticker_run_completion,
            run_id=run_id,
            status="completed",
            final_rating=str(verdict.rating.value),
            decision_type="data_quality_rejection",
            recommended_action=verdict.recommended_action,
            final_verdict_json=verdict.model_dump_json(),
            error_message=None,
        )
        await host.recompute(workflow_run_id)
