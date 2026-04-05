"""Serialisable run records written under scripts/outputs."""

from pydantic import AliasChoices, BaseModel, ConfigDict, Field

from discount_analyst.agents.appraiser.schema import AppraiserOutput
from discount_analyst.agents.sentinel.schema import EvaluationReport
from discount_analyst.agents.researcher.schema import DeepResearchReport
from discount_analyst.agents.strategist.schema import MispricingThesis
from discount_analyst.agents.surveyor.schema import SurveyorOutput
from discount_analyst.valuation.data_types import DCFAnalysisResult


class TurnUsage(BaseModel):
    """Usage stats for one model-response turn within a run."""

    turn: int = Field(ge=1)
    input_tokens: int = Field(ge=0)
    output_tokens: int = Field(ge=0)
    cache_write_tokens: int = Field(default=0, ge=0)
    cache_read_tokens: int = Field(default=0, ge=0)
    total_tokens: int = Field(ge=0)
    cumulative_input_tokens: int = Field(ge=0)
    cumulative_output_tokens: int = Field(ge=0)
    cumulative_total_tokens: int = Field(ge=0)


def default_turn_usage_list() -> list[TurnUsage]:
    return []


class AppraiserRunOutput(BaseModel):
    """Complete serialisable record for one model run written to outputs/."""

    model_config = ConfigDict(populate_by_name=True)

    ticker: str
    model_name: str
    risk_free_rate: float
    appraiser: AppraiserOutput = Field(
        validation_alias=AliasChoices("market_analyst", "appraiser"),
    )
    dcf_result: DCFAnalysisResult | None = None
    dcf_error: str | None = None
    elapsed_s: float
    input_tokens: int
    output_tokens: int
    cache_write_tokens: int
    cache_read_tokens: int
    tool_calls: int
    turn_usage: list[TurnUsage] = Field(default_factory=default_turn_usage_list)
    source_surveyor_report: str
    source_candidate_index: int = Field(ge=0)
    source_researcher_report: str
    source_strategist_report: str
    source_sentinel_report: str


class SurveyorRunOutput(BaseModel):
    """Complete serialisable record for one Surveyor run written to outputs/."""

    model_name: str
    elapsed_s: float
    input_tokens: int
    output_tokens: int
    turn_usage: list[TurnUsage] = Field(default_factory=default_turn_usage_list)
    output: SurveyorOutput


class ResearcherRunOutput(BaseModel):
    """Complete serialisable record for one Researcher run written to outputs/."""

    ticker: str
    model_name: str
    source_surveyor_report: str
    source_candidate_index: int = Field(ge=0)
    elapsed_s: float
    input_tokens: int
    output_tokens: int
    cache_write_tokens: int
    cache_read_tokens: int
    tool_calls: int
    turn_usage: list[TurnUsage] = Field(default_factory=default_turn_usage_list)
    output: DeepResearchReport


class StrategistRunOutput(BaseModel):
    """Complete serialisable record for one Strategist run written to outputs/."""

    ticker: str
    model_name: str
    source_surveyor_report: str
    source_candidate_index: int = Field(ge=0)
    source_researcher_report: str
    elapsed_s: float
    input_tokens: int
    output_tokens: int
    cache_write_tokens: int
    cache_read_tokens: int
    tool_calls: int
    turn_usage: list[TurnUsage] = Field(default_factory=default_turn_usage_list)
    output: MispricingThesis


class SentinelRunOutput(BaseModel):
    """Complete serialisable record for one Sentinel run written to outputs/."""

    ticker: str
    model_name: str
    source_surveyor_report: str
    source_candidate_index: int = Field(ge=0)
    source_researcher_report: str
    source_strategist_report: str
    elapsed_s: float
    input_tokens: int
    output_tokens: int
    cache_write_tokens: int
    cache_read_tokens: int
    tool_calls: int
    turn_usage: list[TurnUsage] = Field(default_factory=default_turn_usage_list)
    output: EvaluationReport
