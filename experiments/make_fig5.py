"""Regenerate Fig. 5 (the waterfall) from the unified headline run."""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OUTF = ROOT.parent / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本" / "figures"
d = json.loads((ROOT / "results" / "routeA_r3" / "headline_consistent" / "summary.json").read_text(encoding="utf-8"))
A = d["arms"]

plt.rcParams.update({"font.size": 8, "axes.linewidth": 0.7, "savefig.dpi": 300})


def mean(k):
    return A[k]["summary"]["mean"]


def sd(k):
    return A[k]["summary"]["sd"]


bars = [
    ("PPO-MLP\nno knowledge", mean("ppomlp_none"), sd("ppomlp_none"), "#b0b0b0"),
    ("same knowledge\nas a reward\n($\\lambda$=8)", mean("lam8"), sd("lam8"), "#e0a060"),
    ("same knowledge\nas a shield\n(on PPO-MLP)", mean("ppomlp_rule16"), sd("ppomlp_rule16"), "#7fb3d5"),
    ("mined-rule\ncampaign arm\n(16 s, no margin)", mean("almond_rule16"), sd("almond_rule16"), "#4a7fb5"),
    ("tuned constant\n18 s, no learning", mean("maxel18"), sd("maxel18"), "#c0392b"),
]

fig, ax = plt.subplots(figsize=(6.4, 3.2))
xs = np.arange(len(bars))
ax.bar(xs, [b[1] for b in bars], yerr=[b[2] for b in bars], capsize=3,
       color=[b[3] for b in bars], width=0.62,
       error_kw=dict(elinewidth=0.8, ecolor="#444444"))
for x, (lab, v, s, _c) in zip(xs, bars):
    ax.text(x, v + s + 1.2, f"{v:.1f}", ha="center", fontsize=8)
ax.set_xticks(xs)
ax.set_xticklabels([b[0] for b in bars], fontsize=6.4)
ax.set_ylim(60, 102)
ax.set_ylabel("polar handover success (%)")
ax.grid(axis="y", ls=":", lw=0.5, alpha=0.6)
ax.set_axisbelow(True)
fig.tight_layout()
fig.savefig(OUTF / "fig2_gap.png")
fig.savefig(OUTF / "fig2_gap.pdf")
print("fig5 (fig2_gap.png) regenerated:",
      [round(b[1], 2) for b in bars])
