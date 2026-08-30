from collections import defaultdict
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from discount_analyst.agents.tools.regulatory_data.json_maps import (
    as_object_list,
    as_str_map,
)
from discount_analyst.agents.tools.regulatory_data.models import (
    CanonicalFundamentals,
    PeriodKind,
    missing_fundamental_fields,
)
from discount_analyst.agents.tools.regulatory_data.sec_edgar.concepts import (
    ASSET_CONCEPTS,
    CASH_CONCEPTS,
    Concept,
    DEBT_COMPONENT_PAIRS,
    DEBT_TOTAL_CONCEPTS,
    EQUITY_CONCEPTS,
    LIABILITY_CONCEPTS,
    NET_INCOME_CONCEPTS,
    REVENUE_CONCEPTS,
    SHARES_CONCEPTS,
    TRACKED_CONCEPTS,
)
from discount_analyst.agents.tools.regulatory_data.sec_edgar.tickers import format_cik

_SHARES_UNIT = "shares"


@dataclass(frozen=True, slots=True)
class FactObservation:
    concept: Concept
    unit: str
    value: Decimal
    period_end: date
    filed_at: date
    form: str
    accn: str
    start: date | None = None


@dataclass(frozen=True, slots=True)
class WinningFiling:
    period_end: date
    filed_at: date
    form: str
    accn: str


@dataclass(frozen=True, slots=True)
class SelectedAmount:
    amount: Decimal
    unit: str


def fundamentals_from_companyfacts(
    payload: object,
    *,
    ticker: str,
    issuer_title: str,
    cik: str,
    period_kind: PeriodKind,
    as_of: date | None,
    annual_forms: frozenset[str],
    quarterly_forms: frozenset[str],
) -> CanonicalFundamentals:
    entity_name = issuer_title
    observations: list[FactObservation] = []
    payload_map = as_str_map(payload)
    if payload_map is not None:
        entity_name = str(payload_map.get("entityName") or issuer_title)
        cik = format_cik(payload_map.get("cik") or cik)
        observations = list_observations(payload_map)

    forms = annual_forms if period_kind == "annual" else quarterly_forms
    relevant = [row for row in observations if row.concept in TRACKED_CONCEPTS]
    winning = choose_winning_filing(relevant, forms=forms, as_of=as_of)
    by_concept = _index_observations(relevant)

    revenue = _first_present(by_concept, REVENUE_CONCEPTS, winning, period_kind)
    net_income = _first_present(by_concept, NET_INCOME_CONCEPTS, winning, period_kind)
    total_assets = _first_present(by_concept, ASSET_CONCEPTS, winning, period_kind)
    total_liabilities = _first_present(
        by_concept, LIABILITY_CONCEPTS, winning, period_kind
    )
    equity = _first_present(by_concept, EQUITY_CONCEPTS, winning, period_kind)
    cash = _first_present(by_concept, CASH_CONCEPTS, winning, period_kind)
    shares = _first_present(by_concept, SHARES_CONCEPTS, winning, period_kind)
    debt = _select_debt(by_concept, winning, period_kind)

    revenue_value = None if revenue is None else revenue.amount
    net_income_value = None if net_income is None else net_income.amount
    assets_value = None if total_assets is None else total_assets.amount
    liabilities_value = None if total_liabilities is None else total_liabilities.amount
    equity_value = None if equity is None else equity.amount
    cash_value = None if cash is None else cash.amount
    debt_value = None if debt is None else debt.amount
    shares_value = None if shares is None else shares.amount

    return CanonicalFundamentals(
        identifier=ticker,
        issuer_name=entity_name,
        cik=cik,
        company_number=None,
        currency=_currency_of(
            revenue,
            net_income,
            total_assets,
            total_liabilities,
            equity,
            cash,
            debt,
        ),
        period_kind=period_kind,
        period_end=None if winning is None else winning.period_end,
        filed_at=None if winning is None else winning.filed_at,
        form_type=None if winning is None else winning.form,
        revenue=revenue_value,
        net_income=net_income_value,
        total_assets=assets_value,
        total_liabilities=liabilities_value,
        equity=equity_value,
        cash=cash_value,
        debt=debt_value,
        shares_outstanding=shares_value,
        accounts_filleted=None,
        profit_and_loss_available=(
            revenue_value is not None or net_income_value is not None
        ),
        missing_fields=missing_fundamental_fields(
            revenue=revenue_value,
            net_income=net_income_value,
            total_assets=assets_value,
            total_liabilities=liabilities_value,
            equity=equity_value,
            cash=cash_value,
            debt=debt_value,
            shares_outstanding=shares_value,
        ),
    )


def list_observations(payload: object) -> list[FactObservation]:
    payload_map = as_str_map(payload)
    if payload_map is None:
        return []
    facts_map = as_str_map(payload_map.get("facts"))
    if facts_map is None:
        return []
    observations: list[FactObservation] = []
    for taxonomy, concepts in facts_map.items():
        concepts_map = as_str_map(concepts)
        if concepts_map is None:
            continue
        for concept_name, concept_payload in concepts_map.items():
            concept_map = as_str_map(concept_payload)
            if concept_map is None:
                continue
            units_map = as_str_map(concept_map.get("units"))
            if units_map is None:
                continue
            concept = Concept(taxonomy, concept_name)
            for unit, rows in units_map.items():
                row_list = as_object_list(rows)
                if row_list is None:
                    continue
                for row in row_list:
                    parsed = _parse_observation(concept, unit, row)
                    if parsed is not None:
                        observations.append(parsed)
    return observations


def choose_winning_filing(
    observations: list[FactObservation],
    *,
    forms: frozenset[str],
    as_of: date | None,
) -> WinningFiling | None:
    eligible = [
        row
        for row in observations
        if row.form in forms and (as_of is None or row.filed_at <= as_of)
    ]
    if not eligible:
        return None
    period_end = max(row.period_end for row in eligible)
    at_period = [row for row in eligible if row.period_end == period_end]
    filed_at = max(row.filed_at for row in at_period)
    at_filed = [row for row in at_period if row.filed_at == filed_at]
    chosen = at_filed[0]
    return WinningFiling(
        period_end=chosen.period_end,
        filed_at=chosen.filed_at,
        form=chosen.form,
        accn=chosen.accn,
    )


def reported_decimal(value: object) -> Decimal:
    if isinstance(value, Decimal):
        return value
    if isinstance(value, bool) or value is None:
        raise TypeError("boolean and null values are not reported amounts")
    if isinstance(value, int):
        return Decimal(value)
    if isinstance(value, str):
        return Decimal(value)
    raise TypeError(
        f"unsupported reported value type: {type(value).__name__}; "
        "use int, str, or Decimal"
    )


def _parse_observation(
    concept: Concept,
    unit: str,
    row: object,
) -> FactObservation | None:
    row_map = as_str_map(row)
    if row_map is None:
        return None
    try:
        period_end = date.fromisoformat(str(row_map["end"]))
        filed_at = date.fromisoformat(str(row_map["filed"]))
        form = str(row_map["form"])
        value = reported_decimal(row_map["val"])
    except (KeyError, TypeError, ValueError):
        return None
    start: date | None = None
    raw_start = row_map.get("start")
    if raw_start is not None:
        try:
            start = date.fromisoformat(str(raw_start))
        except ValueError:
            start = None
    return FactObservation(
        concept=concept,
        unit=unit,
        value=value,
        period_end=period_end,
        filed_at=filed_at,
        form=form,
        accn=str(row_map.get("accn") or ""),
        start=start,
    )


def _index_observations(
    observations: list[FactObservation],
) -> dict[Concept, list[FactObservation]]:
    by_concept: dict[Concept, list[FactObservation]] = defaultdict(list)
    for row in observations:
        by_concept[row.concept].append(row)
    return by_concept


def _first_present(
    by_concept: dict[Concept, list[FactObservation]],
    family: tuple[Concept, ...],
    winning: WinningFiling | None,
    period_kind: PeriodKind,
) -> SelectedAmount | None:
    if winning is None:
        return None
    for concept in family:
        matched = _matching_observation(
            by_concept.get(concept, []), winning, period_kind
        )
        if matched is not None:
            return SelectedAmount(amount=matched.value, unit=matched.unit)
    return None


def _select_debt(
    by_concept: dict[Concept, list[FactObservation]],
    winning: WinningFiling | None,
    period_kind: PeriodKind,
) -> SelectedAmount | None:
    total = _first_present(by_concept, DEBT_TOTAL_CONCEPTS, winning, period_kind)
    if total is not None:
        return total
    for left_concept, right_concept in DEBT_COMPONENT_PAIRS:
        left = _first_present(by_concept, (left_concept,), winning, period_kind)
        right = _first_present(by_concept, (right_concept,), winning, period_kind)
        if left is None and right is None:
            continue
        amount = Decimal(0)
        unit = "USD"
        if left is not None:
            amount += left.amount
            unit = left.unit
        if right is not None:
            amount += right.amount
            if left is None:
                unit = right.unit
        return SelectedAmount(amount=amount, unit=unit)
    return None


def _matching_observation(
    candidates: list[FactObservation],
    winning: WinningFiling,
    period_kind: PeriodKind,
) -> FactObservation | None:
    at_period = [row for row in candidates if row.period_end == winning.period_end]
    same_accn = (
        [row for row in at_period if row.accn and row.accn == winning.accn]
        if winning.accn
        else []
    )
    pool = same_accn or [
        row
        for row in at_period
        if row.filed_at == winning.filed_at and row.form == winning.form
    ]
    if not pool:
        return None
    usd_pool = [row for row in pool if row.unit == "USD"]
    ranked = usd_pool or pool
    if period_kind == "quarterly":
        return max(ranked, key=lambda row: row.start or date.min)
    return min(ranked, key=lambda row: row.start or date.max)


def _currency_of(*selected: SelectedAmount | None) -> str | None:
    units = [
        item.unit
        for item in selected
        if item is not None and item.unit.lower() != _SHARES_UNIT
    ]
    if "USD" in units:
        return "USD"
    if units:
        return units[0]
    return None
