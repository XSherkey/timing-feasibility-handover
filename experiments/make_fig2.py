"""R5: Fig. 2 (per-seed factorial) from the unified run, plus every dependent text number."""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OUTF = ROOT.parent / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本" / "figures"
fc = json.loads((ROOT / "results" / "routeA_r3" / "factorial_consistent" / "summary.json").read_text(encoding="utf-8"))
A = fc["arms"]
plt.rcParams.update({"font.size": 8, "axes.linewidth": 0.7, "savefig.dpi": 300})


def main_fig() -> None:
    series = [("no shield", "none", "#b0b0b0", -0.30),
              ("$\\tau$ = 16 s (mined $\\tau^*$)", "rule16", "#9cc3e0", -0.10),
              ("$\\tau$ = 18 s (deployed)", "rule18", "#4a7fb5", 0.10),
              ("$\\tau$ = 20 s (ablation)", "rule20", "#2e5f8a", 0.30)]
    fig, ax = plt.subplots(figsize=(6.6, 3.0))
    xs = np.arange(10)
    for lab, key, col, off in series:
        v = np.asarray(A[key]["polar"], dtype=float)
        ax.bar(xs + off, v, width=0.19, color=col,
               label="%s  (%.2f $\\pm$ %.2f)" % (lab, v.mean(), v.std(ddof=1)))
    ax.set_xlabel("independent policy (seed)")
    ax.set_ylabel("polar handover success (%)")
    ax.set_ylim(40, 100)
    ax.set_xticks(xs)
    ax.set_xticklabels([str(i) for i in range(10)])
    ax.legend(fontsize=6.0, frameon=False, ncol=2, loc="lower center", bbox_to_anchor=(0.5, 1.0))
    ax.grid(axis="y", ls=":", lw=0.5, alpha=0.6)
    ax.set_axisbelow(True)
    fig.tight_layout()
    fig.savefig(OUTF / "fig3_policy_independence.png")
    fig.savefig(OUTF / "fig3_policy_independence.pdf")
    print("Fig. 2 regenerated:",
          {k: round(A[k]["summary"]["mean"], 2) for k in ("none", "rule16", "rule18", "rule20", "oracle")})


if __name__ == "__main__":
    main_fig()
