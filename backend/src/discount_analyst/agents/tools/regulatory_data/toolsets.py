from pydantic_ai import FunctionToolset

from discount_analyst.agents.tools.regulatory_data.companies_house.accounts import (
    get_companies_house_accounts,
)
from discount_analyst.agents.tools.regulatory_data.companies_house.resolve import (
    resolve_uk_company,
)
from discount_analyst.agents.tools.regulatory_data.exchanges.london_stock_exchange import (
    list_uk_listed_equities,
)
from discount_analyst.agents.tools.regulatory_data.exchanges.nasdaq_trader import (
    list_us_listed_equities,
)
from discount_analyst.agents.tools.regulatory_data.sec_edgar.company_facts import (
    get_sec_company_facts,
)
from discount_analyst.agents.tools.terminal.infallible_toolset import InfallibleToolset


def create_universe_toolset() -> InfallibleToolset[None]:
    """Exchange-universe tools for Surveyor."""
    toolset = FunctionToolset[None]()
    toolset.add_function(
        list_us_listed_equities,
        name="list_us_listed_equities",
        docstring_format="google",
        require_parameter_descriptions=True,
    )
    toolset.add_function(
        list_uk_listed_equities,
        name="list_uk_listed_equities",
        docstring_format="google",
        require_parameter_descriptions=True,
    )
    return InfallibleToolset(toolset)


def create_filings_toolset() -> InfallibleToolset[None]:
    """SEC and Companies House filing tools for all pipeline agents."""
    toolset = FunctionToolset[None]()
    toolset.add_function(
        get_sec_company_facts,
        name="get_sec_company_facts",
        docstring_format="google",
        require_parameter_descriptions=True,
    )
    toolset.add_function(
        resolve_uk_company,
        name="resolve_uk_company",
        docstring_format="google",
        require_parameter_descriptions=True,
    )
    toolset.add_function(
        get_companies_house_accounts,
        name="get_companies_house_accounts",
        docstring_format="google",
        require_parameter_descriptions=True,
    )
    return InfallibleToolset(toolset)
