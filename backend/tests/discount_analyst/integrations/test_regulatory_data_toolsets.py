from pydantic_ai import RunContext
from pydantic_ai.models.test import TestModel
from pydantic_ai.usage import RunUsage

from discount_analyst.agents.tools.regulatory_data.toolsets import (
    create_filings_toolset,
    create_universe_toolset,
)
from discount_analyst.agents.tools.terminal.infallible_toolset import InfallibleToolset


async def test_universe_toolset_is_infallible_with_listing_tools() -> None:
    toolset = create_universe_toolset()
    assert isinstance(toolset, InfallibleToolset)
    ctx = RunContext(deps=None, model=TestModel(), usage=RunUsage())
    tools = await toolset.get_tools(ctx)
    assert set(tools) == {"list_us_listed_equities", "list_uk_listed_equities"}


async def test_filings_toolset_is_infallible_with_filing_tools() -> None:
    toolset = create_filings_toolset()
    assert isinstance(toolset, InfallibleToolset)
    ctx = RunContext(deps=None, model=TestModel(), usage=RunUsage())
    tools = await toolset.get_tools(ctx)
    assert set(tools) == {
        "get_sec_company_facts",
        "resolve_uk_company",
        "get_companies_house_accounts",
    }


async def test_listing_tool_errors_are_infallible_strings() -> None:
    toolset = create_universe_toolset()
    ctx = RunContext(deps=None, model=TestModel(), usage=RunUsage())
    tools = await toolset.get_tools(ctx)
    result = await toolset.call_tool(
        "list_us_listed_equities",
        {"limit": 0},
        ctx,
        tools["list_us_listed_equities"],
    )
    assert isinstance(result, str)
    assert "list_us_listed_equities" in result
    assert "limit" in result.lower()
