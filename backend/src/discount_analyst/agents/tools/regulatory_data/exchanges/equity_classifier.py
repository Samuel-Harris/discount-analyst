"""Conservative name filters for listed ordinary equity.

NASDAQ Trader files mark some non-equities with ``ETF`` / ``Test Issue`` flags,
but many warrants, rights, units, preferreds, notes, bonds, and funds are only
visible in the security name. Matching is case-insensitive and uses word
boundaries so ordinary names such as ``United`` or ``Wright`` are kept, while
product tokens from the documented reject list are excluded.
"""

import re

_NON_EQUITY_NAME_PATTERN = re.compile(
    r"\b("
    r"warrants?|rights?|units?|preferred|notes?|bonds?|funds?|"
    r"etfs?|nextshares"
    r")\b",
    re.IGNORECASE,
)


def is_excluded_security_name(security_name: str) -> bool:
    return _NON_EQUITY_NAME_PATTERN.search(security_name) is not None
