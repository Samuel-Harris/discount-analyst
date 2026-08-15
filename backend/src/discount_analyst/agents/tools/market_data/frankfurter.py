from datetime import UTC, date, datetime
from math import isfinite

from pydantic import BaseModel
from pydantic_ai import FunctionToolset

from discount_analyst.agents.tools.http.retrying_client import create_rate_limit_client
from discount_analyst.agents.tools.terminal.infallible_toolset import InfallibleToolset

FRANKFURTER_API_BASE = "https://api.frankfurter.dev"


class CurrencyConversion(BaseModel):
    amount: float
    from_currency: str
    to_currency: str
    rate: float
    rate_date: date
    converted_amount: float


async def convert_currency(
    amount: float, from_currency: str, to_currency: str
) -> CurrencyConversion:
    """Convert an amount using the latest Frankfurter daily exchange rate.

    Fetches ``GET {base}/v2/rate/{from}/{to}`` and multiplies locally. Same-currency
    requests return ``rate=1`` without an HTTP call.

    Args:
        amount: Amount in the source currency. Negative values are allowed so
            cash-flow signs are preserved. Non-finite values (NaN, infinity)
            are rejected.
        from_currency: ISO 4217 source currency code. Case and surrounding
            whitespace are ignored.
        to_currency: ISO 4217 target currency code. Case and surrounding
            whitespace are ignored.

    Returns:
        The converted amount, the rate applied, and the Frankfurter rate date.
    """
    if not isfinite(amount):
        raise ValueError("amount must be a finite number (not NaN or infinity)")

    from_code = from_currency.strip().upper()
    to_code = to_currency.strip().upper()

    if from_code == to_code:
        return CurrencyConversion(
            amount=amount,
            from_currency=from_code,
            to_currency=to_code,
            rate=1.0,
            rate_date=datetime.now(UTC).date(),
            converted_amount=amount,
        )

    async with create_rate_limit_client() as client:
        response = await client.get(
            f"{FRANKFURTER_API_BASE}/v2/rate/{from_code}/{to_code}"
        )
        payload = response.json()

    rate = float(payload["rate"])
    return CurrencyConversion(
        amount=amount,
        from_currency=from_code,
        to_currency=to_code,
        rate=rate,
        rate_date=date.fromisoformat(payload["date"]),
        converted_amount=amount * rate,
    )


def create_frankfurter_toolset() -> InfallibleToolset[None]:
    """Always-on Frankfurter ``convert_currency`` toolset for pipeline agents."""
    toolset = FunctionToolset[None]()
    toolset.add_function(
        convert_currency,
        name="convert_currency",
        docstring_format="google",
        require_parameter_descriptions=True,
    )
    return InfallibleToolset(toolset)
