from pydantic import BaseModel
from discount_analyst.dcf_analysis import DCFAnalysis, DCFAnalysisParameters
import pytest


class TestCase(BaseModel):
    id: str
    dcf_analysis_params: DCFAnalysisParameters

    expected_cost_of_equity: float
    expected_cost_of_debt: float
    expected_discount_rate: float
    expected_projected_revenues: list[float]
    expected_forecasted_free_cash_flows: list[float]
    expected_terminal_value: float
    expected_present_values_of_forecasted_free_cash_flows: list[float]


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
            assumed_depreciation_and_amortization_rate=0.05,
            assumed_capex_rate=0.075,
            assumed_change_in_working_capital_rate=0.01,
            forecast_period_years=7,
        ),
        expected_cost_of_equity=0.1234,
        expected_cost_of_debt=0.15428571428571428,
        expected_discount_rate=0.12324584527220632,
        expected_projected_revenues=[
            2175552000,
            2349596160,
            2537563852.8,
            2740568961.024,
            2959814477.90592,
            3196599636.1383936,
            3452327607.02946509,
        ],
        expected_forecasted_free_cash_flows=[
            102271088.0,
            110452775.03999999,
            119288997.04320002,
            128832116.80665596,
            139138686.15118852,
            150269781.04328355,
            162291363.52674627,
        ],
        expected_terminal_value=1693187606.600753,
        expected_present_values_of_forecasted_free_cash_flows=[
            91049602.74766539,
            87544121.69105202,
            84173604.40218109,
            80932854.67023036,
            77816876.34256649,
            74820865.62234741,
            71940203.66267426,
        ],
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
            assumed_depreciation_and_amortization_rate=0.036,
            assumed_capex_rate=0.15,
            assumed_change_in_working_capital_rate=0.01,
            forecast_period_years=10,
        ),
        expected_cost_of_equity=0.08,
        expected_cost_of_debt=0.01902395740905057,
        expected_discount_rate=0.07971631776015863,
        expected_projected_revenues=[
            385019800000,
            423521780000,
            465873958000,
            512461353800,
            563707489180,
            620078238098,
            682086061907.8,
            750294668098.58,
            825324134908.438,
            907856548399.2818,
        ],
        expected_forecasted_free_cash_flows=[
            59080098248.8,
            64988108073.67999,
            71486918881.04797,
            78635610769.1528,
            86499171846.06807,
            95149089030.67488,
            104663997933.74237,
            115130397727.11661,
            126643437499.8283,
            139307781249.8111,
        ],
        expected_terminal_value=2886115085584.48,
        expected_present_values_of_forecasted_free_cash_flows=[
            54718167426.94046,
            55746109584.133125,
            56793362787.87983,
            57860289817.853004,
            58947260268.94806,
            60054650679.315254,
            61182844660.79632,
            62332233031.8118,
            63503213952.74467,
            64696193063.8673,
        ],
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
            assumed_depreciation_and_amortization_rate=0.01,
            assumed_capex_rate=0.02,
            assumed_change_in_working_capital_rate=0.005,
            forecast_period_years=5,
        ),
        expected_cost_of_equity=0.06575,
        expected_cost_of_debt=0.61715149225538345,
        expected_discount_rate=0.261911619243625,
        expected_projected_revenues=[
            71558592000,
            74134701312,
            76803550559.232,
            79568478379.364352,
            82432943601.02146867,
        ],
        expected_forecasted_free_cash_flows=[
            27209314139.904,
            28188849448.94054,
            29203648029.102406,
            30254979358.15009,
            31344158615.043495,
        ],
        expected_terminal_value=135610750890.95317,
        expected_present_values_of_forecasted_free_cash_flows=[
            21561980827.32049,
            17701883235.28813,
            14532833165.250336,
            11931116989.178486,
            9795168704.602097,
        ],
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
            assumed_depreciation_and_amortization_rate=0.01,
            assumed_capex_rate=0.02,
            assumed_change_in_working_capital_rate=0.005,
            forecast_period_years=5,
        ),
        expected_cost_of_equity=0.09738,
        expected_cost_of_debt=0.02595317725752508,
        expected_discount_rate=0.06029392210943648,
        expected_projected_revenues=[
            305660400,
            328279269.6,
            352571935.5504,
            378662258.7811296,
            406683265.93093319,
        ],
        expected_forecasted_free_cash_flows=[
            132551311.6,
            142360108.65840003,
            152894756.6991216,
            164208968.69485658,
            176360432.378276,
        ],
        expected_terminal_value=5996293404.776411,
        expected_present_values_of_forecasted_free_cash_flows=[
            125013742.73304467,
            126629755.10429464,
            128266657.14676742,
            129924718.89451206,
            131604213.87222065,
        ],
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
            assumed_depreciation_and_amortization_rate=0.019,
            assumed_capex_rate=0.020,
            assumed_change_in_working_capital_rate=0.005,
            forecast_period_years=6,
        ),
        expected_cost_of_equity=0.07372,
        expected_cost_of_debt=0.03811733510109380,
        expected_discount_rate=0.058494582377839666,
        expected_projected_revenues=[
            71663900000,
            73455497500,
            75291884937.5,
            77174182060.9375,
            79103536612.4609375,
            81081125027.77246094,
        ],
        expected_forecasted_free_cash_flows=[
            2069513600.0,
            2121251440.0,
            2174282726.0,
            2228639794.1499996,
            2284355789.00375,
            2341464683.728843,
        ],
        expected_terminal_value=62042340243.13767,
        expected_present_values_of_forecasted_free_cash_flows=[
            1955148032.360233,
            1893280104.1525617,
            1833369900.1055973,
            1775355470.7731483,
            1719176827.0127091,
            1664775877.9543834,
        ],
    ),
]


@pytest.mark.parametrize(
    "test_case", [pytest.param(test_case, id=test_case.id) for test_case in TEST_CASES]
)
def test_calculate_cost_of_equity(test_case: TestCase):
    # Given
    dcf_analysis = DCFAnalysis(test_case.dcf_analysis_params)

    # When
    actual_cost_of_equity = dcf_analysis._calculate_cost_of_equity()

    # Then
    assert actual_cost_of_equity == pytest.approx(test_case.expected_cost_of_equity)  # type: ignore


@pytest.mark.parametrize(
    "test_case", [pytest.param(test_case, id=test_case.id) for test_case in TEST_CASES]
)
def test_calculate_cost_of_deb(test_case: TestCase):
    # Given
    dcf_analysis = DCFAnalysis(test_case.dcf_analysis_params)

    # When
    actual_cost_of_debt = dcf_analysis._calculate_cost_of_debt()

    # Then
    assert actual_cost_of_debt == pytest.approx(test_case.expected_cost_of_debt)  # type: ignore


@pytest.mark.parametrize(
    "test_case", [pytest.param(test_case, id=test_case.id) for test_case in TEST_CASES]
)
def test_calculate_discount_rate(test_case: TestCase):
    # Given
    dcf_analysis = DCFAnalysis(test_case.dcf_analysis_params)

    # When
    actual_discount_rate = dcf_analysis._calculate_discount_rate()

    # Then
    assert actual_discount_rate == pytest.approx(test_case.expected_discount_rate)  # type: ignore


@pytest.mark.parametrize(
    "test_case", [pytest.param(test_case, id=test_case.id) for test_case in TEST_CASES]
)
def test_project_revenue_growth(test_case: TestCase):
    # Given
    dcf_analysis = DCFAnalysis(test_case.dcf_analysis_params)

    # When
    actual_projected_revenues = dcf_analysis._project_revenue_growth()

    # Then
    assert actual_projected_revenues == pytest.approx(  # type: ignore
        test_case.expected_projected_revenues
    )


@pytest.mark.parametrize(
    "test_case", [pytest.param(test_case, id=test_case.id) for test_case in TEST_CASES]
)
def test_forecast_free_cash_flows(test_case: TestCase):
    # Given
    dcf_analysis = DCFAnalysis(test_case.dcf_analysis_params)

    # When
    actual_forecasted_free_cash_flows = dcf_analysis._forecast_free_cash_flows()

    # Then
    assert actual_forecasted_free_cash_flows == pytest.approx(  # type: ignore
        test_case.expected_forecasted_free_cash_flows
    )


@pytest.mark.parametrize(
    "test_case", [pytest.param(test_case, id=test_case.id) for test_case in TEST_CASES]
)
def test_calculate_terminal_value(test_case: TestCase):
    # Given
    dcf_analysis = DCFAnalysis(test_case.dcf_analysis_params)

    # When
    actual_terminal_value = dcf_analysis._calculate_terminal_value(
        test_case.expected_forecasted_free_cash_flows[-1],
        test_case.expected_discount_rate,
    )

    # Then
    assert actual_terminal_value == pytest.approx(  # type: ignore
        test_case.expected_terminal_value
    )


@pytest.mark.parametrize(
    "test_case", [pytest.param(test_case, id=test_case.id) for test_case in TEST_CASES]
)
def test_calculate_present_values_of_forecasted_free_cash_flows(test_case: TestCase):
    # Given
    dcf_analysis = DCFAnalysis(test_case.dcf_analysis_params)

    # When
    actual_terminal_value = (
        dcf_analysis._calculate_present_values_of_forecasted_free_cash_flows(
            test_case.expected_forecasted_free_cash_flows,
            test_case.expected_discount_rate,
        )
    )

    # Then
    assert actual_terminal_value == pytest.approx(  # type: ignore
        test_case.expected_present_values_of_forecasted_free_cash_flows
    )


# TODO: test calculate_enterprise_value


# @pytest.mark.parametrize(
#     "test_case", [pytest.param(test_case, id=test_case.id) for test_case in TEST_CASES]
# )
# def test_forecast_free_cash_flows(test_case: TestCase):
#     # Given
#     dcf_analysis = DCFAnalysis(test_case.dcf_analysis_params)

#     # When
#     actual_intrinsic_share_price = dcf_analysis.dcf_analysis()

#     # Then
#     assert actual_intrinsic_share_price == pytest.approx(  # type: ignore
#         test_case.expected_projected_revenues
#     )
