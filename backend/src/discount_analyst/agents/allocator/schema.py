"""Allocator LLM input and proposal contracts.

These schemas are self-contained so the Allocator package does not import
lower stage schemas. Application code packs compact evidence from those
stages and retains ``source_run_id`` for the audit record.
"""

from datetime import date
from typing import Annotated, Literal

from pydantic import BaseModel, Field, model_validator

from discount_analyst.domain.allocations.invariants import (
    validate_ordered_weight_range,
    validate_portfolio_weight_totals,
)
from discount_analyst.domain.allocations.policy import AllocationPolicy
from discount_analyst.domain.allocations.snapshot import CurrentPortfolioSnapshot
from discount_analyst.domain.decisions.investment_rating import InvestmentRating


class CompactResearcherEvidence(BaseModel):
    customer_segments: str
    risks: tuple[str, ...]


class CompactStrategistEvidence(BaseModel):
    thesis_summary: str
    conviction: Literal["Low", "Medium", "High"]
    thesis_risks: tuple[str, ...]
    permanent_loss_scenarios: tuple[str, ...]


class CompactSentinelEvidence(BaseModel):
    customer_or_supplier_concentration: str
    red_flag_verdict: Literal["Clear", "Monitor", "Serious concern"]
    reservations: bool
    material_data_gaps: str


class CompactAppraiserEvidence(BaseModel):
    current_price: float
    expected_value: float
    p10: float
    p90: float
    margin_of_safety_base_pct: float
    data_quality: Literal["High", "Medium", "Low"]


class AllocatorLaneIdentity(BaseModel):
    ticker: str
    company_name: str
    is_existing_position: bool
    current_weight_pct: float = Field(ge=0, le=100)
    sector: str
    industry: str
    policy: AllocationPolicy
    rating: InvestmentRating


class RatingTableLaneEvidence(BaseModel):
    decision_kind: Literal["rating_table"] = "rating_table"
    identity: AllocatorLaneIdentity
    researcher: CompactResearcherEvidence
    strategist: CompactStrategistEvidence
    sentinel: CompactSentinelEvidence
    appraiser: CompactAppraiserEvidence


class SentinelRejectionLaneEvidence(BaseModel):
    decision_kind: Literal["sentinel_rejection"] = "sentinel_rejection"
    identity: AllocatorLaneIdentity
    rejection_reason: str
    researcher: CompactResearcherEvidence
    strategist: CompactStrategistEvidence
    sentinel: CompactSentinelEvidence


class DataQualityRejectionLaneEvidence(BaseModel):
    decision_kind: Literal["data_quality_rejection"] = "data_quality_rejection"
    identity: AllocatorLaneIdentity
    rejection_reason: str


AllocatorLaneEvidence = Annotated[
    RatingTableLaneEvidence
    | SentinelRejectionLaneEvidence
    | DataQualityRejectionLaneEvidence,
    Field(discriminator="decision_kind"),
]


class AllocatorInput(BaseModel):
    allocation_date: date
    snapshot: CurrentPortfolioSnapshot
    lanes: tuple[AllocatorLaneEvidence, ...]

    @model_validator(mode="after")
    def validate_lane_tickers(self) -> AllocatorInput:
        seen: dict[str, str] = {}
        for lane in self.lanes:
            ticker = lane.identity.ticker
            key = ticker.casefold()
            previous = seen.get(key)
            if previous is not None:
                msg = (
                    "Allocator input tickers must be unique case-insensitively; "
                    f"{previous!r} and {ticker!r} collide."
                )
                raise ValueError(msg)
            seen[key] = ticker
        return self


class ProposedPosition(BaseModel):
    ticker: str
    target_weight_pct: float = Field(ge=0, le=100)
    acceptable_weight_low_pct: float = Field(ge=0, le=100)
    acceptable_weight_high_pct: float = Field(ge=0, le=100)
    rationale: str


class ProposedCash(BaseModel):
    target_weight_pct: float = Field(ge=0, le=100)
    acceptable_weight_low_pct: float = Field(ge=0, le=100)
    acceptable_weight_high_pct: float = Field(ge=0, le=100)
    rationale: str


class ProposedSharedRiskCluster(BaseModel):
    label: str
    member_tickers: tuple[str, ...]
    mechanism: str
    allocation_effect: str


class AllocatorProposal(BaseModel):
    allocation_date: date
    positions: tuple[ProposedPosition, ...]
    cash: ProposedCash
    shared_risk_clusters: tuple[ProposedSharedRiskCluster, ...]
    portfolio_rationale: str

    @model_validator(mode="after")
    def validate_proposal_shape(self) -> AllocatorProposal:
        seen: dict[str, str] = {}
        for position in self.positions:
            key = position.ticker.casefold()
            previous = seen.get(key)
            if previous is not None:
                msg = (
                    "Proposal tickers must be unique case-insensitively; "
                    f"{previous!r} and {position.ticker!r} collide."
                )
                raise ValueError(msg)
            seen[key] = position.ticker
            validate_ordered_weight_range(
                low_pct=position.acceptable_weight_low_pct,
                target_pct=position.target_weight_pct,
                high_pct=position.acceptable_weight_high_pct,
                label=f"Proposed position {position.ticker!r}",
            )
        validate_ordered_weight_range(
            low_pct=self.cash.acceptable_weight_low_pct,
            target_pct=self.cash.target_weight_pct,
            high_pct=self.cash.acceptable_weight_high_pct,
            label="Proposed cash",
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
        _validate_proposal_clusters(self.shared_risk_clusters)
        return self


def _validate_proposal_clusters(
    clusters: tuple[ProposedSharedRiskCluster, ...],
) -> None:
    seen_labels: dict[str, str] = {}
    for cluster in clusters:
        label_key = cluster.label.casefold()
        previous = seen_labels.get(label_key)
        if previous is not None:
            msg = (
                "Shared-risk cluster labels must be unique; "
                f"{previous!r} and {cluster.label!r} collide."
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
