from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from lxml import etree

from discount_analyst.agents.tools.regulatory_data.companies_house.concepts import (
    ENTITY_NAME_LOCAL_NAMES,
)

_XSI_NIL = "{http://www.w3.org/2001/XMLSchema-instance}nil"
_NON_CURRENCY_UNITS = frozenset({"PURE", "SHARES", "SHARES-IAS"})


@dataclass(frozen=True, slots=True)
class ParsedIxbrl:
    facts: dict[str, Decimal]
    currency: str | None
    issuer_name: str | None


@dataclass(frozen=True, slots=True)
class _Context:
    period_end: date | None
    dimensional: bool


@dataclass(frozen=True, slots=True)
class _TaggedValue:
    value: Decimal
    period_end: date | None
    dimensional: bool
    currency: str | None


def parse_ixbrl(path: Path) -> ParsedIxbrl:
    tree = _parse_tree(path)
    root = tree.getroot()
    contexts = _parse_contexts(root)
    units = _parse_units(root)
    tagged: dict[str, list[_TaggedValue]] = {}
    for element in root.xpath("//*[local-name()='nonFraction']"):
        local_name = _concept_local_name(element)
        if local_name is None or _is_nil(element):
            continue
        value = _decimal_from_element(element)
        if value is None:
            continue
        context = contexts.get(_attr(element, "contextRef", "contextref") or "")
        tagged.setdefault(local_name, []).append(
            _TaggedValue(
                value=value,
                period_end=None if context is None else context.period_end,
                dimensional=False if context is None else context.dimensional,
                currency=_currency_for_fact(
                    _attr(element, "unitRef", "unitref"), units
                ),
            )
        )
    current_end = _latest_period_end(tagged)
    facts: dict[str, Decimal] = {}
    currency: str | None = None
    for local_name, values in tagged.items():
        chosen = _select_current(values, current_end)
        if chosen is None:
            continue
        facts[local_name] = chosen.value
        if currency is None and chosen.currency is not None:
            currency = chosen.currency
    issuer_name = _select_issuer_name(root, contexts, current_end)
    return ParsedIxbrl(facts=facts, currency=currency, issuer_name=issuer_name)


def _parse_tree(path: Path) -> Any:
    try:
        return etree.parse(str(path))
    except etree.XMLSyntaxError:
        return etree.parse(str(path), etree.HTMLParser())


def _parse_contexts(root: Any) -> dict[str, _Context]:
    parsed: dict[str, _Context] = {}
    for element in root.xpath("//*[local-name()='context']"):
        context_id = element.get("id")
        if not context_id:
            continue
        instant = _first_child_text(element, "instant")
        end_date = _first_child_text(element, "endDate")
        period_end = _parse_iso_date(instant or end_date)
        dimensional = bool(
            element.xpath(".//*[local-name()='explicitMember']")
            or element.xpath(".//*[local-name()='typedMember']")
        )
        parsed[context_id] = _Context(period_end=period_end, dimensional=dimensional)
    return parsed


def _parse_units(root: Any) -> dict[str, str]:
    parsed: dict[str, str] = {}
    for element in root.xpath("//*[local-name()='unit']"):
        unit_id = element.get("id")
        if not unit_id:
            continue
        measures = [
            "".join(measure.itertext()).strip()
            for measure in element.xpath(".//*[local-name()='measure']")
        ]
        if len(measures) != 1:
            continue
        token = measures[0].rsplit(":", 1)[-1].upper()
        if not token or token in _NON_CURRENCY_UNITS:
            continue
        parsed[unit_id] = token
    return parsed


def _currency_for_fact(unit_ref: str | None, units: dict[str, str]) -> str | None:
    if unit_ref is None:
        return None
    mapped = units.get(unit_ref)
    if mapped is not None:
        return mapped
    token = unit_ref.strip().upper()
    if len(token) == 3 and token.isalpha() and token not in _NON_CURRENCY_UNITS:
        return token
    return None


def _latest_period_end(tagged: dict[str, list[_TaggedValue]]) -> date | None:
    ends = [
        item.period_end
        for values in tagged.values()
        for item in values
        if item.period_end is not None
    ]
    return max(ends) if ends else None


def _select_current(
    values: list[_TaggedValue], current_end: date | None
) -> _TaggedValue | None:
    pool = values
    if current_end is not None:
        same_period = [item for item in values if item.period_end == current_end]
        if same_period:
            pool = same_period
        else:
            pool = [item for item in values if item.period_end is None]
            if not pool:
                return None
    undimensional = [item for item in pool if not item.dimensional]
    return (undimensional or pool)[0]


def _select_issuer_name(
    root: Any, contexts: dict[str, _Context], current_end: date | None
) -> str | None:
    candidates: list[tuple[str, date | None, bool]] = []
    for element in root.xpath("//*[local-name()='nonNumeric']"):
        local_name = _concept_local_name(element)
        if local_name not in ENTITY_NAME_LOCAL_NAMES:
            continue
        text = " ".join("".join(element.itertext()).split())
        if not text:
            continue
        context = contexts.get(_attr(element, "contextRef", "contextref") or "")
        candidates.append(
            (
                text,
                None if context is None else context.period_end,
                False if context is None else context.dimensional,
            )
        )
    pool = candidates
    if current_end is not None:
        same_period = [item for item in candidates if item[1] == current_end]
        pool = same_period or [item for item in candidates if item[1] is None]
    if not pool:
        return None
    undimensional = [item for item in pool if not item[2]]
    return (undimensional or pool)[0][0]


def _first_child_text(element: Any, local_name: str) -> str | None:
    matches = element.xpath(f".//*[local-name()='{local_name}']")
    if not matches:
        return None
    text = "".join(matches[0].itertext()).strip()
    return text or None


def _parse_iso_date(raw: str | None) -> date | None:
    if raw is None:
        return None
    try:
        return date.fromisoformat(raw[:10])
    except ValueError:
        return None


def _concept_local_name(element: Any) -> str | None:
    raw = _attr(element, "name")
    if raw is None:
        return None
    name = raw.strip()
    if not name:
        return None
    if "}" in name:
        return name.rsplit("}", 1)[-1]
    if ":" in name:
        return name.rsplit(":", 1)[-1]
    return name


def _attr(element: Any, *names: str) -> str | None:
    for name in names:
        value = element.get(name)
        if value:
            return value
    return None


def _is_nil(element: Any) -> bool:
    raw = element.get(_XSI_NIL) or element.get("nil")
    if raw is None:
        return False
    return raw.strip().lower() in {"true", "1"}


def _decimal_from_element(element: Any) -> Decimal | None:
    text = "".join(element.itertext()).strip().replace(",", "").replace(" ", "")
    if not text or text == "-":
        return None
    try:
        value = Decimal(text)
    except InvalidOperation:
        return None
    scale_raw = _attr(element, "scale")
    if scale_raw:
        try:
            value *= Decimal(10) ** int(scale_raw)
        except (InvalidOperation, ValueError):
            return None
    if _attr(element, "sign") == "-":
        value = -value
    return value
