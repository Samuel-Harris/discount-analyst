from __future__ import annotations

from pydantic import BaseModel, Field

from discount_analyst.shared.schemas.surveyor import KeyMetrics, SurveyorCandidate


class BusinessModel(BaseModel):
    """How the company creates, delivers, and captures value."""

    products_and_services: str = Field(
        description="Primary products/services and what customers pay for."
    )
    customer_segments: str = Field(
        description="Who the core customers are and any concentration risks."
    )
    unit_economics: str = Field(
        description="High-level gross margin and operating leverage characteristics."
    )
    competitive_positioning: str = Field(
        description="How the company is positioned versus peers and substitutes."
    )
    moat_and_durability: str = Field(
        description="Evidence for or against durable competitive advantages."
    )


class FinancialProfile(BaseModel):
    """Neutral financial profile with refreshed key metrics."""

    key_metrics_updated: KeyMetrics = Field(
        description="Updated key metrics for the current research pass."
    )
    revenue_and_growth_quality: str = Field(
        description="Revenue trajectory, growth drivers, and quality of growth."
    )
    profitability_and_margin_structure: str = Field(
        description="Margin profile, trends, and key drivers."
    )
    balance_sheet_and_liquidity: str = Field(
        description="Leverage, liquidity, and balance sheet resilience."
    )
    cash_flow_and_capital_intensity: str = Field(
        description="Cash conversion, capex profile, and capital needs."
    )
    capital_allocation: str = Field(
        description="Management capital allocation behavior and implications."
    )


class ManagementAssessment(BaseModel):
    """Assessment of leadership quality and governance."""

    leadership_and_execution: str = Field(
        description="Management quality, track record, and execution credibility."
    )
    governance_and_alignment: str = Field(
        description="Incentive alignment, ownership structure, and governance quality."
    )
    communication_quality: str = Field(
        description="Transparency and consistency of external communication."
    )
    key_concerns: str = Field(
        description="Most important management or governance concerns."
    )


class MarketNarrative(BaseModel):
    """How the market currently frames the business and what price implies."""

    dominant_narrative: str = Field(
        description="Current sell-side/media consensus framing."
    )
    bull_case_in_market: str = Field(
        description="Main bullish arguments currently reflected in discourse."
    )
    bear_case_in_market: str = Field(
        description="Main bearish arguments currently reflected in discourse."
    )
    expectations_implied_by_price: str = Field(
        description="What level of growth/margins the current price appears to imply."
    )
    where_expectations_may_be_wrong: str = Field(
        description="Potential mismatch between consensus expectations and evidence."
    )
    narrative_monitoring_signals: list[str] = Field(
        description="Forward indicators to track whether the market narrative shifts.",
    )


class DataGapsUpdate(BaseModel):
    """Explicit status update for Surveyor data gaps."""

    original_data_gaps: str = Field(
        description="Original SurveyorCandidate data_gaps text."
    )
    closed_gaps: list[str] = Field(
        description="Gaps that were closed in this research pass."
    )
    remaining_open_gaps: list[str] = Field(
        description="Gaps still unresolved after this research pass."
    )
    material_open_gaps: list[str] = Field(
        description="Open gaps likely to affect an investment decision materially."
    )


class DeepResearchReport(BaseModel):
    """Structured, neutral evidence report for one Surveyor candidate."""

    candidate: SurveyorCandidate = Field(
        description="Original Surveyor candidate context used for research."
    )
    executive_overview: str = Field(
        description="Neutral synthesis of what is known, unknown, and most relevant."
    )
    business_model: BusinessModel
    financial_profile: FinancialProfile
    management_assessment: ManagementAssessment
    market_narrative: MarketNarrative
    risks: list[str] = Field(description="Evidence-based business and financial risks.")
    potential_catalysts: list[str] = Field(
        description="Potential events that could change sentiment or fundamentals."
    )
    data_gaps_update: DataGapsUpdate
    source_notes: list[str] = Field(
        description=(
            "Short source notes with attribution, e.g. '10-K FY2024: revenue split'."
        ),
    )
