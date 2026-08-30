"""Persisted workflow-level portfolio allocation."""

from datetime import date

from pydantic import BaseModel, Field, model_validator

from discount_analyst.domain.allocations.actions import RebalanceAction
from discount_analyst.domain.allocations.invariants import (
    validate_company_weight_caps,
    validate_forced_zero_weights,
    validate_ordered_weight_range,
    validate_portfolio_weight_totals,
    validate_retain_or_reduce_weights,
)
from discount_analyst.domain.allocations.policy import AllocationPolicy


class AllocationPosition(BaseModel):
    ticker: str
    company_name: str
    source_run_id: str
    is_existing_position: bool
    current_weight_pct: float = Field(ge=0, le=100)
    policy: AllocationPolicy
    target_weight_pct: float = Field(ge=0, le=100)
    acceptable_weight_low_pct: float = Field(ge=0, le=100)
    acceptable_weight_high_pct: float = Field(ge=0, le=100)
    action: RebalanceAction
    rationale: str


class CashAllocation(BaseModel):
    current_weight_pct: float = Field(ge=0, le=100)
    target_weight_pct: float = Field(ge=0, le=100)
    acceptable_weight_low_pct: float = Field(ge=0, le=100)
    acceptable_weight_high_pct: float = Field(ge=0, le=100)
    rationale: str


class SharedRiskCluster(BaseModel):
    label: str
    member_tickers: tuple[str, ...]
    mechanism: str
    allocation_effect: str


class PortfolioAllocation(BaseModel):
    allocation_date: date
    positions: tuple[AllocationPosition, ...]
    cash: CashAllocation
    shared_risk_clusters: tuple[SharedRiskCluster, ...]
    portfolio_rationale: str

    @model_validator(mode="after")
    def validate_allocation(self) -> PortfolioAllocation:
        seen_tickers: dict[str, str] = {}
        for position in self.positions:
            key = position.ticker.casefold()
            previous = seen_tickers.get(key)
            if previous is not None:
                msg = (
                    "Allocation tickers must be unique case-insensitively; "
                    f"{previous!r} and {position.ticker!r} collide."
                )
                raise ValueError(msg)
            seen_tickers[key] = position.ticker
            validate_ordered_weight_range(
                low_pct=position.acceptable_weight_low_pct,
                target_pct=position.target_weight_pct,
                high_pct=position.acceptable_weight_high_pct,
                label=f"Position {position.ticker!r}",
            )
            if position.policy.kind == "forced_zero":
                validate_forced_zero_weights(
                    low_pct=position.acceptable_weight_low_pct,
                    target_pct=position.target_weight_pct,
                    high_pct=position.acceptable_weight_high_pct,
                    ticker=position.ticker,
                )
            elif position.policy.kind == "retain_or_reduce":
                validate_retain_or_reduce_weights(
                    target_pct=position.target_weight_pct,
                    high_pct=position.acceptable_weight_high_pct,
                    current_weight_pct=position.policy.current_weight_pct,
                    ticker=position.ticker,
                )
        validate_ordered_weight_range(
            low_pct=self.cash.acceptable_weight_low_pct,
            target_pct=self.cash.target_weight_pct,
            high_pct=self.cash.acceptable_weight_high_pct,
            label="Cash",
        )
        validate_company_weight_caps(
            [
                (
                    position.company_name,
                    position.target_weight_pct,
                    position.acceptable_weight_high_pct,
                )
                for position in self.positions
            ]
        )
        validate_portfolio_weight_totals(
            equity_target_pcts=[
                position.target_weight_pct for position in self.positions
            ],
            cash_target_pct=self.cash.target_weight_pct,
            range_low_pcts=[
                *(position.acceptable_weight_low_pct for position in self.positions),
                self.cash.acceptable_weight_low_pct,
            ],
            range_high_pcts=[
                *(position.acceptable_weight_high_pct for position in self.positions),
                self.cash.acceptable_weight_high_pct,
            ],
        )
        _validate_risk_clusters(self.shared_risk_clusters, frozenset(seen_tickers))
        return self


def _validate_risk_clusters(
    clusters: tuple[SharedRiskCluster, ...],
    known_ticker_keys: frozenset[str],
) -> None:
    seen_labels: dict[str, str] = {}
    for cluster in clusters:
        label_key = cluster.label.casefold()
        previous_label = seen_labels.get(label_key)
        if previous_label is not None:
            msg = (
                "Shared-risk cluster labels must be unique; "
                f"{previous_label!r} and {cluster.label!r} collide."
            )
            raise ValueError(msg)
        seen_labels[label_key] = cluster.label
        if len(cluster.member_tickers) < 2:
            msg = (
                f"Shared-risk cluster {cluster.label!r} must name at least "
                "two member tickers."
            )
            raise ValueError(msg)
        seen_members: dict[str, str] = {}
        for ticker in cluster.member_tickers:
            member_key = ticker.casefold()
            previous_member = seen_members.get(member_key)
            if previous_member is not None:
                msg = (
                    f"Shared-risk cluster {cluster.label!r} repeats ticker "
                    f"{previous_member!r}."
                )
                raise ValueError(msg)
            seen_members[member_key] = ticker
            if member_key not in known_ticker_keys:
                msg = (
                    f"Shared-risk cluster {cluster.label!r} names unknown "
                    f"ticker {ticker!r}."
                )
                raise ValueError(msg)
