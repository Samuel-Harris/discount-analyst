"""Current portfolio weights supplied to the Allocator."""

from datetime import date

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


def snapshot_weight_for_ticker(
    snapshot: CurrentPortfolioSnapshot, ticker: str
) -> float | None:
    """Return the stored weight for ``ticker``, or ``None`` if the name is absent."""
    wanted = ticker.casefold()
    for position in snapshot.positions:
        if position.ticker.casefold() == wanted:
            return position.current_weight_pct
    return None
