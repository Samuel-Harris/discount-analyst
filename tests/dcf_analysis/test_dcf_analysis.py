from pydantic import BaseModel
from discount_analyst.dcf_analysis import DCFAnalysis, DCFAnalysisParameters
import pytest


class TestCase(BaseModel):
    id: str
    dcf_analysis_params: DCFAnalysisParameters

    expected_cost_of_equity: float
    expected_cost_of_debt: float
    expected_discount_rate: float


TEST_CASES: list[TestCase] = [
    TestCase(
        id="Greggs plc.",
        dcf_analysis_params=DCFAnalysisParameters(
            initial_ebit=195_300_000,
            initial_revenue=2_014_400_000,
            total_interest_expense=5_400_000,
            gross_debt=35_000_000,
            gross_debt_last_year=35_000_000,
            net_debt=2_500_000,
            initial_capital_expenditure=150_000_000,
            n_shares_outstanding=101_775_428,
            equity_value=1_710_000_000,
            beta=1.39,
            risk_free_rate=0.04,
            expected_market_return=0.10,
            assumed_forecast_period_annual_revenue_growth_rate=0.08,
            assumed_perpetuity_cash_flow_growth_rate=0.025,
            assumed_ebit_margin=0.097,
            assumed_tax_rate=0.25,
            assumed_depreciation_rate=0.05,
            assumed_capex_rate=0.075,
            assumed_change_in_working_capital_rate=0.01,
            forecast_period_years=7,
        ),
        expected_cost_of_equity=0.1234,
        expected_cost_of_debt=0.15428571428571428,
        expected_discount_rate=0.12324584527220632,
    ),
    TestCase(
        id="Alphabet Inc.",
        dcf_analysis_params=DCFAnalysisParameters(
            initial_ebit=112_390_000_000,
            initial_revenue=350_018_000_000,
            total_interest_expense=268_000_000,
            gross_debt=13_559_000_000,
            gross_debt_last_year=14_616_000_000,
            net_debt=-81_591_000_000,
            initial_capital_expenditure=52_535_000_000,
            n_shares_outstanding=12_090_000_000,
            equity_value=3_050_000_000_000,
            beta=1.0,
            risk_free_rate=0.0396,
            expected_market_return=0.08,
            assumed_forecast_period_annual_revenue_growth_rate=0.10,
            assumed_perpetuity_cash_flow_growth_rate=0.03,
            assumed_ebit_margin=0.321,
            assumed_tax_rate=0.164,
            assumed_depreciation_rate=0.036,
            assumed_capex_rate=0.15,
            assumed_change_in_working_capital_rate=0.01,
            forecast_period_years=10,
        ),
        expected_cost_of_equity=0.08,
        expected_cost_of_debt=0.01902395740905057,
        expected_discount_rate=0.07971631776015863,
    ),
    TestCase(
        id="HSBC Holdings plc.",
        dcf_analysis_params=DCFAnalysisParameters(
            initial_ebit=32_300_000_000,
            initial_revenue=69_072_000_000,
            total_interest_expense=81_680_000_000,
            gross_debt=129_700_000_000,
            gross_debt_last_year=135_000_000_000,
            net_debt=-116_660_000_000,
            initial_capital_expenditure=1_344_000_000,
            n_shares_outstanding=17_730_000_000,
            equity_value=167_960_000_000,
            beta=0.50,
            risk_free_rate=0.0415,
            expected_market_return=0.09,
            assumed_forecast_period_annual_revenue_growth_rate=0.036,
            assumed_perpetuity_cash_flow_growth_rate=0.025,
            assumed_ebit_margin=0.467,
            assumed_tax_rate=0.164,
            assumed_depreciation_rate=0.01,
            assumed_capex_rate=0.02,
            assumed_change_in_working_capital_rate=0.005,
            forecast_period_years=5,
        ),
        expected_cost_of_equity=0.06575,
        expected_cost_of_debt=0.61715149225538345,
        expected_discount_rate=0.261911619243625,
    ),
    TestCase(
        id="Grainger plc",
        dcf_analysis_params=DCFAnalysisParameters(
            initial_ebit=126_300_000,
            initial_revenue=284_600_000,
            total_interest_expense=38_800_000,
            gross_debt=1_540_000_000,
            gross_debt_last_year=1_450_000_000,
            net_debt=1_419_000_000,
            initial_capital_expenditure=6_100_000,
            n_shares_outstanding=741_550_000,
            equity_value=1_426_000_000,
            beta=0.71,
            risk_free_rate=0.042,
            expected_market_return=0.12,
            assumed_forecast_period_annual_revenue_growth_rate=0.074,
            assumed_perpetuity_cash_flow_growth_rate=0.03,
            assumed_ebit_margin=0.444,
            assumed_tax_rate=0.00,
            assumed_depreciation_rate=0.01,
            assumed_capex_rate=0.02,
            assumed_change_in_working_capital_rate=0.005,
            forecast_period_years=5,
        ),
        expected_cost_of_equity=0.09738,
        expected_cost_of_debt=0.02595317725752508,
        expected_discount_rate=0.06029392210943648,
    ),
    TestCase(
        id="Tesco plc",
        dcf_analysis_params=DCFAnalysisParameters(
            initial_ebit=2_809_000_000,
            initial_revenue=69_916_000_000,
            total_interest_expense=575_000_000,
            gross_debt=14_670_000_000,
            gross_debt_last_year=15_500_000_000,
            net_debt=10_040_000_000,
            initial_capital_expenditure=1_392_000_000,
            n_shares_outstanding=6_480_000_000,
            equity_value=28_815_600_000,
            beta=0.62,
            risk_free_rate=0.039,
            expected_market_return=0.095,
            assumed_forecast_period_annual_revenue_growth_rate=0.025,
            assumed_perpetuity_cash_flow_growth_rate=0.02,
            assumed_ebit_margin=0.040,
            assumed_tax_rate=0.25,
            assumed_depreciation_rate=0.019,
            assumed_capex_rate=0.020,
            assumed_change_in_working_capital_rate=0.005,
            forecast_period_years=6,
        ),
        expected_cost_of_equity=0.07372,
        expected_cost_of_debt=0.03811733510109380,
        expected_discount_rate=0.058494582377839666,
    ),
]


@pytest.mark.parametrize(
    "test_case", [pytest.param(test_case, id=test_case.id) for test_case in TEST_CASES]
)
def test_calculate_cost_of_equity(test_case: TestCase):
    # Given
    dcf_analysis = DCFAnalysis(test_case.dcf_analysis_params)

    # When
    actual_cost_of_equity = dcf_analysis.calculate_cost_of_equity()

    # Then
    assert actual_cost_of_equity == pytest.approx(test_case.expected_cost_of_equity)  # type: ignore


@pytest.mark.parametrize(
    "test_case", [pytest.param(test_case, id=test_case.id) for test_case in TEST_CASES]
)
def test_calculate_cost_of_deb(test_case: TestCase):
    # Given
    dcf_analysis = DCFAnalysis(test_case.dcf_analysis_params)

    # When
    actual_cost_of_debt = dcf_analysis.calculate_cost_of_debt()

    # Then
    assert actual_cost_of_debt == pytest.approx(test_case.expected_cost_of_debt)  # type: ignore


@pytest.mark.parametrize(
    "test_case", [pytest.param(test_case, id=test_case.id) for test_case in TEST_CASES]
)
def test_calculate_discount_rate(test_case: TestCase):
    # Given
    dcf_analysis = DCFAnalysis(test_case.dcf_analysis_params)

    # When
    actual_discount_rate = dcf_analysis.calculate_discount_rate()

    # Then
    assert actual_discount_rate == pytest.approx(test_case.expected_discount_rate)  # type: ignore


# TODO: test project_revenue_growth

# TODO: test forecast_free_cash_flows

# TODO: test calculate_terminal_value

# TODO: test calculate_present_values_of_forecasted_free_cash_flows

# TODO: test calculate_enterprise_value

# TODO: test dcf_analysis
