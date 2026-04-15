"""Schema-valid placeholder outputs for dashboard mock mode."""

from __future__ import annotations

import random
from datetime import date

from discount_analyst.agents.appraiser.schema import AppraiserOutput
from discount_analyst.agents.arbiter.schema import (
    ArbiterDecision,
    ArbiterRationale,
    MarginOfSafetyAssessment,
    MarginOfSafetyVerdict,
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
    SurveyorOutput,
)
from discount_analyst.rating import InvestmentRating
from discount_analyst.valuation.data_types import DCFAnalysisResult
from discount_analyst.valuation.schema import StockAssumptions, StockData

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


def mock_deep_research(candidate: SurveyorCandidate) -> DeepResearchReport:
    return DeepResearchReport(
        candidate=candidate,
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
            original_data_gaps=candidate.data_gaps,
            closed_gaps=[],
            remaining_open_gaps=["Mock remaining gap"],
            material_open_gaps=[],
        ),
        source_notes=["Mock source note"],
    )


def mock_thesis(candidate: SurveyorCandidate) -> MispricingThesis:
    return MispricingThesis(
        ticker=candidate.ticker,
        company_name=candidate.company_name,
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
    *, candidate: SurveyorCandidate, proceed: bool
) -> EvaluationReport:
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
        ticker=candidate.ticker,
        company_name=candidate.company_name,
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


def mock_stock_data(candidate: SurveyorCandidate) -> StockData:
    return StockData(
        ticker=candidate.ticker,
        name=candidate.company_name,
        ebit=12_000_000.0,
        revenue=80_000_000.0,
        capital_expenditure=4_000_000.0,
        n_shares_outstanding=50_000_000.0,
        market_cap=150_000_000.0,
        gross_debt=20_000_000.0,
        gross_debt_last_year=22_000_000.0,
        net_debt=10_000_000.0,
        total_interest_expense=1_000_000.0,
        beta=1.1,
    )


def mock_stock_assumptions() -> StockAssumptions:
    return StockAssumptions(
        reasoning="Mock assumptions for dashboard DCF.",
        forecast_period_years=5,
        assumed_tax_rate=0.21,
        assumed_forecast_period_annual_revenue_growth_rate=0.08,
        assumed_perpetuity_cash_flow_growth_rate=0.025,
        assumed_ebit_margin=0.18,
        assumed_depreciation_and_amortization_rate=0.04,
        assumed_capex_rate=0.05,
        assumed_change_in_working_capital_rate=0.02,
    )


def mock_appraiser_output(candidate: SurveyorCandidate) -> AppraiserOutput:
    return AppraiserOutput(
        stock_data=mock_stock_data(candidate),
        stock_assumptions=mock_stock_assumptions(),
    )


def mock_dcf_result() -> DCFAnalysisResult:
    return DCFAnalysisResult(
        intrinsic_share_price=3.2,
        enterprise_value=180_000_000.0,
        equity_value=160_000_000.0,
    )


def mock_arbiter_rating_for_dashboard_lane(ticker: str) -> InvestmentRating:
    """Pick a stable ``InvestmentRating`` per ticker for mock Arbiter output.

    Random ratings made short mock runs look uniformly bearish; this cycles
    across all five levels using the same case-folded character-sum scheme as
    :func:`mock_sentinel_proceed_for_dashboard_lane`.
    """

    order: tuple[InvestmentRating, ...] = (
        InvestmentRating.STRONG_BUY,
        InvestmentRating.BUY,
        InvestmentRating.HOLD,
        InvestmentRating.SELL,
        InvestmentRating.STRONG_SELL,
    )
    bucket = sum(ord(ch) for ch in ticker.casefold()) % len(order)
    return order[bucket]


def mock_arbiter_decision(
    candidate: SurveyorCandidate, *, is_existing_position: bool
) -> ArbiterDecision:
    rating = mock_arbiter_rating_for_dashboard_lane(candidate.ticker)
    conviction = random.choice(("Low", "Medium", "High"))

    action_by_rating = {
        InvestmentRating.STRONG_BUY: (
            "Increase materially on weakness.",
            "Add aggressively while liquidity permits.",
        ),
        InvestmentRating.BUY: (
            "Accumulate on pullbacks.",
            "Add gradually within risk limits.",
        ),
        InvestmentRating.HOLD: (
            "Maintain sizing; reassess on new data.",
            "Hold pending clearer catalysts.",
        ),
        InvestmentRating.SELL: (
            "Trim exposure into strength.",
            "Reduce position size.",
        ),
        InvestmentRating.STRONG_SELL: (
            "Exit or hedge promptly.",
            "Close the position.",
        ),
    }
    recommended_action = random.choice(action_by_rating[rating])

    base = round(random.uniform(1.5, 120.0), 2)
    bear = round(base * random.uniform(0.55, 0.92), 2)
    bull = round(base * random.uniform(1.05, 1.45), 2)
    current = round(base * random.uniform(0.78, 1.12), 2)
    mos_pct = round((base - current) / base * 100.0, 1) if base else 0.0

    substantial: MarginOfSafetyVerdict = (
        "Substantial — price implies significant downside in market expectations"
    )
    moderate: MarginOfSafetyVerdict = "Moderate — meaningful upside but not exceptional"
    thin: MarginOfSafetyVerdict = "Thin — limited margin for error"
    none_mos: MarginOfSafetyVerdict = "None — stock appears fairly valued or overvalued"
    if mos_pct >= 12:
        mos_verdict = substantial
    elif mos_pct >= 3:
        mos_verdict = random.choice((substantial, moderate))
    elif mos_pct >= -5:
        mos_verdict = random.choice((moderate, thin))
    else:
        mos_verdict = random.choice((thin, none_mos))

    return ArbiterDecision(
        ticker=candidate.ticker,
        company_name=candidate.company_name,
        decision_date=date.today().isoformat(),
        is_existing_position=is_existing_position,
        rating=rating,
        recommended_action=recommended_action,
        conviction=conviction,
        margin_of_safety=MarginOfSafetyAssessment(
            current_price=current,
            bear_intrinsic_value=bear,
            base_intrinsic_value=base,
            bull_intrinsic_value=bull,
            margin_of_safety_base_pct=mos_pct,
            margin_of_safety_verdict=mos_verdict,
        ),
        rationale=ArbiterRationale(
            primary_driver=random.choice(
                (
                    "Valuation versus revised intrinsic range.",
                    "Thesis durability after latest operating evidence.",
                    "Balance sheet optionality versus peer set.",
                )
            ),
            supporting_factors=random.sample(
                (
                    "Cash conversion remains supportive.",
                    "Narrative dislocation still evident in multiples.",
                    "Catalyst path within a sensible horizon.",
                ),
                k=random.randint(1, 3),
            ),
            mitigating_factors=random.sample(
                (
                    "Macro sensitivity is non-trivial.",
                    "Execution risk on key initiatives.",
                    "Disclosure gaps on segment economics.",
                ),
                k=random.randint(1, 3),
            ),
            red_flag_disposition=random.choice(
                ("Acceptable", "Manageable with monitoring", "Elevated but priced")
            ),
            data_gap_disposition=random.choice(
                ("Monitor", "Close before sizing up", "Immaterial for the decision")
            ),
        ),
        thesis_expiry_note=random.choice(
            (
                "Revisit after the next two reporting periods.",
                "Mock expiry note: refresh thesis if guidance changes materially.",
                "Mock expiry note: reassess if the red-flag screen worsens.",
            )
        ),
    )
