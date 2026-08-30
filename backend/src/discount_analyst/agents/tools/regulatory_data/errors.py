REFRESH_COMMAND = "discount-analyst admin refresh-regulatory-data"


class RegulatoryDataError(Exception):
    """Base error for official exchange, SEC, and Companies House tools."""


class ColdCacheError(RegulatoryDataError):
    """Raised when a required local snapshot has never been published."""

    def __init__(self, source: str, *, refresh_flags: str = "") -> None:
        command = REFRESH_COMMAND
        if refresh_flags:
            command = f"{command} {refresh_flags}"
        super().__init__(
            f"{source} cache is missing or incomplete. "
            f"Run `{command}` to download official bulk data."
        )
        self.source = source
        self.refresh_command = command


class SecUserAgentMissingError(RegulatoryDataError):
    """Raised when SEC refresh or live gap-fill is attempted without a User-Agent."""

    def __init__(self) -> None:
        super().__init__(
            "SEC__USER_AGENT is missing or empty. Set it to an application name "
            "and contact details (for example "
            "'DiscountAnalyst/0.1 (analyst@example.com)') before running "
            f"`{REFRESH_COMMAND} --sec` or querying SEC company facts that need "
            "a live gap-fill."
        )


class UnknownTickerError(RegulatoryDataError):
    """Raised when a ticker cannot be mapped to an SEC CIK."""

    def __init__(self, ticker: str) -> None:
        super().__init__(
            f"No SEC CIK mapping for ticker {ticker!r}. Confirm the symbol is a "
            "US-listed equity in the NASDAQ Trader directory."
        )
        self.ticker = ticker


class SchemaValidationError(RegulatoryDataError):
    """Raised when a downloaded official file does not match the expected headers."""

    def __init__(self, source: str, detail: str) -> None:
        super().__init__(f"{source} schema validation failed: {detail}")
        self.source = source
