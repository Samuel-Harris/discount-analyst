"""Schema-valid placeholder outputs for dashboard mock mode."""

from __future__ import annotations

import random
from datetime import date

from discount_analyst.agents.appraiser.schema import (
    AppraiserOutput,
    ValuationMethod,
    ValuationMethodResult,
)
from discount_analyst.domain.valuation.intrinsic_value_distribution import (
    IntrinsicValueDistribution,
)
from discount_analyst.agents.profiler.schema import ProfilerOutput
from discount_analyst.agents.researcher.schema import (
    BusinessModel,
    DataGapsUpdate,
    DeepResearchReport,
    FinancialProfile,
    ManagementAssessment,
    MarketNarrative,
)
from discount_analyst.agents.sentinel.schema import (
    EvaluationReport,
    OverallRedFlagVerdict,
    QuestionAssessment,
    RedFlagScreen,
    ThesisVerdict,
)
from discount_analyst.agents.strategist.schema import MispricingThesis
from discount_analyst.agents.surveyor.schema import (
    Currency,
    Exchange,
    KeyMetrics,
    SurveyorCandidate,
    SurveyorLaneContext,
    SurveyorOutput,
)
from discount_analyst.application.decisions.builders import build_rating_table_decision
from discount_analyst.domain.decisions.schema import RatingTableDecision
from discount_analyst.domain.decisions.margin_of_safety import MarginOfSafetyAssessment

# Fifteen distinct discovery names for mock surveyor output (LSE-style tickers).
_DEFAULT_DISCOVERY: list[tuple[str, str]] = [
    ("DISC.L", "Discount Analyst Mock Group plc"),
    ("ALPH.L", "Alpha Horizon Consumer plc"),
    ("BETA.L", "Beta Industrial Holdings plc"),
    ("GAMM.L", "Gamma Digital Services plc"),
    ("DELT.L", "Delta Logistics Network plc"),
    ("EPSL.L", "Epsilon Energy Transition plc"),
    ("ZETA.L", "Zeta Specialty Finance plc"),
    ("ETAL.L", "Eta Healthcare Innovation plc"),
    ("THET.L", "Theta Telecom Infrastructure plc"),
    ("IOTA.L", "Iota Building Products plc"),
    ("KAPP.L", "Kappa Food & Beverage plc"),
    ("LAMB.L", "Lambda Aerospace Components plc"),
    ("MUON.L", "Muon Semiconductor plc"),
    ("NUCL.L", "Nucleus Biotech Research plc"),
    ("OMEG.L", "Omega Urban Regeneration plc"),
]

_MOCK_DISCOVERY_COUNT = 15


def mock_key_metrics() -> KeyMetrics:
    return KeyMetrics()


def mock_surveyor_candidate(
    *, ticker: str, company_name: str | None = None
) -> SurveyorCandidate:
    name = company_name or f"{ticker} Mock Co"
    return SurveyorCandidate(
        ticker=ticker,
        company_name=name,
        exchange=Exchange.LSE,
        currency=Currency.GBP,
        market_cap_local=150_000_000,
        market_cap_display="£150M",
        sector="Mock sector",
        industry="Mock industry",
        analyst_coverage_count=2,
        key_metrics=mock_key_metrics(),
        rationale="Mock rationale with concrete placeholder metrics for dashboard testing.",
        red_flags="None identified in mock.",
        data_gaps="Mock data gaps entry.",
    )


def mock_surveyor_output(*, extra_tickers: list[str] | None = None) -> SurveyorOutput:
    """Lightweight discovery payload for dashboard mock mode (validation bypassed).

    Returns exactly :data:`_MOCK_DISCOVERY_COUNT` candidates. When ``extra_tickers``
    is set, those tickers are listed first (deduplicated), then defaults fill the
    remainder so seeds and tests can pin portfolio symbols while keeping fifteen
    rows for the UI.
    """
    merged: list[tuple[str, str | None]] = []
    seen: set[str] = set()

    if extra_tickers:
        for raw in extra_tickers:
            key = raw.casefold()
            if key in seen:
                continue
            seen.add(key)
            merged.append((raw, None))
            if len(merged) >= _MOCK_DISCOVERY_COUNT:
                break

    if len(merged) < _MOCK_DISCOVERY_COUNT:
        for ticker, name in _DEFAULT_DISCOVERY:
            key = ticker.casefold()
            if key in seen:
                continue
            seen.add(key)
            merged.append((ticker, name))
            if len(merged) >= _MOCK_DISCOVERY_COUNT:
                break

    candidates = [
        mock_surveyor_candidate(ticker=t, company_name=n)
        if n is not None
        else mock_surveyor_candidate(ticker=t)
        for t, n in merged
    ]
    return SurveyorOutput.model_construct(candidates=candidates)


def mock_surveyor_dashboard_discoveries(
    portfolio_fold: set[str], *, limit: int = 3
) -> SurveyorOutput:
    """Short mock Surveyor output for the dashboard pipeline (no live LLM).

    Returns up to ``limit`` discovery candidates from :data:`_DEFAULT_DISCOVERY`
    whose tickers are **not** in ``portfolio_fold``. Tickers already in the
    launch portfolio get an immediate Profiler run instead, so they are omitted
    here — this list is only names Surveyor is treated as having "found" beyond
    the portfolio, which each become their own ``entry_path="surveyor"`` lane.

    Capping the count keeps mock workflows fast enough to finish while still
    producing multiple Surveyor branches for the graph UI.
    """
    candidates: list[SurveyorCandidate] = []
    for ticker, name in _DEFAULT_DISCOVERY:
        if ticker.casefold() in portfolio_fold:
            continue
        candidates.append(mock_surveyor_candidate(ticker=ticker, company_name=name))
        if len(candidates) >= limit:
            break
    return SurveyorOutput.model_construct(candidates=candidates)


def mock_profiler_output(*, ticker: str) -> ProfilerOutput:
    return ProfilerOutput(candidate=mock_surveyor_candidate(ticker=ticker))


def _as_lane_context(
    candidate: SurveyorCandidate | SurveyorLaneContext,
) -> SurveyorLaneContext:
    if isinstance(candidate, SurveyorLaneContext):
        return candidate
    return candidate.to_lane_context()


def mock_deep_research(
    candidate: SurveyorCandidate | SurveyorLaneContext,
) -> DeepResearchReport:
    lane_context = _as_lane_context(candidate)
    return DeepResearchReport(
        executive_overview="Mock executive overview.",
        business_model=BusinessModel(
            products_and_services="Mock products.",
            customer_segments="Mock customers.",
            unit_economics="Mock unit economics.",
            competitive_positioning="Mock positioning.",
            moat_and_durability="Mock moat.",
        ),
        financial_profile=FinancialProfile(
            key_metrics_updated=mock_key_metrics(),
            revenue_and_growth_quality="Mock revenue narrative.",
            profitability_and_margin_structure="Mock margins.",
            balance_sheet_and_liquidity="Mock balance sheet.",
            cash_flow_and_capital_intensity="Mock cash flow.",
            capital_allocation="Mock capital allocation.",
        ),
        management_assessment=ManagementAssessment(
            leadership_and_execution="Mock leadership.",
            governance_and_alignment="Mock governance.",
            communication_quality="Mock communication.",
            key_concerns="Mock concerns.",
        ),
        market_narrative=MarketNarrative(
            dominant_narrative="Mock dominant narrative.",
            bull_case_in_market="Mock bull case.",
            bear_case_in_market="Mock bear case.",
            expectations_implied_by_price="Mock expectations.",
            where_expectations_may_be_wrong="Mock mismatch.",
            narrative_monitoring_signals=["Mock signal one", "Mock signal two"],
        ),
        risks=["Mock risk one"],
        potential_catalysts=["Mock catalyst"],
        data_gaps_update=DataGapsUpdate(
            original_data_gaps=lane_context.data_gaps,
            closed_gaps=[],
            remaining_open_gaps=["Mock remaining gap"],
            material_open_gaps=[],
        ),
        source_notes=["Mock source note"],
    )


def mock_thesis(candidate: SurveyorCandidate | SurveyorLaneContext) -> MispricingThesis:
    lane_context = _as_lane_context(candidate)
    return MispricingThesis(
        ticker=lane_context.ticker,
        company_name=lane_context.company_name,
        mispricing_type="Mock mispricing",
        market_belief="Mock market belief.",
        mispricing_argument="Mock argument.",
        resolution_mechanism="Mock resolution.",
        falsification_conditions=["C1", "C2", "C3"],
        thesis_risks=["Mock thesis risk"],
        evaluation_questions=["Q1", "Q2", "Q3", "Q4", "Q5"],
        permanent_loss_scenarios=["PL1", "PL2"],
        conviction_level="Medium",
    )


def mock_sentinel_proceed_for_dashboard_lane(ticker: str) -> bool:
    """Return whether mock Sentinel should authorise valuation for this ticker.

    Deterministic from the ticker string (character-sum parity) so dashboard
    mock runs show a stable mix of pass and fail lanes without RNG coupling.
    """

    return sum(ord(ch) for ch in ticker.casefold()) % 2 == 0


def mock_sentinel_evaluation(
    *, candidate: SurveyorCandidate | SurveyorLaneContext, proceed: bool
) -> EvaluationReport:
    lane_context = _as_lane_context(candidate)
    proceed_verdicts = (
        ThesisVerdict.INTACT_PROCEED_TO_VALUATION,
        ThesisVerdict.INTACT_WITH_RESERVATIONS,
    )
    block_verdicts = (
        ThesisVerdict.WEAKENED_DO_NOT_PROCEED,
        ThesisVerdict.BROKEN_DO_NOT_PROCEED,
    )
    if proceed:
        thesis_verdict = random.choice(proceed_verdicts)
        red_verdict = random.choice(
            (OverallRedFlagVerdict.CLEAR, OverallRedFlagVerdict.MONITOR)
        )
    else:
        if random.random() < 0.5:
            thesis_verdict = random.choice(proceed_verdicts + block_verdicts)
            red_verdict = OverallRedFlagVerdict.SERIOUS_CONCERN
        else:
            thesis_verdict = random.choice(block_verdicts)
            red_verdict = random.choice(tuple(OverallRedFlagVerdict))

    questions_pool = [
        "Is the mispricing thesis still supported by recent trading updates?",
        "Do margins and cash conversion still align with the bull narrative?",
        "Has competitive intensity materially changed versus the thesis baseline?",
        "Are balance sheet covenants and liquidity still comfortable?",
        "Does management guidance still imply the resolution path assumed?",
    ]
    verdict_opts = (
        "Supports thesis",
        "Neutral",
        "Weakens thesis",
        "Breaks thesis",
    )
    n_q = random.randint(1, min(5, len(questions_pool)))
    question_assessments = [
        QuestionAssessment(
            question=questions_pool[i],
            evidence=random.choice(
                (
                    "Recent filings and newsflow are broadly consistent with the thesis.",
                    "Mixed signals: some metrics improved, others lag expectations.",
                    "Evidence is thin; several material claims remain unverified.",
                )
            ),
            verdict=random.choice(verdict_opts),
            confidence=random.choice(("Low", "Medium", "High")),
        )
        for i in random.sample(range(len(questions_pool)), n_q)
    ]

    gov = random.choice(
        (
            "None",
            "Low-level related-party disclosure only",
            "Elevated governance scrutiny",
        )
    )
    bs_stress = random.choice(("Low", "Moderate", "Elevated"))
    conc = random.choice(("Low", "Moderate", "High"))
    acct = random.choice(
        ("Acceptable", "Requires monitoring", "Elevated estimation risk")
    )
    rpt = random.choice(
        (
            "None noted",
            "Immaterial related-party activity",
            "Material related-party exposure",
        )
    )
    lit = random.choice(("Low", "Moderate", "Elevated"))

    return EvaluationReport(
        ticker=lane_context.ticker,
        company_name=lane_context.company_name,
        question_assessments=question_assessments,
        red_flag_screen=RedFlagScreen(
            governance_concerns=gov,
            balance_sheet_stress=bs_stress,
            customer_or_supplier_concentration=conc,
            accounting_quality=acct,
            related_party_transactions=rpt,
            litigation_or_regulatory_risk=lit,
            overall_red_flag_verdict=red_verdict,
        ),
        thesis_verdict=thesis_verdict,
        verdict_rationale=random.choice(
            (
                "Mock sentinel rationale: question-level evidence and red-flag "
                "screen jointly support the chosen thesis verdict.",
                "Mock sentinel rationale: red-flag concentration outweighs "
                "supportive question assessments.",
                "Mock sentinel rationale: thesis questions are mixed; verdict "
                "reflects the dominant balance of evidence in mock mode.",
            )
        ),
        material_data_gaps=random.choice(
            (
                "None material in mock.",
                "Segment margin disclosure remains a load-bearing gap.",
                "Working capital seasonality not fully explained in public data.",
            )
        ),
        caveats=random.sample(
            (
                "Mock caveat: illustrative dashboard output only.",
                "Mock caveat: numbers are placeholders, not investment advice.",
                "Mock caveat: rerun for production-grade diligence.",
            ),
            k=random.randint(1, 3),
        ),
    )


def mock_appraiser_output(
    candidate: SurveyorCandidate | SurveyorLaneContext,
) -> AppraiserOutput:
    lane_context = _as_lane_context(candidate)
    current_price = 3.0
    return AppraiserOutput(
        ticker=lane_context.ticker,
        company_name=lane_context.company_name,
        valuation_date=date.today().isoformat(),
        summary="Mock Appraiser distribution for dashboard testing.",
        valuation_distribution=IntrinsicValueDistribution(
            currency=lane_context.currency.value,
            current_share_price=current_price,
            expected_intrinsic_value=3.8,
            p10_intrinsic_value=2.6,
            p25_intrinsic_value=3.1,
            p50_intrinsic_value=3.6,
            p75_intrinsic_value=4.2,
            p90_intrinsic_value=5.0,
            distribution_method="mock_scenario_weighting",
            distribution_reasoning="Mock downside/base/upside range.",
        ),
        methods=[
            ValuationMethodResult(
                method=ValuationMethod.SCENARIO_WEIGHTING,
                role="primary",
                value_per_share=3.8,
                low_value_per_share=2.6,
                high_value_per_share=5.0,
                weight_pct=70.0,
                key_assumptions=["Mock growth and margin assumptions."],
                evidence_summary=["Mock research evidence."],
                sanity_checks=["Mock distribution is monotonic."],
                limitations=["Mock output only."],
            ),
            ValuationMethodResult(
                method=ValuationMethod.COMPARABLE_MULTIPLES,
                role="cross_check",
                value_per_share=3.5,
                low_value_per_share=3.0,
                high_value_per_share=4.1,
                weight_pct=30.0,
                key_assumptions=["Mock peer multiple range."],
                evidence_summary=["Mock peer set."],
                sanity_checks=["Mock selected multiple within peer range."],
                limitations=["Peer set is illustrative."],
            ),
        ],
        key_value_drivers=["Mock revenue growth", "Mock margin expansion"],
        downside_risks_to_value=["Mock execution risk"],
        upside_drivers_to_value=["Mock catalyst delivery"],
        data_quality="Medium",
        caveats=["Mock valuation only."],
    )


def mock_rating_table_gate_evaluation(
    candidate: SurveyorCandidate | SurveyorLaneContext,
    *,
    thesis_verdict: ThesisVerdict = ThesisVerdict.INTACT_PROCEED_TO_VALUATION,
) -> EvaluationReport:
    """Minimal Sentinel output for deterministic mock rating-table rows."""
    lane_context = _as_lane_context(candidate)
    return EvaluationReport(
        ticker=lane_context.ticker,
        company_name=lane_context.company_name,
        question_assessments=[
            QuestionAssessment(
                question="Q1",
                evidence="Mock evidence.",
                verdict="Supports thesis",
                confidence="High",
            )
        ],
        red_flag_screen=RedFlagScreen(
            governance_concerns="",
            balance_sheet_stress="",
            customer_or_supplier_concentration="",
            accounting_quality="",
            related_party_transactions="",
            litigation_or_regulatory_risk="",
            overall_red_flag_verdict=OverallRedFlagVerdict.CLEAR,
        ),
        thesis_verdict=thesis_verdict,
        verdict_rationale="Mock sentinel verdict.",
        material_data_gaps="",
        caveats=[],
    )


def mock_rating_table_decision(
    candidate: SurveyorCandidate | SurveyorLaneContext,
    *,
    is_existing_position: bool,
    thesis: MispricingThesis | None = None,
    evaluation: EvaluationReport | None = None,
) -> RatingTableDecision:
    """Deterministic rating-table decision for mock dashboard runs (no LLM)."""
    lane_context = _as_lane_context(candidate)
    th = thesis or mock_thesis(candidate)
    ev = evaluation or mock_rating_table_gate_evaluation(candidate)
    appraiser_out = mock_appraiser_output(candidate)
    mos = MarginOfSafetyAssessment.from_distribution(
        appraiser_out.valuation_distribution
    )
    return build_rating_table_decision(
        lane_context=lane_context,
        thesis=th,
        evaluation=ev,
        margin_of_safety=mos,
        is_existing_position=is_existing_position,
        decision_date=date.today().isoformat(),
    )
