"""Current portfolio weights supplied to the Curator."""

from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field, model_validator

from discount_analyst.domain.allocations.constants import WEIGHT_SUM_TOLERANCE_PP
from discount_analyst.domain.allocations.invariants import require_unique_casefold


class CurrentPositionWeight(BaseModel):
    ticker: str
    current_weight_pct: float = Field(ge=0, le=100)


class CurrentPortfolioSnapshot(BaseModel):
    as_of: date
    positions: tuple[CurrentPositionWeight, ...]
    cash_weight_pct: float = Field(ge=0, le=100)

    @model_validator(mode="after")
    def validate_snapshot(self) -> CurrentPortfolioSnapshot:
        require_unique_casefold(
            (position.ticker for position in self.positions),
            item_kind="Snapshot tickers",
        )
        total = sum(position.current_weight_pct for position in self.positions)
        total += self.cash_weight_pct
        if abs(total - 100.0) > WEIGHT_SUM_TOLERANCE_PP:
            msg = (
                "Snapshot position weights plus cash must total 100% "
                f"(within {WEIGHT_SUM_TOLERANCE_PP} percentage points); "
                f"got {total}."
            )
            raise ValueError(msg)
        return self


class SterlingPosition(BaseModel):
    ticker: str
    value_gbp: Decimal = Field(ge=0)


class SterlingPortfolioLedger(BaseModel):
    positions: tuple[SterlingPosition, ...]
    cash_gbp: Decimal = Field(ge=0)

    @model_validator(mode="after")
    def validate_unique_tickers(self) -> SterlingPortfolioLedger:
        require_unique_casefold(
            (position.ticker for position in self.positions),
            item_kind="Snapshot tickers",
        )
        return self


def snapshot_from_sterling_ledger(
    ledger: SterlingPortfolioLedger, *, as_of: date
) -> CurrentPortfolioSnapshot:
    total = sum((position.value_gbp for position in ledger.positions), Decimal("0"))
    total += ledger.cash_gbp
    if total == 0:
        return CurrentPortfolioSnapshot(
            as_of=as_of,
            positions=tuple(
                CurrentPositionWeight(ticker=position.ticker, current_weight_pct=0.0)
                for position in ledger.positions
            ),
            cash_weight_pct=100.0,
        )

    rounded_weights = tuple(
        round(float(Decimal("100") * position.value_gbp / total), 2)
        for position in ledger.positions
    )
    if ledger.cash_gbp == 0 and ledger.positions:
        head = rounded_weights[:-1]
        tail = round(100.0 - sum(head), 2)
        position_weights = (*head, tail)
        cash_weight_pct = 0.0
    else:
        position_weights = rounded_weights
        cash_weight_pct = round(100.0 - sum(rounded_weights), 2)

    return CurrentPortfolioSnapshot(
        as_of=as_of,
        positions=tuple(
            CurrentPositionWeight(ticker=position.ticker, current_weight_pct=weight)
            for position, weight in zip(ledger.positions, position_weights, strict=True)
        ),
        cash_weight_pct=cash_weight_pct,
    )


def snapshot_weight_for_ticker(
    snapshot: CurrentPortfolioSnapshot, ticker: str
) -> float | None:
    """Return the stored weight for ``ticker``, or ``None`` if the name is absent."""
    wanted = ticker.casefold()
    for position in snapshot.positions:
        if position.ticker.casefold() == wanted:
            return position.current_weight_pct
    return None
