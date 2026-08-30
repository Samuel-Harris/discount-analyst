import sqlite3

from discount_analyst.agents.tools.regulatory_data.cache import RegulatoryDataCache
from discount_analyst.agents.tools.regulatory_data.companies_house.ingest import (
    canonical_company_number,
    normalise_text,
)
from discount_analyst.agents.tools.regulatory_data.companies_house.store import (
    connect,
    fetch_companies_by_normalised_name,
    fetch_company_by_number,
    require_active_database,
)
from discount_analyst.agents.tools.regulatory_data.exchanges.london_stock_exchange import (
    listing_for_symbol,
)
from discount_analyst.agents.tools.regulatory_data.models import (
    UkCompanyMatch,
    UkCompanyResolveResult,
)


async def resolve_uk_company(query: str) -> UkCompanyResolveResult:
    """Resolve a UK company number, exact name, or listed TIDM.

    Auto-selects only when exactly one candidate matches after normalisation.
    Ambiguous results return candidates with ``selected`` left unset; that is
    data, not an error. A TIDM (with or without ``.L``) is resolved only when
    an LSE issuers snapshot is already cached; this tool does not download
    listings.

    Args:
        query: Companies House number, exact registered name, or TIDM.
            Surrounding whitespace is ignored.

    Returns:
        Candidate companies and an optional auto-selected match.
    """
    cache = RegulatoryDataCache.from_settings()
    connection = connect(require_active_database(cache))
    try:
        return _resolve(connection, cache, query)
    finally:
        connection.close()


def _resolve(
    connection: sqlite3.Connection,
    cache: RegulatoryDataCache,
    query: str,
) -> UkCompanyResolveResult:
    normalised = normalise_text(query)
    if not normalised:
        return UkCompanyResolveResult(query=query, candidates=[], selected=None)

    company_number = canonical_company_number(normalised)
    if company_number is not None:
        row = fetch_company_by_number(connection, company_number)
        if row is None:
            return UkCompanyResolveResult(query=query, candidates=[], selected=None)
        match = _match_from_row(row)
        return UkCompanyResolveResult(query=query, candidates=[match], selected=match)

    rows = fetch_companies_by_normalised_name(connection, normalised)
    candidates = [_match_from_row(row) for row in rows]
    if not candidates and " " not in normalised:
        listing = listing_for_symbol(cache, normalised)
        if listing is not None:
            rows = fetch_companies_by_normalised_name(
                connection, normalise_text(listing.issuer_name)
            )
            candidates = [_match_from_row(row) for row in rows]
    selected = candidates[0] if len(candidates) == 1 else None
    return UkCompanyResolveResult(query=query, candidates=candidates, selected=selected)


def _match_from_row(row: sqlite3.Row) -> UkCompanyMatch:
    return UkCompanyMatch(
        company_number=row["company_number"],
        company_name=row["company_name"],
        company_status=row["company_status"],
        company_type=row["company_type"],
    )
