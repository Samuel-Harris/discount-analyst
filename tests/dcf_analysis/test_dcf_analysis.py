from pydantic import BaseModel
from discount_analyst.valuation.dcf_analysis import DCFAnalysis
from discount_analyst.valuation.data_types import DCFAnalysisParameters
from discount_analyst.valuation.schema import StockAssumptions, StockData
import pytest

from discount_analyst.valuation.data_types import DCFAnalysisResult


class TestCase(BaseModel):
    id: str
    dcf_analysis_params: DCFAnalysisParameters

    expected_dcf_analysis_result: DCFAnalysisResult


TEST_CASES: list[TestCase] = [
    TestCase(
        id="Greggs plc.",
        dcf_analysis_params=DCFAnalysisParameters(
            stock_data=StockData(
                ticker="TEST",
                name="Test Company",
                ebit=195_300_000,
                revenue=2_014_400_000,
                total_interest_expense=5_400_000,
                gross_debt=35_000_000,
                gross_debt_last_year=35_000_000,
                net_debt=2_500_000,
                capital_expenditure=150_000_000,
                n_shares_outstanding=101_775_428,
                market_cap=1_710_000_000,
                beta=1.39,
            ),
            stock_assumptions=StockAssumptions(
                reasoning="Test assumptions for DCF analysis",
                forecast_period_years=7,
                assumed_tax_rate_pct=25.0,
                assumed_forecast_period_annual_revenue_growth_rate_pct=8.0,
                assumed_perpetuity_cash_flow_growth_rate_pct=2.5,
                assumed_ebit_margin_pct=9.7,
                assumed_depreciation_and_amortization_rate_pct=5.0,
                assumed_capex_rate_pct=7.5,
                assumed_change_in_working_capital_rate_pct=1.0,
            ),
            risk_free_rate_pct=4.0,
            expected_market_return_pct=10.0,
        ),
        expected_dcf_analysis_result=DCFAnalysisResult(
            intrinsic_share_price=12.933682545607047,
            enterprise_value=1318831076.6952868,
            equity_value=1316331076.6952868,
        ),
    ),
    TestCase(
        id="Alphabet Inc.",
        dcf_analysis_params=DCFAnalysisParameters(
            stock_data=StockData(
                ticker="TEST",
                name="Test Company",
                ebit=112_390_000_000,
                revenue=350_018_000_000,
                total_interest_expense=268_000_000,
                gross_debt=13_559_000_000,
                gross_debt_last_year=14_616_000_000,
                net_debt=-81_591_000_000,
                capital_expenditure=52_535_000_000,
                n_shares_outstanding=12_090_000_000,
                market_cap=3_050_000_000_000,
                beta=1.0,
            ),
            stock_assumptions=StockAssumptions(
                reasoning="Test assumptions for DCF analysis",
                forecast_period_years=10,
                assumed_tax_rate_pct=16.4,
                assumed_forecast_period_annual_revenue_growth_rate_pct=10.0,
                assumed_perpetuity_cash_flow_growth_rate_pct=3.0,
                assumed_ebit_margin_pct=32.1,
                assumed_depreciation_and_amortization_rate_pct=3.6,
                assumed_capex_rate_pct=15.0,
                assumed_change_in_working_capital_rate_pct=1.0,
            ),
            risk_free_rate_pct=3.96,
            expected_market_return_pct=8.0,
        ),
        expected_dcf_analysis_result=DCFAnalysisResult(
            intrinsic_share_price=166.89590990721538,
            enterprise_value=1936180550778.234,
            equity_value=2017771550778.234,
        ),
    ),
    TestCase(
        id="HSBC Holdings plc.",
        dcf_analysis_params=DCFAnalysisParameters(
            stock_data=StockData(
                ticker="TEST",
                name="Test Company",
                ebit=32_300_000_000,
                revenue=69_072_000_000,
                total_interest_expense=81_680_000_000,
                gross_debt=129_700_000_000,
                gross_debt_last_year=135_000_000_000,
                net_debt=-116_660_000_000,
                capital_expenditure=1_344_000_000,
                n_shares_outstanding=17_730_000_000,
                market_cap=167_960_000_000,
                beta=0.50,
            ),
            stock_assumptions=StockAssumptions(
                reasoning="Test assumptions for DCF analysis",
                forecast_period_years=5,
                assumed_tax_rate_pct=16.4,
                assumed_forecast_period_annual_revenue_growth_rate_pct=3.6,
                assumed_perpetuity_cash_flow_growth_rate_pct=2.5,
                assumed_ebit_margin_pct=46.7,
                assumed_depreciation_and_amortization_rate_pct=1.0,
                assumed_capex_rate_pct=2.0,
                assumed_change_in_working_capital_rate_pct=0.5,
            ),
            risk_free_rate_pct=4.15,
            expected_market_return_pct=9.0,
        ),
        expected_dcf_analysis_result=DCFAnalysisResult(
            intrinsic_share_price=13.229659223010318,
            enterprise_value=117901858023.97293,
            equity_value=234561858023.97293,
        ),
    ),
    TestCase(
        id="Grainger plc",
        dcf_analysis_params=DCFAnalysisParameters(
            stock_data=StockData(
                ticker="TEST",
                name="Test Company",
                ebit=126_300_000,
                revenue=284_600_000,
                total_interest_expense=38_800_000,
                gross_debt=1_540_000_000,
                gross_debt_last_year=1_450_000_000,
                net_debt=1_419_000_000,
                capital_expenditure=6_100_000,
                n_shares_outstanding=741_550_000,
                market_cap=1_426_000_000,
                beta=0.71,
            ),
            stock_assumptions=StockAssumptions(
                reasoning="Test assumptions for DCF analysis",
                forecast_period_years=5,
                assumed_tax_rate_pct=0.0,
                assumed_forecast_period_annual_revenue_growth_rate_pct=7.4,
                assumed_perpetuity_cash_flow_growth_rate_pct=3.0,
                assumed_ebit_margin_pct=44.4,
                assumed_depreciation_and_amortization_rate_pct=1.0,
                assumed_capex_rate_pct=2.0,
                assumed_change_in_working_capital_rate_pct=0.5,
            ),
            risk_free_rate_pct=4.2,
            expected_market_return_pct=12.0,
        ),
        expected_dcf_analysis_result=DCFAnalysisResult(
            intrinsic_share_price=4.985518496606527,
            enterprise_value=5116011241.15857,
            equity_value=3697011241.1585703,
        ),
    ),
    TestCase(
        id="Tesco plc",
        dcf_analysis_params=DCFAnalysisParameters(
            stock_data=StockData(
                ticker="TEST",
                name="Test Company",
                ebit=2_809_000_000,
                revenue=69_916_000_000,
                total_interest_expense=575_000_000,
                gross_debt=14_670_000_000,
                gross_debt_last_year=15_500_000_000,
                net_debt=10_040_000_000,
                capital_expenditure=1_392_000_000,
                n_shares_outstanding=6_480_000_000,
                market_cap=28_815_600_000,
                beta=0.62,
            ),
            stock_assumptions=StockAssumptions(
                reasoning="Test assumptions for DCF analysis",
                forecast_period_years=6,
                assumed_tax_rate_pct=25.0,
                assumed_forecast_period_annual_revenue_growth_rate_pct=2.5,
                assumed_perpetuity_cash_flow_growth_rate_pct=2.0,
                assumed_ebit_margin_pct=4.0,
                assumed_depreciation_and_amortization_rate_pct=1.9,
                assumed_capex_rate_pct=2.0,
                assumed_change_in_working_capital_rate_pct=0.5,
            ),
            risk_free_rate_pct=3.9,
            expected_market_return_pct=9.5,
        ),
        expected_dcf_analysis_result=DCFAnalysisResult(
            intrinsic_share_price=6.9310284055222535,
            enterprise_value=54953064067.7842,
            equity_value=44913064067.7842,
        ),
    ),
]


@pytest.mark.parametrize(
    "test_case", [pytest.param(test_case, id=test_case.id) for test_case in TEST_CASES]
)
def test_dcf_analysis(test_case: TestCase):
    # Given
    dcf_analysis = DCFAnalysis(test_case.dcf_analysis_params)

    # When
    actual_dcf_analysis_result = dcf_analysis.dcf_analysis()

    # Then
    assert actual_dcf_analysis_result.model_dump() == pytest.approx(  # type: ignore
        test_case.expected_dcf_analysis_result.model_dump()
    )
