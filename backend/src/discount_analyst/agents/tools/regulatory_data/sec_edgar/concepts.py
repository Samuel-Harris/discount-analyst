from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Concept:
    taxonomy: str
    name: str


def _us_gaap(*names: str) -> tuple[Concept, ...]:
    return tuple(Concept("us-gaap", name) for name in names)


REVENUE_CONCEPTS: tuple[Concept, ...] = _us_gaap(
    "RevenueFromContractWithCustomerExcludingAssessedTax",
    "Revenues",
    "SalesRevenueNet",
    "RevenueFromContractWithCustomerIncludingAssessedTax",
)

NET_INCOME_CONCEPTS: tuple[Concept, ...] = _us_gaap(
    "NetIncomeLoss",
    "ProfitLoss",
    "NetIncomeLossAvailableToCommonStockholdersBasic",
)

ASSET_CONCEPTS: tuple[Concept, ...] = _us_gaap("Assets")

LIABILITY_CONCEPTS: tuple[Concept, ...] = _us_gaap("Liabilities")

EQUITY_CONCEPTS: tuple[Concept, ...] = _us_gaap(
    "StockholdersEquity",
    "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest",
    "Equity",
)

CASH_CONCEPTS: tuple[Concept, ...] = _us_gaap(
    "CashAndCashEquivalentsAtCarryingValue",
    "CashCashEquivalentsAndShortTermInvestments",
    "Cash",
)

SHARES_CONCEPTS: tuple[Concept, ...] = (
    Concept("dei", "EntityCommonStockSharesOutstanding"),
    Concept("us-gaap", "CommonStockSharesOutstanding"),
)

DEBT_TOTAL_CONCEPTS: tuple[Concept, ...] = _us_gaap(
    "LongTermDebtAndCapitalLeaseObligations",
    "LongTermDebt",
    "DebtAndCapitalLeaseObligations",
)

DEBT_COMPONENT_PAIRS: tuple[tuple[Concept, Concept], ...] = (
    (
        Concept("us-gaap", "DebtCurrent"),
        Concept("us-gaap", "LongTermDebtNoncurrent"),
    ),
    (
        Concept("us-gaap", "LongTermDebtCurrent"),
        Concept("us-gaap", "LongTermDebtNoncurrent"),
    ),
)


TRACKED_CONCEPTS: frozenset[Concept] = frozenset(
    (
        *REVENUE_CONCEPTS,
        *NET_INCOME_CONCEPTS,
        *ASSET_CONCEPTS,
        *LIABILITY_CONCEPTS,
        *EQUITY_CONCEPTS,
        *CASH_CONCEPTS,
        *SHARES_CONCEPTS,
        *DEBT_TOTAL_CONCEPTS,
        *(concept for pair in DEBT_COMPONENT_PAIRS for concept in pair),
    )
)
