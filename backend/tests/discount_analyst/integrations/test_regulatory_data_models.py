from datetime import UTC, date, datetime
from decimal import Decimal

import pytest
from pydantic import ValidationError

from discount_analyst.agents.tools.regulatory_data.models import (
    CanonicalFundamentals,
    EquityListing,
    FilingHandle,
    UkCompanyMatch,
    UkCompanyResolveResult,
    missing_fundamental_fields,
)


def test_equity_listing_round_trip() -> None:
    listing = EquityListing(
        symbol="AAPL",
        issuer_name="Apple Inc.",
        exchange="NASDAQ",
        market="NASDAQ GS",
        isin=None,
        source="nasdaq_trader",
        source_refreshed_at=datetime(2026, 8, 30, tzinfo=UTC),
    )
    restored = EquityListing.model_validate(listing.model_dump())
    assert restored == listing


def test_canonical_fundamentals_preserve_decimal() -> None:
    snapshot = CanonicalFundamentals(
        identifier="AAPL",
        issuer_name="Apple Inc.",
        cik="0000320193",
        currency="USD",
        period_kind="annual",
        period_end=date(2023, 9, 30),
        filed_at=date(2023, 12, 15),
        form_type="10-K/A",
        revenue=Decimal("383000000000"),
        net_income=Decimal("97000000000"),
        missing_fields=["cash"],
        recent_filings=[
            FilingHandle(
                form_type="10-K/A",
                period_end=date(2023, 9, 30),
                filed_at=date(2023, 12, 15),
                accession_or_document_id="0000320193-23-000120",
                source_url="https://www.sec.gov/",
            )
        ],
    )
    dumped = snapshot.model_dump()
    assert dumped["revenue"] == Decimal("383000000000")
    assert type(dumped["revenue"]) is Decimal


def test_canonical_fundamentals_reject_binary_float() -> None:
    with pytest.raises(ValidationError, match="binary float"):
        CanonicalFundamentals(
            identifier="AAPL",
            issuer_name="Apple Inc.",
            period_kind="annual",
            revenue=1.25,  # type: ignore[arg-type]
        )


def test_uk_resolve_ambiguity_is_data() -> None:
    result = UkCompanyResolveResult(
        query="AMBIGUOUS EXAMPLE",
        candidates=[
            UkCompanyMatch(
                company_number="12345678", company_name="AMBIGUOUS EXAMPLE LTD"
            ),
            UkCompanyMatch(
                company_number="87654321", company_name="AMBIGUOUS EXAMPLE PLC"
            ),
        ],
        selected=None,
    )
    assert result.selected is None
    assert len(result.candidates) == 2


def test_missing_fundamental_fields_lists_none_values() -> None:
    missing = missing_fundamental_fields(
        revenue=Decimal("1"),
        net_income=None,
        total_assets=Decimal("2"),
        total_liabilities=None,
        equity=Decimal("3"),
        cash=None,
        debt=None,
        shares_outstanding=Decimal("4"),
    )
    assert missing == ["net_income", "total_liabilities", "cash", "debt"]
