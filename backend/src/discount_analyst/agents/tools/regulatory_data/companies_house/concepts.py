from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal

REVENUE_LOCAL_NAMES: tuple[str, ...] = ("Revenue", "TurnoverRevenue", "Turnover")
PROFIT_LOCAL_NAMES: tuple[str, ...] = ("ProfitLoss",)
ASSETS_LOCAL_NAMES: tuple[str, ...] = ("Assets",)
ASSETS_SUM_LOCAL_NAMES: tuple[str, ...] = ("FixedAssets", "CurrentAssets")
LIABILITIES_LOCAL_NAMES: tuple[str, ...] = ("Liabilities",)
LIABILITIES_SUM_LOCAL_NAMES: tuple[str, ...] = (
    "CreditorsDueWithinOneYear",
    "CreditorsDueAfterOneYear",
)
EQUITY_LOCAL_NAMES: tuple[str, ...] = (
    "Equity",
    "NetAssetsLiabilitiesIncludingPensionAssetLiability",
)
CASH_LOCAL_NAMES: tuple[str, ...] = ("CashAndCashEquivalents", "CashBankOnHand")
DEBT_LOCAL_NAMES: tuple[str, ...] = ("Borrowings",)
ENTITY_NAME_LOCAL_NAMES: tuple[str, ...] = (
    "NameOfReportingEntityOrOtherMeansOfIdentification",
    "EntityCurrentLegalOrRegisteredName",
)


@dataclass(frozen=True, slots=True)
class MappedAmounts:
    revenue: Decimal | None
    net_income: Decimal | None
    total_assets: Decimal | None
    total_liabilities: Decimal | None
    equity: Decimal | None
    cash: Decimal | None
    debt: Decimal | None
    shares_outstanding: Decimal | None
    accounts_filleted: bool
    profit_and_loss_available: bool


def first_present(
    facts: Mapping[str, Decimal], names: tuple[str, ...]
) -> Decimal | None:
    for name in names:
        value = facts.get(name)
        if value is not None:
            return value
    return None


def sum_present(facts: Mapping[str, Decimal], names: tuple[str, ...]) -> Decimal | None:
    total: Decimal | None = None
    for name in names:
        value = facts.get(name)
        if value is None:
            continue
        total = value if total is None else total + value
    return total


def map_facts(facts: Mapping[str, Decimal]) -> MappedAmounts:
    revenue = first_present(facts, REVENUE_LOCAL_NAMES)
    net_income = first_present(facts, PROFIT_LOCAL_NAMES)
    total_assets = first_present(facts, ASSETS_LOCAL_NAMES)
    if total_assets is None:
        total_assets = sum_present(facts, ASSETS_SUM_LOCAL_NAMES)
    total_liabilities = first_present(facts, LIABILITIES_LOCAL_NAMES)
    if total_liabilities is None:
        total_liabilities = sum_present(facts, LIABILITIES_SUM_LOCAL_NAMES)
    equity = first_present(facts, EQUITY_LOCAL_NAMES)
    cash = first_present(facts, CASH_LOCAL_NAMES)
    debt = first_present(facts, DEBT_LOCAL_NAMES)
    accounts_filleted = revenue is None and net_income is None
    return MappedAmounts(
        revenue=revenue,
        net_income=net_income,
        total_assets=total_assets,
        total_liabilities=total_liabilities,
        equity=equity,
        cash=cash,
        debt=debt,
        shares_outstanding=None,
        accounts_filleted=accounts_filleted,
        profit_and_loss_available=not accounts_filleted,
    )
