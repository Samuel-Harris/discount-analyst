"""Rich reporting helpers for valuation method summaries."""

from __future__ import annotations

from typing import cast

from rich.table import Table


def method_summary_table(methods: list[dict[str, object]], *, title: str) -> Table:
    table = Table(title=title, show_header=True, header_style="bold cyan")
    table.add_column("Method", style="cyan")
    table.add_column("Role", style="yellow")
    table.add_column("Value/share", justify="right")
    table.add_column("Range", justify="right")
    table.add_column("Weight", justify="right")
    for method in methods:
        value = cast(float | None, method.get("value_per_share"))
        low = cast(float | None, method.get("low_value_per_share"))
        high = cast(float | None, method.get("high_value_per_share"))
        weight = cast(float | None, method.get("weight_pct"))
        table.add_row(
            str(method.get("method", "")),
            str(method.get("role", "")),
            "" if value is None else f"{float(value):.2f}",
            ""
            if low is None or high is None
            else f"{float(low):.2f}-{float(high):.2f}",
            "" if weight is None else f"{float(weight):.1f}%",
        )
    return table
