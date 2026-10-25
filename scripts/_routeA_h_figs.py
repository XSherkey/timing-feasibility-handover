"""Phase H figures: (1) advance-distribution comparison, (2) drift response of the
constant vs naive PCS vs conservative PCS."""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "routeA" / "figures"
OUT.mkdir(parents=True, exist_ok=True)
BUCKETS = [6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26]


def fig_adv() -> None:
    rows = json.load(open(ROOT / "results" / "routeA" / "h1_advance_dist.json", encoding="utf-8"))
    arms = {"penalty_lam8": ("λ=8 (knowledge in weights)", "#c0392b"),
            "no_knowledge": ("no knowledge", "#2980b9")}
    fig, ax = plt.subplots(figsize=(7.2, 3.6), dpi=160)
    width = 0.38
    for k, (arm, (label, color)) in enumerate(arms.items()):
        sel = [r for r in rows if r["arm"] == arm]
        share = np.zeros(len(BUCKETS))
        for r in sel:
            share += np.array([r["ref"]["hist"][str(b)] for b in BUCKETS])
        share /= max(len(sel), 1)
        ax.bar(np.arange(len(BUCKETS)) + (k - 0.5) * width, share * 100, width,
               label=f"{label}  (mean {np.mean([r['ref']['mean'] for r in sel]):.1f}s, "
                     f"sd {np.mean([r['ref']['sd'] for r in sel]):.1f})",
               color=color, alpha=0.85)
    ax.axvline(BUCKETS.index(16) - 0.5, color="k", ls="--", lw=1)
    ax.text(BUCKETS.index(16) - 0.4, ax.get_ylim()[1] * 0.92, "16 s", fontsize=8)
    ax.set_xticks(range(len(BUCKETS)))
    ax.set_xticklabels([str(b) for b in BUCKETS])
    ax.set_xlabel("handover advance chosen at polar sites (s)")
    ax.set_ylabel("share of attempts (%)")
    ax.set_title("H1: the penalised policy is not narrower - it is wider", fontsize=10)
    ax.legend(fontsize=7, frameon=False)
    fig.tight_layout()
    fig.savefig(OUT / "h1_advance_distribution.png")
    print("wrote", OUT / "h1_advance_distribution.png")


def fig_drift() -> None:
    h3 = json.load(open(ROOT / "results" / "routeA" / "g3_drift_table_5seed.json", encoding="utf-8"))
    h2 = json.load(open(ROOT / "results" / "routeA" / "h2_margin.json", encoding="utf-8"))
    drifts = [0.0, 2.0, 3.2, 4.4]
    const, naive = [], []
    for d in drifts:
        acq = d + 1.2
        sel = [r for r in h3 if abs(r["acq"] - acq) < 1e-6]
        const.append(np.mean([r["fixed18"] for r in sel]))
        naive.append(np.mean([r["calib"] for r in sel]))
    cons_pts = []
    for phys, d in (("ref", 0.0), ("sig32", 2.0), ("drift44", 3.2)):
        sel = [r for r in h2 if r["physics"] == phys]
        cons_pts.append((d, np.mean([r["m2"] for r in sel])))

    fig, ax = plt.subplots(figsize=(6.4, 3.4), dpi=160)
    ax.plot(drifts, const, "o-", color="#c0392b", lw=1.8, label="constant 18 s (5 seeds)")
    ax.plot(drifts, naive, "s--", color="#7f8c8d", lw=1.5, label="naive PCS, no margin (5 seeds)")
    ax.plot([p[0] for p in cons_pts], [p[1] for p in cons_pts], "^-", color="#27ae60",
            lw=1.8, label="conservative PCS, m=2 s (5 seeds)")
    ax.axvspan(2.0, 3.2, color="grey", alpha=0.06)
    ax.annotate("constant loses 6-8 pp\nonce drift > 2 s", xy=(3.25, 89.2), xytext=(1.45, 91.0),
                fontsize=7.5, arrowprops=dict(arrowstyle="->", lw=0.8))
    ax.set_xlabel("extra acquisition time (s)")
    ax.set_ylabel("polar handover success (%)")
    ax.set_ylim(85.5, 96)
    ax.set_title("H2: conservative calibration holds the ceiling under drift", fontsize=10)
    ax.legend(fontsize=7, frameon=False, loc="lower center", bbox_to_anchor=(0.5, -0.03), ncol=3)
    ax.grid(alpha=0.25, lw=0.5)
    fig.tight_layout()
    fig.savefig(OUT / "h2_drift_three_lines.png")
    print("wrote", OUT / "h2_drift_three_lines.png")


if __name__ == "__main__":
    fig_adv()
    fig_drift()
