"""R7 (v9): regenerate Fig. 2 with the ledger name on the bar label."""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT.parent / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本" / "figures"
plt.rcParams.update({"font.size": 8, "axes.linewidth": 0.7, "savefig.dpi": 300})


def main() -> int:
    vals = [("PPO-MLP\nno knowledge", 72.6, "#b0b0b0"),
            ("same knowledge\nin the reward\n($\\lambda$=8, best)", 84.4, "#e0a060"),
            ("same knowledge\nas a shield\n(on PPO-MLP)", 91.8, "#7fb3d5"),
            ("mined-rule\ncampaign arm\n(16 s, no margin)", 93.6, "#4a7fb5"),
            ("tuned constant\n18 s, no learning", 94.0, "#c0392b")]
    fig, ax = plt.subplots(figsize=(6.4, 3.2))
    xs = np.arange(len(vals))
    ax.bar(xs, [v[1] for v in vals], color=[v[2] for v in vals], width=0.62)
    for x, (lab, v, _c) in zip(xs, vals):
        ax.text(x, v + 0.6, f"{v:.1f}", ha="center", fontsize=8)
    ax.set_xticks(xs)
    ax.set_xticklabels([v[0] for v in vals], fontsize=6.4)
    ax.set_ylim(60, 100)
    ax.set_ylabel("polar handover success (%)")
    ax.grid(axis="y", ls=":", lw=0.5, alpha=0.6)
    ax.set_axisbelow(True)
    fig.tight_layout()
    fig.savefig(OUT / "fig2_gap.png")
    fig.savefig(OUT / "fig2_gap.pdf")
    print("fig2 regenerated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
