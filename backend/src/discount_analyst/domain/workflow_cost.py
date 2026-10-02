"""USD figures for a dashboard workflow, summed from recorded agent attempts."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_EVEN
from typing import Literal

_CENT = Decimal("0.01")
AGENT_COST_ORDER: tuple[str, ...] = (
    "surveyor",
    "profiler",
    "researcher",
    "strategist",
    "sentinel",
    "appraiser",
    "curator",
)


@dataclass(frozen=True, slots=True)
class AttemptCost:
    """One captured model spend. Unpriced attempts keep ``cost_usd`` unset."""

    cost_usd: Decimal | None


@dataclass(frozen=True, slots=True)
class RecordedAttempt:
    agent_execution_id: str
    agent_name: str
    successful: bool
    cost_usd: Decimal | None


@dataclass(frozen=True, slots=True)
class CostFigure:
    state: Literal["amount", "unknown"]
    amount_usd: Decimal | None

    @classmethod
    def amount(cls, value: Decimal) -> CostFigure:
        return cls(state="amount", amount_usd=value)

    @classmethod
    def unknown(cls) -> CostFigure:
        return cls(state="unknown", amount_usd=None)

    def amount_text(self) -> str | None:
        if self.state == "unknown" or self.amount_usd is None:
            return None
        return f"{self.amount_usd:.2f}"


@dataclass(frozen=True, slots=True)
class AgentTypeCost:
    agent_name: str
    cost: CostFigure


@dataclass(frozen=True, slots=True)
class WorkflowCostSummary:
    total: CostFigure
    successful: CostFigure
    unsuccessful: CostFigure
    by_agent: tuple[AgentTypeCost, ...]
    execution_figures: tuple[tuple[str, CostFigure], ...]

    def figure_for_execution(self, execution_id: str) -> CostFigure:
        for recorded_id, figure in self.execution_figures:
            if recorded_id == execution_id:
                return figure
        raise KeyError(execution_id)


def summarise_workflow_cost(
    attempts: list[RecordedAttempt],
    *,
    is_mock: bool,
    execution_ids: list[str],
) -> WorkflowCostSummary:
    """Sum attempt spend. Mock runs are $0.00 even when attempt rows exist."""
    if is_mock:
        zero = CostFigure.amount(Decimal("0.00"))
        return WorkflowCostSummary(
            total=zero,
            successful=zero,
            unsuccessful=zero,
            by_agent=tuple(
                AgentTypeCost(agent_name=agent_name, cost=zero)
                for agent_name in AGENT_COST_ORDER
            ),
            execution_figures=tuple(
                (execution_id, zero) for execution_id in execution_ids
            ),
        )

    return WorkflowCostSummary(
        total=_figure([attempt.cost_usd for attempt in attempts]),
        successful=_figure(
            [attempt.cost_usd for attempt in attempts if attempt.successful]
        ),
        unsuccessful=_figure(
            [attempt.cost_usd for attempt in attempts if not attempt.successful]
        ),
        by_agent=tuple(
            AgentTypeCost(
                agent_name=agent_name,
                cost=_figure(
                    [
                        attempt.cost_usd
                        for attempt in attempts
                        if attempt.agent_name == agent_name
                    ]
                ),
            )
            for agent_name in AGENT_COST_ORDER
        ),
        execution_figures=tuple(
            (
                execution_id,
                _figure(
                    [
                        attempt.cost_usd
                        for attempt in attempts
                        if attempt.agent_execution_id == execution_id
                    ]
                ),
            )
            for execution_id in execution_ids
        ),
    )


def _figure(amounts: list[Decimal | None]) -> CostFigure:
    if not amounts:
        return CostFigure.amount(Decimal("0.00"))
    priced = [amount for amount in amounts if amount is not None]
    if not priced:
        return CostFigure.unknown()
    total = sum(priced, start=Decimal(0)).quantize(_CENT, rounding=ROUND_HALF_EVEN)
    return CostFigure.amount(total)
