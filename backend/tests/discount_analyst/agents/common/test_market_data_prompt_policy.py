import json

from discount_analyst.agents.appraiser.system_prompt import (
    SYSTEM_PROMPT as APPRAISER_PROMPT,
)
from discount_analyst.agents.common_prompts.market_data import (
    MARKET_DATA_TOOL_RULES,
)
from discount_analyst.agents.common_prompts.regulatory_data import (
    REGULATORY_FILINGS_TOOL_RULES,
    REGULATORY_UNIVERSE_TOOL_RULES,
)
from discount_analyst.agents.profiler.system_prompt import (
    SYSTEM_PROMPT as PROFILER_PROMPT,
)
from discount_analyst.agents.researcher.system_prompt import (
    SYSTEM_PROMPT as RESEARCHER_PROMPT,
)
from discount_analyst.agents.sentinel.system_prompt import (
    SYSTEM_PROMPT as SENTINEL_PROMPT,
)
from discount_analyst.agents.strategist.system_prompt import (
    SYSTEM_PROMPT as STRATEGIST_PROMPT,
)
from discount_analyst.agents.surveyor.system_prompt import (
    SYSTEM_PROMPT as SURVEYOR_PROMPT,
)
from discount_analyst.agents.surveyor.schema import SurveyorOutput
from discount_analyst.agents.tools.terminal.client import TERMINAL_EXEC_DESCRIPTION


def test_market_data_rules_reach_agents_that_can_run_yfinance() -> None:
    for prompt in (
        SURVEYOR_PROMPT,
        PROFILER_PROMPT,
        RESEARCHER_PROMPT,
        APPRAISER_PROMPT,
    ):
        assert MARKET_DATA_TOOL_RULES in prompt

    assert MARKET_DATA_TOOL_RULES not in SENTINEL_PROMPT
    assert MARKET_DATA_TOOL_RULES not in STRATEGIST_PROMPT


def test_official_tool_rules_match_agent_tool_surfaces() -> None:
    assert REGULATORY_UNIVERSE_TOOL_RULES in SURVEYOR_PROMPT
    for prompt in (
        SURVEYOR_PROMPT,
        PROFILER_PROMPT,
        RESEARCHER_PROMPT,
        STRATEGIST_PROMPT,
        SENTINEL_PROMPT,
        APPRAISER_PROMPT,
    ):
        assert REGULATORY_FILINGS_TOOL_RULES in prompt


def test_surveyor_uses_yfinance_screening_path() -> None:
    assert "yfinance.EquityQuery" in SURVEYOR_PROMPT
    assert "never call FMP" in SURVEYOR_PROMPT
    assert "EODHD `stock_screener`" in SURVEYOR_PROMPT
    assert "server-side `intradaymarketcap` filter is unreliable" in SURVEYOR_PROMPT
    assert "strip the `.L` suffix" in SURVEYOR_PROMPT
    assert "`market_cap_local` in the Surveyor output is whole **GBP or USD**" in (
        SURVEYOR_PROMPT
    )


def test_named_stock_prompts_use_major_currency_market_cap() -> None:
    normalised_prompt = " ".join(PROFILER_PROMPT.split())

    assert (
        "Store `market_cap_local` as a whole number of GBP or USD" in normalised_prompt
    )
    assert "never store pence under a `GBP` currency label" in normalised_prompt


def test_surveyor_schema_does_not_direct_agents_to_paid_sources() -> None:
    rendered_schema = json.dumps(SurveyorOutput.model_json_schema())

    assert "FMP" not in rendered_schema
    assert "EODHD" not in rendered_schema


def test_sentinel_cannot_claim_market_data_research() -> None:
    assert "You cannot run yfinance" in SENTINEL_PROMPT
    assert "Paid FMP/EODHD tools" in SENTINEL_PROMPT
    assert "one `get_sec_company_facts` call" in SENTINEL_PROMPT


def test_surveyor_uses_valid_yfinance_volume_field() -> None:
    assert "avgdailyvol3m" in SURVEYOR_PROMPT
    lowered = SURVEYOR_PROMPT.casefold()
    assert "averagedailyvolume10day" not in lowered
    assert "averagevolume10days" not in lowered


def test_researcher_classifies_helper_failures_as_remaining_gaps() -> None:
    assert "never `material_open_gaps`" in RESEARCHER_PROMPT
    assert "SEC__USER_AGENT" in RESEARCHER_PROMPT
    assert "Companies House cold cache" in RESEARCHER_PROMPT


def test_terminal_description_uses_markitdown_not_downloaders() -> None:
    assert "markitdown" in TERMINAL_EXEC_DESCRIPTION
    assert "do not call ``curl``" in TERMINAL_EXEC_DESCRIPTION
    assert "wget" in TERMINAL_EXEC_DESCRIPTION
    assert "pdftotext" in TERMINAL_EXEC_DESCRIPTION
