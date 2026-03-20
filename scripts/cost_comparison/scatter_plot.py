#!/usr/bin/env python3
"""Scatter plot: Accuracy vs Cost per test, with Pareto frontier for each benchmark."""

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle
from matplotlib.text import Text
from matplotlib.legend_handler import HandlerBase


class HandlerTwoToneBox(HandlerBase):
    """Legend handler: one box with green top/left edge, purple bottom/right edge."""

    def __init__(self, vals_color: str, finance_color: str, **kwargs):
        super().__init__(**kwargs)
        self.vals_color = vals_color
        self.finance_color = finance_color

    def create_artists(
        self, legend, orig_handle, xdescent, ydescent, width, height, fontsize, trans
    ):
        side = height * 1.35  # slightly larger than markersize=10 square markers
        x0 = xdescent + (width - side) / 2
        y0 = ydescent + (height - side) / 2
        x1, y1 = x0 + side, y0 + side
        artists = []
        rect = Rectangle(
            (x0, y0),
            side,
            side,
            facecolor="white",
            edgecolor="none",
            transform=trans,
        )
        artists.append(rect)
        for (px1, py1), (px2, py2), color in [
            ((x0, y1), (x1, y1), self.vals_color),  # top
            ((x0, y0), (x1, y0), self.finance_color),  # bottom
            ((x0, y0), (x0, y1), self.vals_color),  # left
            ((x1, y0), (x1, y1), self.finance_color),  # right
        ]:
            line = Line2D(
                [px1, px2],
                [py1, py2],
                color=color,
                linewidth=1.5,
                transform=trans,
            )
            artists.append(line)
        return artists


MODELS = [
    "Claude Opus 4.6 (thinking)",
    "Claude Opus 4.5 (thinking)",
    "Claude Sonnet 4.6",
    "Claude Sonnet 4.5 (Thinking)",
    "Gemini 3.1 pro-preview",
    "Gemini 3 pro-preview",
    "GPT 5.4",
    "GPT 5.2",
    "GPT 5.1",
    "GPT 5.4 (flex tier)",
    "GPT 5.2 (flex tier)",
    "GPT 5.1 (flex tier)",
]

# (accuracy %, cost USD)
VALS = [
    (66.06, 1.00),
    (63.11, 0.98),
    (66.82, 0.78),
    (60.19, 0.76),
    (64.86, 0.57),
    (61.44, 0.34),
    (64.59, 0.71),
    (64.11, 0.78),
    (60.93, 0.28),
    (64.59, 0.355),  # GPT 5.4 flex tier
    (64.11, 0.39),  # GPT 5.2 flex tier
    (60.93, 0.14),  # GPT 5.1 flex tier
]

FINANCE = [
    (60.05, 1.11),
    (58.81, 1.50),
    (63.33, 1.44),
    (54.50, 1.10),
    (59.72, 0.87),
    (55.15, 0.56),
    (57.15, 1.41),
    (58.53, 0.98),
    (55.31, 0.47),
    (57.15, 0.705),  # GPT 5.4 flex tier
    (58.53, 0.49),  # GPT 5.2 flex tier
    (55.31, 0.235),  # GPT 5.1 flex tier
]


def pareto_frontier(points: list[tuple[float, float]]) -> list[tuple[float, float]]:
    """Points (acc, cost) sorted by cost; keep those with max accuracy so far."""
    sorted_ = sorted(points, key=lambda p: p[1])  # by cost
    frontier = []
    max_acc = -1.0
    for acc, cost in sorted_:
        if acc > max_acc:
            max_acc = acc
            frontier.append((acc, cost))
    return frontier


def main() -> None:
    pareto_vals = pareto_frontier(VALS)
    pareto_finance = pareto_frontier(FINANCE)

    fig, ax = plt.subplots(figsize=(9, 6))

    # Pareto curves
    ax.plot(
        [c for _, c in pareto_vals],
        [a for a, _ in pareto_vals],
        color="#059669",
        linewidth=2,
        label="Pareto frontier (Vals Index)",
        zorder=2,
    )
    ax.plot(
        [c for _, c in pareto_finance],
        [a for a, _ in pareto_finance],
        color="#7c3aed",
        linewidth=2,
        label="Pareto frontier (Finance Agent v1.1)",
        zorder=2,
    )

    # Scatter points
    ax.scatter(
        [c for _, c in VALS],
        [a for a, _ in VALS],
        c="#2563eb",
        s=80,
        marker="o",
        label="Vals Index",
        edgecolors="#1e40af",
        linewidths=1,
        zorder=3,
    )
    ax.scatter(
        [c for _, c in FINANCE],
        [a for a, _ in FINANCE],
        c="#dc2626",
        s=80,
        marker="s",
        label="Finance Agent v1.1",
        edgecolors="#b91c1c",
        linewidths=1,
        zorder=3,
    )

    # Connect each model's two points; blue (Vals) to red (Finance); label on line
    LABEL_OFFSETS = {
        "GPT 5.1": (-0.01, 0),
        "GPT 5.4": (-0.02, 0),
        "Claude Opus 4.6 (thinking)": (0.11, 0),
        "Claude Sonnet 4.6": (0.02, 0),
        "Gemini 3 pro-preview": (0.08, 0),
    }
    VALS_COLOR = "#059669"
    FINANCE_COLOR = "#7c3aed"
    BLUE = "#2563eb"
    RED = "#dc2626"

    bbox_style = dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.9)
    two_tone_texts: list[tuple[Text, float, float]] = []  # (text_obj, lx, ly)

    for i, model in enumerate(MODELS):
        v_pt = VALS[i]
        f_pt = FINANCE[i]
        v_cost, v_acc = v_pt[1], v_pt[0]
        f_cost, f_acc = f_pt[1], f_pt[0]
        mid_x = (v_cost + f_cost) / 2
        mid_y = (v_acc + f_acc) / 2
        # Blue segment (Vals) -> midpoint, red segment midpoint -> (Finance)
        ax.plot(
            [v_cost, mid_x],
            [v_acc, mid_y],
            color=BLUE,
            linestyle="--",
            alpha=0.7,
            zorder=1,
        )
        ax.plot(
            [mid_x, f_cost],
            [mid_y, f_acc],
            color=RED,
            linestyle="--",
            alpha=0.7,
            zorder=1,
        )
        dx, dy = LABEL_OFFSETS.get(model, (0, 0))
        lx, ly = mid_x + dx, mid_y + dy

        on_v = v_pt in pareto_vals
        on_f = f_pt in pareto_finance
        if on_v and on_f:
            txt = ax.text(
                lx,
                ly,
                model,
                fontsize=8,
                ha="center",
                va="center",
                zorder=4,
                bbox={**bbox_style, "edgecolor": "none"},
            )
            two_tone_texts.append((txt, lx, ly))
        else:
            edgecolor = VALS_COLOR if on_v else (FINANCE_COLOR if on_f else "gray")
            ax.text(
                lx,
                ly,
                model,
                fontsize=8,
                ha="center",
                va="center",
                zorder=4,
                bbox={**bbox_style, "edgecolor": edgecolor, "linewidth": 1.5},
            )

    # Draw two-tone edges over the bbox (must match bbox size); need render pass first
    fig.canvas.draw()
    for txt, lx, ly in two_tone_texts:
        patch = txt.get_bbox_patch()
        if patch is not None:
            bbox = patch.get_window_extent().transformed(ax.transData.inverted())
            x1, x2 = bbox.xmin, bbox.xmax
            y1, y2 = bbox.ymin, bbox.ymax
            ax.plot([x1, x2], [y2, y2], color=VALS_COLOR, linewidth=1.5, zorder=5)
            ax.plot([x1, x2], [y1, y1], color=FINANCE_COLOR, linewidth=1.5, zorder=5)
            ax.plot([x1, x1], [y1, y2], color=VALS_COLOR, linewidth=1.5, zorder=5)
            ax.plot([x2, x2], [y1, y2], color=FINANCE_COLOR, linewidth=1.5, zorder=5)

    ax.set_xlabel("Cost per test (USD)")
    ax.set_ylabel("Accuracy (%)")
    ax.set_title("Models: Accuracy vs Cost per Test")

    # Add label edge colour meaning to legend
    class TwoToneBoxHandle:
        """Placeholder for legend handler."""

    handles, labels = ax.get_legend_handles_labels()
    handles += [
        Line2D(
            [0],
            [0],
            color="none",
            marker="s",
            markerfacecolor="white",
            markeredgecolor=VALS_COLOR,
            markersize=10,
            markeredgewidth=1.5,
        ),
        Line2D(
            [0],
            [0],
            color="none",
            marker="s",
            markerfacecolor="white",
            markeredgecolor=FINANCE_COLOR,
            markersize=10,
            markeredgewidth=1.5,
        ),
        TwoToneBoxHandle(),
    ]
    labels += [
        "On Vals Index Pareto frontier only",
        "On Finance Agent v1.1 Pareto frontier only",
        "On both Pareto frontiers",
    ]
    ax.legend(
        handles=handles,
        labels=labels,
        loc="lower right",
        handler_map={TwoToneBoxHandle: HandlerTwoToneBox(VALS_COLOR, FINANCE_COLOR)},
    )
    ax.grid(True, alpha=0.3)
    ax.set_xlim(0.0, 1.6)
    ax.set_ylim(54, 68)
    plt.tight_layout()

    out = __file__.replace(".py", ".png")
    plt.savefig(out, dpi=150)
    print(f"Saved {out}")
    # plt.show()  # uncomment to display interactively


if __name__ == "__main__":
    main()
