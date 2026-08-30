from collections.abc import Awaitable, Callable

from discount_analyst.agents.tools.regulatory_data.companies_house.accounts import (
    refresh_companies_house,
)
from discount_analyst.agents.tools.regulatory_data.exchanges.london_stock_exchange import (
    refresh_lse_issuers,
)
from discount_analyst.agents.tools.regulatory_data.exchanges.nasdaq_trader import (
    refresh_nasdaq_trader,
)
from discount_analyst.agents.tools.regulatory_data.models import SourceRefreshResult
from discount_analyst.agents.tools.regulatory_data.sec_edgar.company_facts import (
    refresh_sec_edgar,
)

type RefreshJob = Callable[[], Awaitable[SourceRefreshResult]]


def resolve_refresh_flags(
    *,
    exchanges: bool,
    sec: bool,
    companies_house: bool,
) -> tuple[bool, bool, bool]:
    if not (exchanges or sec or companies_house):
        return True, True, True
    return exchanges, sec, companies_house


def refresh_jobs(
    *,
    exchanges: bool,
    sec: bool,
    companies_house: bool,
) -> tuple[tuple[str, RefreshJob], ...]:
    exchanges, sec, companies_house = resolve_refresh_flags(
        exchanges=exchanges, sec=sec, companies_house=companies_house
    )
    jobs: list[tuple[str, RefreshJob]] = []
    if exchanges:
        jobs.append(("nasdaq_trader", refresh_nasdaq_trader))
        jobs.append(("lse_issuers", refresh_lse_issuers))
    if sec:
        jobs.append(("sec_edgar", refresh_sec_edgar))
    if companies_house:
        jobs.append(("companies_house", refresh_companies_house))
    return tuple(jobs)


async def refresh_selected(
    *,
    exchanges: bool = False,
    sec: bool = False,
    companies_house: bool = False,
) -> tuple[list[SourceRefreshResult], list[tuple[str, BaseException]]]:
    results: list[SourceRefreshResult] = []
    failures: list[tuple[str, BaseException]] = []
    for source, job in refresh_jobs(
        exchanges=exchanges, sec=sec, companies_house=companies_house
    ):
        try:
            results.append(await job())
        except Exception as exc:
            failures.append((source, exc))
    return results, failures
