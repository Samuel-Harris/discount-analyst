"""Conservative name filters for listed ordinary equity.

NASDAQ Trader files mark some non-equities with ``ETF`` / ``Test Issue`` flags,
but many warrants, rights, units, preferreds, notes, bonds, and funds are only
visible in the security name. Matching is case-insensitive and uses word
boundaries so ordinary names such as ``United`` or ``Wright`` are kept, while
product tokens from the documented reject list are excluded.

LSE issuer reports are filtered with an allow-list on the instrument name:
rows are kept only when the instrument looks like ordinary shares (or common
stock). ``Common Stock`` and ``Ordinary Shares`` themselves are never treated
as reject tokens.
"""

import re

_NON_EQUITY_NAME_PATTERN = re.compile(
    r"\b("
    r"warrants?|rights?|units?|preferred|notes?|bonds?|funds?|"
    r"etfs?|nextshares"
    r")\b",
    re.IGNORECASE,
)

_ORDINARY_EQUITY_MARKERS = (
    "ordinary shares",
    "ordinary share",
    "common stock",
    "common shares",
)


def is_excluded_security_name(security_name: str) -> bool:
    return _NON_EQUITY_NAME_PATTERN.search(security_name) is not None


def is_ordinary_equity_instrument(instrument_name: str) -> bool:
    lowered = instrument_name.casefold()
    return any(marker in lowered for marker in _ORDINARY_EQUITY_MARKERS)
