from datetime import date
from decimal import Decimal

from discount_analyst.agents.tools.regulatory_data.models import (
    CanonicalFundamentals,
    PeriodKind,
)
from discount_analyst.agents.tools.regulatory_data.sec_edgar.company_facts import (
    ANNUAL_FORMS,
    QUARTERLY_FORMS,
)
from discount_analyst.agents.tools.regulatory_data.sec_edgar.selection import (
    fundamentals_from_companyfacts,
)

FY2025_END = date(2025, 9, 27)
SHARES_INSTANT = date(2025, 10, 17)
FILED_AT = date(2025, 10, 31)
ACCN = "0000320193-25-000079"
FY_REVENUE = Decimal("416161000000")
FY_ASSETS = Decimal("359241000000")
FY_SHARES = Decimal("14773260000")
LATER_DEI_SHARES = Decimal("14776353000")

Q3_END = date(2026, 6, 27)
Q3_SHARES_INSTANT = date(2026, 7, 17)
Q3_FILED = date(2026, 7, 31)
Q3_ACCN = "0000320193-26-000020"
Q3_REVENUE = Decimal("94036000000")
Q3_ASSETS = Decimal("331685000000")
Q3_SHARES = Decimal("14591163000")
Q3_LATER_DEI_SHARES = Decimal("14594180000")


def _unit_row(
    *,
    end: str,
    val: int,
    accn: str,
    form: str,
    filed: str,
    start: str | None = None,
) -> dict[str, object]:
    row: dict[str, object] = {
        "end": end,
        "val": val,
        "accn": accn,
        "form": form,
        "filed": filed,
    }
    if start is not None:
        row["start"] = start
    return row


def _concept(unit: str, rows: list[dict[str, object]]) -> dict[str, object]:
    return {"units": {unit: rows}}


def _later_share_instant_payload() -> dict[str, object]:
    return {
        "cik": 320193,
        "entityName": "Apple Inc.",
        "facts": {
            "dei": {
                "EntityCommonStockSharesOutstanding": _concept(
                    "shares",
                    [
                        _unit_row(
                            end="2025-10-17",
                            val=int(LATER_DEI_SHARES),
                            accn=ACCN,
                            form="10-K",
                            filed="2025-10-31",
                        ),
                        _unit_row(
                            end="2026-07-17",
                            val=int(Q3_LATER_DEI_SHARES),
                            accn=Q3_ACCN,
                            form="10-Q",
                            filed="2026-07-31",
                        ),
                    ],
                )
            },
            "us-gaap": {
                "RevenueFromContractWithCustomerExcludingAssessedTax": _concept(
                    "USD",
                    [
                        _unit_row(
                            end="2025-09-27",
                            val=int(FY_REVENUE),
                            accn=ACCN,
                            form="10-K",
                            filed="2025-10-31",
                            start="2024-09-29",
                        ),
                        _unit_row(
                            end="2026-06-27",
                            val=int(Q3_REVENUE),
                            accn=Q3_ACCN,
                            form="10-Q",
                            filed="2026-07-31",
                            start="2026-03-29",
                        ),
                    ],
                ),
                "Assets": _concept(
                    "USD",
                    [
                        _unit_row(
                            end="2025-09-27",
                            val=int(FY_ASSETS),
                            accn=ACCN,
                            form="10-K",
                            filed="2025-10-31",
                        ),
                        _unit_row(
                            end="2026-06-27",
                            val=int(Q3_ASSETS),
                            accn=Q3_ACCN,
                            form="10-Q",
                            filed="2026-07-31",
                        ),
                    ],
                ),
                "CommonStockSharesOutstanding": _concept(
                    "shares",
                    [
                        _unit_row(
                            end="2025-09-27",
                            val=int(FY_SHARES),
                            accn=ACCN,
                            form="10-K",
                            filed="2025-10-31",
                        ),
                        _unit_row(
                            end="2026-06-27",
                            val=int(Q3_SHARES),
                            accn=Q3_ACCN,
                            form="10-Q",
                            filed="2026-07-31",
                        ),
                    ],
                ),
            },
        },
    }


def _snapshot(period_kind: PeriodKind) -> CanonicalFundamentals:
    return fundamentals_from_companyfacts(
        _later_share_instant_payload(),
        ticker="AAPL",
        issuer_title="Apple Inc.",
        cik="0000320193",
        period_kind=period_kind,
        as_of=None,
        annual_forms=ANNUAL_FORMS,
        quarterly_forms=QUARTERLY_FORMS,
    )


def test_annual_statement_period_ignores_later_share_instant() -> None:
    snapshot = _snapshot("annual")
    assert snapshot.period_end == FY2025_END
    assert snapshot.filed_at == FILED_AT
    assert snapshot.form_type == "10-K"
    assert snapshot.revenue == FY_REVENUE
    assert snapshot.total_assets == FY_ASSETS
    assert snapshot.shares_outstanding == FY_SHARES
    assert snapshot.shares_outstanding != LATER_DEI_SHARES
    assert snapshot.profit_and_loss_available is True
    assert snapshot.period_end != SHARES_INSTANT


def test_quarterly_statement_period_ignores_later_share_instant() -> None:
    snapshot = _snapshot("quarterly")
    assert snapshot.period_end == Q3_END
    assert snapshot.filed_at == Q3_FILED
    assert snapshot.form_type == "10-Q"
    assert snapshot.revenue == Q3_REVENUE
    assert snapshot.total_assets == Q3_ASSETS
    assert snapshot.shares_outstanding == Q3_SHARES
    assert snapshot.shares_outstanding != Q3_LATER_DEI_SHARES
    assert snapshot.period_end != Q3_SHARES_INSTANT


def test_shares_only_snapshot_still_uses_the_share_instant() -> None:
    payload = {
        "cik": 320193,
        "entityName": "Apple Inc.",
        "facts": {
            "dei": {
                "EntityCommonStockSharesOutstanding": _concept(
                    "shares",
                    [
                        _unit_row(
                            end="2025-10-17",
                            val=int(LATER_DEI_SHARES),
                            accn=ACCN,
                            form="10-K",
                            filed="2025-10-31",
                        )
                    ],
                )
            }
        },
    }
    snapshot = fundamentals_from_companyfacts(
        payload,
        ticker="AAPL",
        issuer_title="Apple Inc.",
        cik="0000320193",
        period_kind="annual",
        as_of=None,
        annual_forms=ANNUAL_FORMS,
        quarterly_forms=QUARTERLY_FORMS,
    )
    assert snapshot.period_end == SHARES_INSTANT
    assert snapshot.shares_outstanding == LATER_DEI_SHARES
    assert snapshot.revenue is None
