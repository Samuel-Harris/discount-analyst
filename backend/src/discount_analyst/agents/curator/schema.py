"""Curator LLM input and proposal contracts.

These schemas are self-contained so the Curator package does not import
lower stage schemas. Application code packs compact evidence from those
stages and retains ``source_run_id`` for the audit record.
"""

from datetime import date
from typing import Annotated, Literal

from pydantic import BaseModel, Field, model_validator

from discount_analyst.domain.allocations.invariants import (
    require_unique_casefold,
    validate_ordered_weight_range,
    validate_portfolio_weight_totals,
    validate_shared_risk_clusters,
)
from discount_analyst.domain.allocations.policy import AllocationPolicy
from discount_analyst.domain.allocations.snapshot import CurrentPortfolioSnapshot
from discount_analyst.domain.decisions.investment_rating import InvestmentRating


class CompactResearcherEvidence(BaseModel):
    customer_segments: str
    risks: tuple[str, ...]


class PackedMispricingThesis(BaseModel):
    """Field-identical copy of Strategist ``MispricingThesis`` for Curator input.

    Kept here so ``schema.py`` does not import the Strategist package.
    """

    ticker: str
    company_name: str
    mispricing_type: str
    market_belief: str
    mispricing_argument: str
    resolution_mechanism: str
    falsification_conditions: list[str]
    thesis_risks: list[str]
    evaluation_questions: list[str]
    permanent_loss_scenarios: list[str]
    conviction_level: Literal["Low", "Medium", "High"]


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


class CuratorLaneIdentity(BaseModel):
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
    identity: CuratorLaneIdentity
    live_thesis: PackedMispricingThesis
    researcher: CompactResearcherEvidence
    strategist: CompactStrategistEvidence
    sentinel: CompactSentinelEvidence
    appraiser: CompactAppraiserEvidence


class SentinelRejectionLaneEvidence(BaseModel):
    decision_kind: Literal["sentinel_rejection"] = "sentinel_rejection"
    identity: CuratorLaneIdentity
    live_thesis: PackedMispricingThesis
    rejection_reason: str
    researcher: CompactResearcherEvidence
    strategist: CompactStrategistEvidence
    sentinel: CompactSentinelEvidence


class DataQualityRejectionLaneEvidence(BaseModel):
    decision_kind: Literal["data_quality_rejection"] = "data_quality_rejection"
    identity: CuratorLaneIdentity
    rejection_reason: str
    live_thesis: PackedMispricingThesis | None = None


CuratorLaneEvidence = Annotated[
    RatingTableLaneEvidence
    | SentinelRejectionLaneEvidence
    | DataQualityRejectionLaneEvidence,
    Field(discriminator="decision_kind"),
]


class CuratorInput(BaseModel):
    allocation_date: date
    snapshot: CurrentPortfolioSnapshot
    lanes: tuple[CuratorLaneEvidence, ...]

    @model_validator(mode="after")
    def validate_lane_tickers(self) -> CuratorInput:
        require_unique_casefold(
            (lane.identity.ticker for lane in self.lanes),
            item_kind="Curator input tickers",
        )
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


class CuratorProposal(BaseModel):
    allocation_date: date
    positions: tuple[ProposedPosition, ...]
    cash: ProposedCash
    shared_risk_clusters: tuple[ProposedSharedRiskCluster, ...]
    portfolio_rationale: str

    @model_validator(mode="after")
    def validate_proposal_shape(self) -> CuratorProposal:
        require_unique_casefold(
            (position.ticker for position in self.positions),
            item_kind="Proposal tickers",
        )
        for position in self.positions:
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
        validate_shared_risk_clusters(self.shared_risk_clusters)
        return self
