from datetime import UTC, date, datetime
from decimal import Decimal
from enum import StrEnum
from typing import Annotated, Literal

from pydantic import BaseModel, BeforeValidator, Field


def _reject_binary_float(value: object) -> object:
    if type(value) is float:
        raise ValueError("binary float is not allowed; use Decimal or a decimal string")
    return value


ReportedDecimal = Annotated[Decimal, BeforeValidator(_reject_binary_float)]

FUNDAMENTAL_VALUE_FIELDS: tuple[str, ...] = (
    "revenue",
    "net_income",
    "total_assets",
    "total_liabilities",
    "equity",
    "cash",
    "debt",
    "shares_outstanding",
)

PeriodKind = Literal["annual", "quarterly"]


class UsExchange(StrEnum):
    NASDAQ = "NASDAQ"
    NYSE = "NYSE"
    NYSE_AMERICAN = "NYSE American"


class UkMarket(StrEnum):
    MAIN = "Main"
    AIM = "AIM"


class CacheSource(StrEnum):
    NASDAQ_TRADER = "nasdaq_trader"
    LSE_ISSUERS = "lse_issuers"
    SEC_COMPANYFACTS = "sec_companyfacts"
    COMPANIES_HOUSE = "companies_house"


class EquityListing(BaseModel):
    symbol: str
    issuer_name: str
    exchange: str
    market: str
    isin: str | None = None
    source: str
    source_refreshed_at: datetime


class ListedEquitiesPage(BaseModel):
    items: list[EquityListing]
    total_count: int
    next_cursor: str | None = None


class FilingHandle(BaseModel):
    form_type: str
    period_end: date
    filed_at: date
    accession_or_document_id: str
    source_url: str


class CanonicalFundamentals(BaseModel):
    identifier: str
    issuer_name: str
    cik: str | None = None
    company_number: str | None = None
    currency: str | None = None
    period_kind: PeriodKind
    period_end: date | None = None
    filed_at: date | None = None
    form_type: str | None = None
    revenue: ReportedDecimal | None = None
    net_income: ReportedDecimal | None = None
    total_assets: ReportedDecimal | None = None
    total_liabilities: ReportedDecimal | None = None
    equity: ReportedDecimal | None = None
    cash: ReportedDecimal | None = None
    debt: ReportedDecimal | None = None
    shares_outstanding: ReportedDecimal | None = None
    accounts_filleted: bool | None = None
    profit_and_loss_available: bool | None = None
    missing_fields: list[str] = Field(default_factory=list)
    recent_filings: list[FilingHandle] = Field(default_factory=list[FilingHandle])


class UkCompanyMatch(BaseModel):
    company_number: str
    company_name: str
    company_status: str | None = None
    company_type: str | None = None


class UkCompanyResolveResult(BaseModel):
    query: str
    candidates: list[UkCompanyMatch]
    selected: UkCompanyMatch | None = None


class SourceSnapshot(BaseModel):
    source: str
    version_id: str
    relative_path: str
    refreshed_at: datetime
    record_count: int = 0
    downloaded_version_or_date: str = ""


class CacheManifest(BaseModel):
    sources: dict[str, SourceSnapshot] = Field(default_factory=dict)


class SourceRefreshResult(BaseModel):
    source: str
    version_id: str
    downloaded_version_or_date: str
    record_count: int
    cache_path: str
    skipped_or_idempotent_count: int = 0
    active_snapshot: str


def utc_now() -> datetime:
    return datetime.now(UTC)


def missing_fundamental_fields(
    *,
    revenue: Decimal | None,
    net_income: Decimal | None,
    total_assets: Decimal | None,
    total_liabilities: Decimal | None,
    equity: Decimal | None,
    cash: Decimal | None,
    debt: Decimal | None,
    shares_outstanding: Decimal | None,
) -> list[str]:
    values = {
        "revenue": revenue,
        "net_income": net_income,
        "total_assets": total_assets,
        "total_liabilities": total_liabilities,
        "equity": equity,
        "cash": cash,
        "debt": debt,
        "shares_outstanding": shares_outstanding,
    }
    return [name for name in FUNDAMENTAL_VALUE_FIELDS if values[name] is None]
