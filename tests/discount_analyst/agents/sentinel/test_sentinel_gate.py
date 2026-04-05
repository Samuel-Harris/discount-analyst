"""Unit tests for ``sentinel_proceeds_to_valuation``."""

import pytest

from discount_analyst.agents.sentinel.schema import (
    ThesisVerdict,
    sentinel_proceeds_to_valuation,
)


@pytest.mark.parametrize(
    ("verdict", "proceeds"),
    [
        ("Thesis intact — proceed to valuation", True),
        ("Thesis intact with reservations — proceed with noted caveats", True),
        ("Thesis weakened — do not proceed", False),
        ("Thesis broken — do not proceed", False),
    ],
)
def test_sentinel_proceeds_to_valuation(verdict: str, proceeds: bool) -> None:
    assert sentinel_proceeds_to_valuation(ThesisVerdict(verdict)) is proceeds
