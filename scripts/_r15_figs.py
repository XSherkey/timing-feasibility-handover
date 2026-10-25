"""R15: regenerate the four figures whose arrows, whiskers, legend and box text were out of bounds.

  * fig1_pipeline.png  - arrow endpoints now sit exactly on the padded box borders (pad = 0.05)
  * fig2_gap.png       - the PPO-MLP error bar no longer dips below the x axis
  * fig6_forms.png     - the legend moved outside the axes, above the plot
  * fig8_architecture.png - the monitoring label wraps to two lines inside its box
"""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT.parent / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本" / "figures"
plt.rcParams.update({"font.size": 8, "axes.linewidth": 0.7, "savefig.dpi": 300})
PAD = 0.05          # FancyBboxPatch pad used by the pipeline figure
APAD = 0.06         # pad used by the architecture figure


# ---------------------------------------------------------------- Fig. 1
def fig_pipeline() -> None:
    fig, ax = plt.subplots(figsize=(7.0, 2.7))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 4)
    ax.axis("off")
    boxes = [
        (0.2, 1.5, 1.9, 1.1, "censored\nfailure log", "#d6e6f5"),
        (2.4, 1.5, 1.9, 1.1, "Kaplan-Meier\n$F_z$ recovery", "#d6e6f5"),
        (4.6, 2.4, 1.9, 1.0, "LLM: predicate\n$P_z$ only", "#f6e2c8"),
        (4.6, 0.6, 1.9, 1.0, "probe on deployed\npolicy: $\\tau^*$", "#f6e2c8"),
        (6.9, 1.5, 1.7, 1.1, "margin\n$m=2$ s", "#e8d8ef"),
        (8.9, 1.5, 1.0, 1.1, "shield\n$\\Pi_\\tau$", "#d9edd8"),
    ]
    for x, y, w, h, txt, col in boxes:
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle=f"round,pad={PAD}",
                                    fc=col, ec="#333333", lw=0.8))
        ax.text(x + w / 2, y + h / 2, txt, ha="center", va="center", fontsize=7.2)

    # padded outer edges of the boxes
    r1, l2 = 0.2 + 1.9 + PAD, 2.4 - PAD                 # 2.15 -> 2.35
    r2 = 2.4 + 1.9 + PAD                                 # 4.35
    l3, l4 = 4.6 - PAD, 4.6 - PAD                        # 4.55 (LLM / probe)
    r3 = 4.6 + 1.9 + PAD                                 # 6.55
    l5 = 6.9 - PAD                                       # 6.85
    r5 = 6.9 + 1.7 + PAD                                 # 8.65
    l6 = 8.9 - PAD                                       # 8.85
    arrows = [
        ((r1, 2.05), (l2, 2.05)),
        ((r2, 2.15), (l3, 2.78)),
        ((r2, 1.95), (l4, 1.12)),
        ((r3, 2.92), (l5, 2.24)),
        ((r3, 1.08), (l5, 1.86)),
        ((r5, 2.05), (l6, 2.05)),
    ]
    for a, b in arrows:
        ax.add_patch(FancyArrowPatch(a, b, arrowstyle="->", lw=0.9, color="#333333",
                                     shrinkA=0, shrinkB=0))
    ax.text(5.55, 1.93, "predicate", fontsize=6.2, ha="center", color="#8a5a00")
    ax.text(5.55, 0.42, "magnitude", fontsize=6.2, ha="center", color="#8a5a00")
    ax.text(0.2, 3.55, "Every candidate passes the audit gate: semantic check, physics check, "
                       "counterfactual replay on held-out splits",
            fontsize=7.0, style="italic", color="#444444")
    ax.text(0.2, 0.2, "training weights are never touched: the shield acts at decision time only",
            fontsize=6.8, color="#555555")
    fig.tight_layout()
    fig.savefig(OUT / "fig1_pipeline.png")
    fig.savefig(OUT / "fig1_pipeline.pdf")
    plt.close(fig)
    print("fig1 written")


# ---------------------------------------------------------------- Fig. 2 (gap)
def fig_gap() -> None:
    import json

    d = json.loads((ROOT / "results" / "routeA_r3" / "headline_consistent" / "summary.json")
                   .read_text(encoding="utf-8"))
    A = d["arms"]
    m = lambda k: A[k]["summary"]["mean"]
    s = lambda k: A[k]["summary"]["sd"]
    bars = [
        ("PPO-MLP\nno knowledge", m("ppomlp_none"), s("ppomlp_none"), "#b0b0b0"),
        ("same knowledge\nas a reward\n($\\lambda$=8)", m("lam8"), s("lam8"), "#e0a060"),
        ("same knowledge\nas a shield\n(on PPO-MLP)", m("ppomlp_rule16"), s("ppomlp_rule16"), "#7fb3d5"),
        ("mined-rule\ncampaign arm\n(16 s, no margin)", m("almond_rule16"), s("almond_rule16"), "#4a7fb5"),
        ("tuned constant\n18 s, no learning", m("maxel18"), s("maxel18"), "#c0392b"),
    ]
    lo = min(b[1] - b[2] for b in bars)
    fig, ax = plt.subplots(figsize=(6.4, 3.2))
    xs = np.arange(len(bars))
    ax.bar(xs, [b[1] for b in bars], yerr=[b[2] for b in bars], capsize=3,
           color=[b[3] for b in bars], width=0.62,
           error_kw=dict(elinewidth=0.8, ecolor="#444444"))
    for x, (lab, v, sd, _c) in zip(xs, bars):
        ax.text(x, v + sd + 1.2, f"{v:.1f}", ha="center", fontsize=8)
    ax.set_xticks(xs)
    ax.set_xticklabels([b[0] for b in bars], fontsize=6.4)
    ax.set_ylim(np.floor(lo - 2), 102)          # keep the lowest whisker inside the axes
    ax.set_ylabel("polar handover success (%)")
    ax.grid(axis="y", ls=":", lw=0.5, alpha=0.6)
    ax.set_axisbelow(True)
    fig.tight_layout()
    fig.savefig(OUT / "fig2_gap.png")
    fig.savefig(OUT / "fig2_gap.pdf")
    plt.close(fig)
    print("fig2 written; ylim", ax.get_ylim())


# ---------------------------------------------------------------- Fig. 6 (forms)
def fig_forms() -> None:
    import json

    d = json.loads((ROOT / "results" / "routeA_r3" / "ladder_consistent" / "summary.json")
                   .read_text(encoding="utf-8"))
    ORDER = [("no_knowledge", "no knowledge"), ("reward_lam8", "reward λ = 8"),
             ("narrative_16s_rule", "narrative 16 s rule"), ("tuned_constant_18", "tuned 18 s constant"),
             ("deployed_probe_shield", "deployed shield"), ("oracle", "oracle")]
    nom = [d["regimes"]["nominal"][k]["summary"]["mean"] for k, _ in ORDER]
    p2 = [d["regimes"]["plus2s"][k]["summary"]["mean"] for k, _ in ORDER]
    nom_sd = [d["regimes"]["nominal"][k]["summary"]["sd"] for k, _ in ORDER]
    p2_sd = [d["regimes"]["plus2s"][k]["summary"]["sd"] for k, _ in ORDER]

    x = np.arange(len(ORDER))
    fig, ax = plt.subplots(figsize=(6.6, 3.0))
    ax.bar(x - 0.19, nom, width=0.36, yerr=nom_sd, capsize=2, color="#4a7fb5", label="nominal physics",
           error_kw=dict(elinewidth=0.7, ecolor="#333333"))
    ax.bar(x + 0.19, p2, width=0.36, yerr=p2_sd, capsize=2, color="#c0392b", label="+2 s acquisition drift",
           error_kw=dict(elinewidth=0.7, ecolor="#333333"))
    for xi, v in zip(x - 0.19, nom):
        ax.text(xi, v + 1.0, f"{v:.1f}", ha="center", fontsize=6.2)
    for xi, v in zip(x + 0.19, p2):
        ax.text(xi, v + 1.0, f"{v:.1f}", ha="center", fontsize=6.2)
    ax.set_xticks(x)
    ax.set_xticklabels([lbl for _, lbl in ORDER], fontsize=6.4, rotation=18, ha="right")
    lo6 = min(min(n - d for n, d in zip(nom, nom_sd)), min(q - d for q, d in zip(p2, p2_sd)))
    ax.set_ylim(int(np.floor(lo6 - 2)), 102)   # keep every whisker inside the axes
    ax.set_ylabel("polar handover success (%)")
    # legend outside the axes, above the plot, so it cannot cover any bar
    ax.legend(fontsize=6.6, frameon=False, ncol=2, loc="lower center",
              bbox_to_anchor=(0.5, 1.02), borderaxespad=0.0)
    ax.grid(axis="y", ls=":", lw=0.5, alpha=0.6)
    ax.set_axisbelow(True)
    fig.tight_layout()
    fig.savefig(OUT / "fig6_forms.png")
    fig.savefig(OUT / "fig6_forms.pdf")
    plt.close(fig)
    print("fig6 written")


# ---------------------------------------------------------------- Fig. 8 (architecture)
def fig_architecture() -> None:
    fig, ax = plt.subplots(figsize=(7.0, 3.4))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 5)
    ax.axis("off")

    def box(x, y, w, h, label, fc="#dce9f5", fs=6.6):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle=f"round,pad={APAD}",
                                    fc=fc, ec="#33506e", lw=0.8))
        ax.text(x + w / 2, y + h / 2, label, ha="center", va="center", fontsize=fs, wrap=True)

    def arrow(x1, y1, x2, y2, style="-|>", ls="-"):
        ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle=style, lw=0.8,
                                     color="#33506e", linestyle=ls, mutation_scale=8,
                                     shrinkA=0, shrinkB=0))

    box(0.15, 3.6, 1.55, 0.9, "operator intent")
    box(2.05, 3.6, 1.75, 0.9, "LLM predicate\nservice")
    box(4.15, 3.6, 1.55, 0.9, "training-log\nstore")
    box(6.05, 3.6, 1.55, 0.9, "KM diagnostic\n(not deployed)")
    box(0.15, 2.2, 1.55, 0.9, "failure log\ninjection")
    box(2.05, 2.2, 1.75, 0.9, "probe runner\n(validation only)")
    box(4.15, 2.2, 1.55, 0.9, "audit gate\n(validation replay)")
    box(6.05, 2.2, 1.75, 0.9, "versioned KG\n(commit / rollback)")
    box(8.15, 2.2, 1.7, 0.9, "runtime shield\n(decision time)")
    box(8.15, 0.9, 1.7, 0.9, "network controller\n(PPO policy, frozen)")
    box(0.15, 0.9, 3.65, 0.9,
        "monitoring: late_handover / no_route /\nwindow / drift trigger", fc="#f6e7d5", fs=6.2)

    r = APAD
    arrow(1.70 + r, 4.05, 2.05 - r, 4.05)
    arrow(3.80 + r, 4.05, 4.15 - r, 4.05)
    arrow(5.70 + r, 4.05, 6.05 - r, 4.05)
    arrow(2.92, 3.60, 2.92, 3.10)
    arrow(3.80 + r, 2.65, 4.15 - r, 2.65)
    arrow(5.70 + r, 2.65, 6.05 - r, 2.65)
    arrow(7.80 + r, 2.65, 8.15 - r, 2.65)
    arrow(9.0, 2.20, 9.0, 1.80)
    arrow(8.15 - r, 1.35, 3.80 + r, 1.35, style="-|>", ls="--")
    arrow(1.9, 1.80, 1.9, 2.20, style="-|>", ls="--")
    arrow(6.05, 3.60, 5.4, 3.10, style="-|>", ls=":")
    ax.text(5.0, 4.85, "discovery (training window only)", fontsize=6.4, ha="center", style="italic")
    ax.text(5.0, 1.95, "calibration and admission (validation window only)", fontsize=6.4,
            ha="center", style="italic")
    ax.text(9.0, 3.35, "deployment", fontsize=6.4, ha="center", style="italic")
    fig.tight_layout()
    fig.savefig(OUT / "fig8_architecture.png")
    fig.savefig(OUT / "fig8_architecture.pdf")
    plt.close(fig)
    print("fig8 written")


if __name__ == "__main__":
    fig_pipeline()
    fig_gap()
    fig_forms()
    fig_architecture()
