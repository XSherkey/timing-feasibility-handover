"""Where does the 21-point reliability gap actually come from?

One bar per intervention, same twin, same held-out test split, error bar over seeds.
The point of the figure is that the *knowledge* (the preparation threshold) is what
moves the number, and that a hand-tuned constant with no learning at all reaches
the same place - a fact the manuscript has to state rather than hide.
"""
from __future__ import annotations

import json
import statistics as st
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]

# (label, mean, sd, colour, hatched)
BARS = [
    ("PPO-MLP\n(reward only)", 72.6, 16.1, "#c0392b", False),
    ("same knowledge\nas reward penalty", 72.1, 9.3, "#e67e22", False),
    ("PPO-MLP policy\n+ decision shield", 91.8, 1.1, "#2980b9", False),
    ("max-elevation + 18 s\n(no learning at all)", 94.0, 0.7, "#7f8c8d", True),
    ("ALMOND\n(learned policy + shield)", 93.6, 0.7, "#16a085", False),
]


def main() -> int:
    fig, ax = plt.subplots(figsize=(8.2, 4.2))
    xs = range(len(BARS))
    for i, (label, mean, sd, colour, hatch) in enumerate(BARS):
        ax.bar(i, mean, yerr=sd, capsize=4, color=colour, hatch="//" if hatch else None,
               edgecolor="white", linewidth=0.6, width=0.62,
               error_kw=dict(lw=1.2, ecolor="#333333"))
        ax.text(i, mean + sd + 1.2, f"{mean:.1f}", ha="center", va="bottom", fontsize=10, fontweight="bold")
    ax.set_xticks(list(xs))
    ax.set_xticklabels([b[0] for b in BARS], fontsize=8.5)
    ax.set_ylabel("Arctic handover success rate (%)", fontsize=10)
    ax.set_ylim(0, 108)
    ax.axhline(94.0, ls=":", lw=1, color="#555555")
    ax.text(4.45, 94.8, "tuned-constant ceiling", ha="right", fontsize=8, color="#555555")
    ax.grid(axis="y", alpha=0.25, ls=":")
    ax.set_axisbelow(True)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.set_title("The reliability gap is a threshold, not a controller", fontsize=11)
    fig.tight_layout()
    out = ROOT / "results" / "figures_1023" / "fig_gap_decomposition.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=200)
    print("wrote", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
