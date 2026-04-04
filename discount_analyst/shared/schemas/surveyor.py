from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field


class Exchange(StrEnum):
    LSE = "LSE"
    AIM = "AIM"
    NYSE = "NYSE"
    NASDAQ = "NASDAQ"


class Currency(StrEnum):
    GBP = "GBP"
    USD = "USD"


class StockCategory(StrEnum):
    VALUE = "value"
    GROWTH = "growth"


class EthicalExclusionFilter(StrEnum):
    DEFENCE_AND_MILITARY = "Defence and military"
    CIVILIAN_FIREARMS = "Civilian firearms"
    FOSSIL_FUELS = "Fossil fuels"
    TOBACCO_AND_NICOTINE = "Tobacco and nicotine"
    GAMBLING = "Gambling"
    PRIVATE_PRISONS_AND_DETENTION = "Private prisons and detention"
    PREDATORY_CONSUMER_FINANCE = "Predatory consumer finance"


class EthicalExclusionBasis(StrEnum):
    CONFIRMED_DATA = "Confirmed data"
    PRECAUTIONARY = "Precautionary — data unavailable"


class KeyMetrics(BaseModel):
    """Core financial metrics for evaluating a candidate.

    Use null for any metric that cannot be found or calculated.
    Never fabricate numbers - a null with an explanation in data_gaps
    is always preferable to a guess.
    """

    trailing_pe: float | None = Field(
        default=None, description="Trailing twelve-month price-to-earnings ratio."
    )
    ev_ebit: float | None = Field(
        default=None, description="Enterprise value to EBIT ratio."
    )
    price_to_book: float | None = Field(
        default=None, description="Price-to-book ratio."
    )
    revenue_growth_3y_cagr_pct: float | None = Field(
        default=None,
        description="Revenue CAGR over the last 3 fiscal years, as a percentage.",
    )
    free_cash_flow_yield_pct: float | None = Field(
        default=None,
        description=(
            "Free cash flow yield as a percentage of market cap. "
            "Calculate from operating cash flow minus capex, divided by market cap."
        ),
    )
    net_debt_to_ebitda: float | None = Field(
        default=None,
        description="Net debt / EBITDA. Negative values indicate a net cash position.",
    )
    piotroski_f_score: int | None = Field(
        default=None,
        ge=0,
        le=9,
        description=(
            "Piotroski F-Score (0-9). Use FMP's Financial Score endpoint "
            "which provides this pre-computed. Will typically be null for "
            "UK-listed stocks as FMP coverage is US-centric."
        ),
    )
    altman_z_score: float | None = Field(
        default=None,
        description=(
            "Altman Z-Score. Use FMP's Financial Score endpoint which "
            "bundles this with the Piotroski score. Above 2.99 suggests "
            "safety; below 1.81 suggests distress. Will typically be null "
            "for UK-listed stocks."
        ),
    )
    insider_buying_last_6m: bool | None = Field(
        default=None,
        description=(
            "Whether insiders have made open-market purchases in the last "
            "6 months. Use FMP insider trading tools or EODHD "
            "get_insider_transactions for US stocks. For UK stocks, use "
            "Perplexity web search for RNS announcements."
        ),
    )


class SurveyorCandidate(BaseModel):
    """A single stock candidate surfaced by the Surveyor agent."""

    ticker: str = Field(
        description=(
            "Primary ticker symbol. For UK stocks use the exchange suffix "
            "where needed, e.g. 'ABCD.L'."
        ),
    )
    company_name: str
    exchange: Exchange
    currency: Currency
    market_cap_local: int = Field(
        description="Market cap in the local currency as an integer."
    )
    market_cap_display: str = Field(
        description="Human-readable market cap, e.g. '£145M' or '$320M'."
    )
    sector: str
    industry: str
    analyst_coverage_count: int | None = Field(
        default=None,
        description=(
            "Number of sell-side analysts covering the stock. Infer by "
            "counting distinct analysts from FMP's analyst estimates "
            "endpoint, or from Perplexity web search. This is an estimate, "
            "not an exact count."
        ),
    )
    key_metrics: KeyMetrics
    rationale: str = Field(
        description=(
            "3-6 sentences explaining why this stock merits further analysis. "
            "Reference specific signals and cite numbers, not vague claims."
        ),
    )
    red_flags: str = Field(
        description=(
            "Honestly note any concerns: customer concentration, litigation, "
            "key-person risk, accounting quirks, thin liquidity, etc. "
            "Say 'None identified' only if genuinely nothing was found."
        ),
    )
    data_gaps: str = Field(
        description=(
            "List any metrics that could not be found or verified, and why. "
            "e.g. 'Piotroski and Altman Z-Score unavailable - UK-listed stock "
            "not covered by FMP Financial Score endpoint.'"
        ),
    )


class EthicalExclusion(BaseModel):
    """A stock rejected on ethical grounds before financial evaluation."""

    ticker: str = Field(
        description=(
            "Primary ticker symbol. For UK stocks use the exchange suffix "
            "where needed, e.g. 'ABCD.L'."
        ),
    )
    company_name: str
    triggered_filter: EthicalExclusionFilter = Field(
        description="The specific ethical filter that caused this stock to be excluded."
    )
    evidence: str = Field(
        description=(
            "The specific evidence used to trigger this filter: e.g. SIC code, "
            "segment revenue figure, business description language, or news source. "
            "Be concrete — cite the source and the data point."
        ),
    )
    revenue_exposure_pct: float | None = Field(
        default=None,
        description=(
            "Estimated percentage of revenue derived from the excluded sector, "
            "if segment data was available. Null if unavailable."
        ),
    )
    exclusion_basis: EthicalExclusionBasis = Field(
        description=(
            "Whether the exclusion was based on confirmed segment revenue data, "
            "or a precautionary assumption because the revenue breakdown could "
            "not be verified."
        ),
    )


class SurveyorOutput(BaseModel):
    """Complete output from a single Surveyor run."""

    candidates: list[SurveyorCandidate] = Field(
        min_length=10,
        description=(
            "Ranked list of candidates. Must contain at least 10. Aim for "
            "15-25, but do not pad - a shorter list of strong candidates is "
            "better than a diluted one."
        ),
    )
    ethical_exclusions: list[EthicalExclusion] = Field(
        default_factory=list[EthicalExclusion],
        description=(
            "Stocks rejected on ethical grounds before financial evaluation. "
            "Always populate this field — use an empty list if no stocks were "
            "excluded, so that the absence of exclusions is itself auditable. "
            "Each entry must record which filter triggered, the evidence used, "
            "and whether the exclusion was based on confirmed data or a "
            "precautionary assumption due to missing segment data."
        ),
    )
