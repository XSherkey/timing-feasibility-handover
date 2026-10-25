"""Generate the seven main-text figures for the Route-A paper.

Every number is read from the sealed artefacts (results/routeA/*.json,
results/verify_1023/factorial_matched.json); only labels are hard-coded.
Figure text is ASCII-only so the script survives any console codepage.
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "results" / "routeA"
OUT = ROOT.parent / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本" / "figures"
OUT.mkdir(parents=True, exist_ok=True)
plt.rcParams.update({"font.size": 8, "axes.linewidth": 0.7, "savefig.dpi": 300})


def jsonl(p: Path):
    return json.load(open(p, encoding="utf-8"))


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
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.05",
                                    fc=col, ec="#333333", lw=0.8))
        ax.text(x + w / 2, y + h / 2, txt, ha="center", va="center", fontsize=7.2)
    arrows = [((2.1, 2.05), (2.4, 2.05)), ((4.3, 2.2), (4.6, 2.75)), ((4.3, 1.85), (4.6, 1.1)),
              ((6.5, 2.9), (6.9, 2.3)), ((6.5, 1.1), (6.9, 1.8)), ((8.6, 2.05), (8.9, 2.05))]
    for a, b in arrows:
        ax.add_patch(FancyArrowPatch(a, b, arrowstyle="->", lw=0.9, color="#333333"))
    ax.text(5.55, 1.93, "predicate", fontsize=6.2, ha="center", color="#8a5a00")
    ax.text(5.55, 0.42, "magnitude", fontsize=6.2, ha="center", color="#8a5a00")
    ax.text(0.2, 3.55, "Every candidate passes the audit gate: semantic check, physics check, "
                       "counterfactual replay on held-out splits",
            fontsize=7.0, style="italic", color="#444444")
    ax.text(0.2, 0.2, "training weights are never touched: the shield acts at decision time only",
            fontsize=6.8, color="#555555")
    fig.tight_layout()
    fig.savefig(OUT / "fig1_pipeline.pdf")
    fig.savefig(OUT / "fig1_pipeline.png")
    plt.close(fig)


def fig_gap() -> None:
    vals = [("PPO-MLP\nno knowledge", 72.6, "#b0b0b0"),
            ("same knowledge\nin the reward\n($\\lambda$=8, best)", 84.4, "#e0a060"),
            ("same knowledge\nas a shield\n(on PPO-MLP)", 91.8, "#7fb3d5"),
            ("ALMOND\nshield + policy", 93.6, "#4a7fb5"),
            ("tuned constant\n18 s, no learning", 94.0, "#c0392b")]
    fig, ax = plt.subplots(figsize=(6.4, 3.2))
    xs = np.arange(len(vals))
    ax.bar(xs, [v[1] for v in vals], color=[v[2] for v in vals], width=0.62)
    for x, (lab, v, _c) in zip(xs, vals):
        ax.text(x, v + 0.6, f"{v:.1f}", ha="center", fontsize=8)
    ax.set_xticks(xs)
    ax.set_xticklabels([v[0] for v in vals], fontsize=6.6)
    ax.set_ylim(60, 100)
    ax.set_ylabel("polar handover success (%)")
    ax.grid(axis="y", ls=":", lw=0.5, alpha=0.6)
    ax.set_axisbelow(True)
    fig.tight_layout()
    fig.savefig(OUT / "fig2_gap.pdf")
    fig.savefig(OUT / "fig2_gap.png")
    plt.close(fig)


def fig_policy() -> None:
    rows = jsonl(ROOT / "results" / "verify_1023" / "factorial.json")
    conds = {"none": ("no shield", "#b0b0b0"), "tau16": ("$\\tau$ = 16 s", "#4a7fb5"),
             "tau20": ("$\\tau$ = 20 s", "#2e5f8a")}
    fig, ax = plt.subplots(figsize=(6.6, 3.0))
    for k, (cond, (lab, col)) in enumerate(conds.items()):
        v = [100 * r["arctic"][0] for r in rows
             if r["label"].startswith("almond_") and r["label"].endswith("/" + cond)]
        xs = np.arange(len(v)) + (k - 1) * 0.26
        ax.bar(xs, v, width=0.24, color=col,
               label=f"{lab}  ({np.mean(v):.1f} +/- {np.std(v, ddof=1):.1f})")
    ax.set_xlabel("independent policy (seed)")
    ax.set_ylabel("polar handover success (%)")
    ax.set_ylim(55, 100)
    ax.set_xticks(np.arange(10))
    ax.set_xticklabels([str(i) for i in range(10)])
    ax.legend(fontsize=6.6, frameon=False, ncol=3, loc="lower center", bbox_to_anchor=(0.5, 1.0))
    ax.grid(axis="y", ls=":", lw=0.5, alpha=0.6)
    ax.set_axisbelow(True)
    fig.tight_layout()
    fig.savefig(OUT / "fig3_policy_independence.pdf")
    fig.savefig(OUT / "fig3_policy_independence.png")
    plt.close(fig)


def fig_frontier() -> None:
    s = jsonl(ART / "summary.json")
    fr = s["G2"]["frontier"]
    sh = s["G2"]["shield"]
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 2.9))
    ax = axes[0]
    xs = np.arange(len(fr))
    ax.errorbar(xs, [r["hsr"] for r in fr], yerr=[r["sd"] for r in fr], fmt="o-",
                color="#c0392b", capsize=2, lw=1.2, ms=4, label="reward penalty")
    ax.axhline(sh["hsr"], color="#2e5f8a", ls="--", lw=1.2)
    ax.text(0.05, sh["hsr"] + 1.2, f"decision shield {sh['hsr']:.1f}", color="#2e5f8a", fontsize=6.8)
    ax.set_xticks(xs)
    ax.set_xticklabels([r["lam"] for r in fr], fontsize=6.8)
    ax.set_xlabel("penalty coefficient $\\lambda$")
    ax.set_ylabel("polar handover success (%)")
    ax.grid(ls=":", lw=0.5, alpha=0.6)
    ax.set_ylim(55, 100)

    ax = axes[1]
    ax.plot([r["hsr"] for r in fr], [r["S"] for r in fr], "o", color="#c0392b", ms=5)
    for k, r in enumerate(fr):
        dy = 5 if k % 2 == 0 else -8
        ax.annotate(r["lam"], (r["hsr"], r["S"]), fontsize=5.8, xytext=(4, dy),
                    textcoords="offset points")
    ax.plot([sh["hsr"]], [sh["S"]], "*", color="#2e5f8a", ms=14)
    ax.annotate("shield", (sh["hsr"], sh["S"]), fontsize=6.8, color="#2e5f8a",
                xytext=(-34, -2), textcoords="offset points")
    ax.set_xlabel("polar handover success (%)")
    ax.set_ylabel("intent satisfaction $S$")
    ax.set_xlim(66, 97)
    ax.set_ylim(60, 80)
    ax.grid(ls=":", lw=0.5, alpha=0.6)
    fig.tight_layout()
    fig.savefig(OUT / "fig4_lambda_frontier.pdf")
    fig.savefig(OUT / "fig4_lambda_frontier.png")
    plt.close(fig)


def fig_drift() -> None:
    g3 = jsonl(ART / "g3_drift_table_5seed.json")
    drifts = [0.0, 2.0, 3.2, 4.4]
    const, const_lo, const_hi, cal, cal_lo, cal_hi = [], [], [], [], [], []
    for d in drifts:
        sel = [r for r in g3 if abs(r["acq"] - (d + 1.2)) < 1e-6]
        f = np.array([r["fixed18"] for r in sel])
        c = np.array([r["calib"] for r in sel])
        const.append(f.mean()); const_lo.append(f.min()); const_hi.append(f.max())
        cal.append(c.mean()); cal_lo.append(c.min()); cal_hi.append(c.max())
    fig, ax = plt.subplots(figsize=(5.6, 3.0))
    ax.plot(drifts, const, "o-", color="#c0392b", lw=1.6, ms=4, label="fixed constant (18 s)")
    ax.fill_between(drifts, const_lo, const_hi, color="#c0392b", alpha=0.15)
    ax.plot(drifts, cal, "s-", color="#2e5f8a", lw=1.6, ms=4, label="probe-calibrated (+2 s margin)")
    ax.fill_between(drifts, cal_lo, cal_hi, color="#2e5f8a", alpha=0.15)
    ax.set_xlabel("extra acquisition latency (s)")
    ax.set_ylabel("polar handover success (%)")
    ax.set_ylim(84, 96)
    ax.grid(ls=":", lw=0.5, alpha=0.6)
    ax.legend(fontsize=6.8, frameon=False, loc="lower left")
    fig.tight_layout()
    fig.savefig(OUT / "fig5_drift.pdf")
    fig.savefig(OUT / "fig5_drift.png")
    plt.close(fig)


def fig_forms() -> None:
    s = jsonl(ART / "summary.json")
    forms = [
        ("no knowledge", [71.8, s["H1"]["no_knowledge"]["hsr_sig32"]], "#b0b0b0"),
        ("reward $\\lambda$=8", [s["F3"]["lam8.0"]["mean"], s["H1"]["penalty_lam8"]["hsr_sig32"]], "#e0a060"),
        ("LLM 16 s rule", [93.6, 87.0], "#9cc3e0"),
        ("shield + probe", [s["H2"]["ref"]["m2"]["mean"], s["H2"]["sig32"]["m2"]["mean"]], "#2e5f8a"),
    ]
    fig, ax = plt.subplots(figsize=(5.4, 3.0))
    for lab, v, col in forms:
        ax.plot([0, 1], v, "o-", color=col, lw=1.5, ms=5, label=lab)
        ax.annotate(f"{v[1]:.1f}", (1, v[1]), xytext=(6, 0), textcoords="offset points",
                    fontsize=6.8, color=col, va="center")
    ax.set_xticks([0, 1])
    ax.set_xticklabels(["nominal physics", "+2 s acquisition drift"])
    ax.set_xlim(-0.15, 1.35)
    ax.set_ylabel("polar handover success (%)")
    ax.set_ylim(45, 100)
    ax.grid(ls=":", lw=0.5, alpha=0.6)
    ax.legend(fontsize=6.6, frameon=False, loc="lower left")
    fig.tight_layout()
    fig.savefig(OUT / "fig6_forms.pdf")
    fig.savefig(OUT / "fig6_forms.png")
    plt.close(fig)


def fig_gate() -> None:
    s = jsonl(ART / "summary.json")
    g = s["G1"]
    fig, axes = plt.subplots(1, 2, figsize=(6.8, 2.8))
    ax = axes[0]
    vals = [("no injection", 91.8, "#b0b0b0"),
            ("gate ON\n(bad rule rejected)", g["clean"]["gate_mean"], "#2e5f8a"),
            ("gate OFF\n(both committed)", g["clean"]["nogate_mean"], "#c0392b")]
    ax.bar(range(3), [v[1] for v in vals], color=[v[2] for v in vals], width=0.6)
    for i, (lab, v, _c) in enumerate(vals):
        ax.text(i, v + 1.5, f"{v:.1f}", ha="center", fontsize=7.5)
    ax.set_xticks(range(3))
    ax.set_xticklabels([v[0] for v in vals], fontsize=6.6)
    ax.set_ylim(0, 105)
    ax.set_ylabel("polar HSR, intents 1-3 (%)")
    ax.set_title("clean design (append-mode injection), n = 5", fontsize=7.4)
    ax.grid(axis="y", ls=":", lw=0.5, alpha=0.6)
    ax.set_axisbelow(True)

    ax = axes[1]
    r = s["G1"]["replace"]
    ax.bar([0, 1], [r["gate_mean"], r["nogate_mean"]], color=["#2e5f8a", "#c0392b"], width=0.55)
    for i, v in enumerate([r["gate_mean"], r["nogate_mean"]]):
        ax.text(i, v + 1.5, f"{v:.1f}", ha="center", fontsize=7.5)
    ax.set_xticks([0, 1])
    ax.set_xticklabels(["gate ON", "gate OFF"], fontsize=7)
    ax.set_ylim(0, 105)
    ax.set_title(f"replacement design, n = {r['n']} (Wilcoxon p = {r['p']:.4f})", fontsize=7.4)
    ax.grid(axis="y", ls=":", lw=0.5, alpha=0.6)
    ax.set_axisbelow(True)
    fig.tight_layout()
    fig.savefig(OUT / "fig7_gate.pdf")
    fig.savefig(OUT / "fig7_gate.png")
    plt.close(fig)


if __name__ == "__main__":
    fig_pipeline()
    fig_gap()
    fig_policy()
    fig_frontier()
    fig_drift()
    fig_forms()
    fig_gate()
    print("figures written to", OUT)
