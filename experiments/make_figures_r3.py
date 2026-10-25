"""R3 figures: Fig. 8 (deployment architecture) and Fig. 9 (passive support / sample budget)."""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT.parent / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本" / "figures"
RES = ROOT / "results" / "routeA_r3"
plt.rcParams.update({"font.size": 8, "axes.linewidth": 0.7, "savefig.dpi": 300})


def fig_architecture() -> None:
    fig, ax = plt.subplots(figsize=(7.0, 3.4))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 5)
    ax.axis("off")

    def box(x, y, w, h, label, fc="#dce9f5"):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.06",
                                    fc=fc, ec="#33506e", lw=0.8))
        ax.text(x + w / 2, y + h / 2, label, ha="center", va="center", fontsize=6.6, wrap=True)

    def arrow(x1, y1, x2, y2, style="-|>", ls="-"):
        ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle=style, lw=0.8,
                                     color="#33506e", linestyle=ls, mutation_scale=8))

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
    box(0.15, 0.9, 3.65, 0.9, "monitoring: late_handover / no_route / window / drift trigger", fc="#f6e7d5")

    arrow(1.70, 4.05, 2.05, 4.05)
    arrow(3.80, 4.05, 4.15, 4.05)
    arrow(5.70, 4.05, 6.05, 4.05)
    arrow(2.92, 3.60, 2.92, 3.10)
    arrow(3.80, 2.65, 4.15, 2.65)
    arrow(5.70, 2.65, 6.05, 2.65)
    arrow(7.80, 2.65, 8.15, 2.65)
    arrow(9.0, 2.20, 9.0, 1.80)
    arrow(8.15, 1.35, 3.80, 1.35, style="-|>", ls="--")
    arrow(1.9, 1.80, 1.9, 2.20, style="-|>", ls="--")
    arrow(6.05, 3.60, 5.4, 3.10, style="-|>", ls=":")
    ax.text(5.0, 4.85, "discovery (training window only)", fontsize=6.4, ha="center", style="italic")
    ax.text(5.0, 1.95, "calibration and admission (validation window only)", fontsize=6.4,
            ha="center", style="italic")
    ax.text(9.0, 3.35, "deployment", fontsize=6.4, ha="center", style="italic")
    fig.tight_layout()
    fig.savefig(OUT / "fig8_architecture.png")
    fig.savefig(OUT / "fig8_architecture.pdf")
    print("fig8 written")


def fig_passive() -> None:
    d = json.loads((RES / "passive_ci" / "summary.json").read_text(encoding="utf-8"))
    xs = np.array([c["advance"] for c in d["curve"]])
    rate = np.array([c["late_rate"] for c in d["curve"]])
    n = np.array([c["n"] for c in d["curve"]])
    fit = np.array([c["fit"] for c in d["curve"]])
    se = 100 * np.sqrt(np.clip(rate * (1 - rate), 0, None) / np.maximum(n, 1))

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(7.0, 2.7))
    ax1.errorbar(xs, 100 * rate, yerr=1.96 * se, fmt="o", ms=3, color="#4a7fb5",
                 ecolor="#9cc3e0", elinewidth=0.8, capsize=2, label="passive log (binomial 95% CI)")
    ax1.plot(xs, 100 * fit, "-", color="#c0392b", lw=1.2, label="PAVA monotone fit")
    ax1.axhline(5, ls="--", lw=0.8, color="#555555")
    ax1.text(xs.min() + 0.2, 6.5, "ε = 5%", fontsize=6.5, color="#555555")
    ci = d["bootstrap"]["ci95"]
    ax1.axvspan(ci[0], ci[1], color="#c0392b", alpha=0.10, lw=0,
                label="crossing 95%% CI [%.0f, %.0f] s" % (ci[0], ci[1]))
    ax1.set_xlabel("handover advance a (s)")
    ax1.set_ylabel("late-handover rate (%)")
    ax1.set_xlim(xs.min() - 0.5, min(xs.max(), 26) + 0.5)
    ax1.legend(fontsize=5.8, frameon=False, loc="upper right")
    ax1.grid(ls=":", lw=0.4, alpha=0.6)
    ax1.set_title("(a) passive support", fontsize=7)

    b = [c for c in d["budget_curve"] if c.get("ci_width")]
    ns = [c["n"] for c in b]
    w = [c["ci_width"] for c in b]
    ax2.plot(ns, w, "o-", ms=3, lw=1.1, color="#4a7fb5")
    ax2.axhline(2.0, ls="--", lw=0.8, color="#555555")
    ax2.text(ns[0], 2.2, "one grid step (2 s)", fontsize=6.5, color="#555555")
    full = d["n_attempts"]
    ax2.axvline(full, ls=":", lw=0.9, color="#c0392b")
    ax2.text(full * 0.96, max(w) * 0.9, "full passive\nbudget (%d)" % full, fontsize=6,
             color="#c0392b", ha="right")
    ax2.set_xlabel("attempts in the passive log")
    ax2.set_ylabel("95% CI width of the crossing (s)")
    ax2.set_xscale("log")
    ax2.grid(ls=":", lw=0.4, alpha=0.6)
    ax2.set_title("(b) sample budget", fontsize=7)
    fig.tight_layout()
    fig.savefig(OUT / "fig9_passive_support.png")
    fig.savefig(OUT / "fig9_passive_support.pdf")
    print("fig9 written; CI width at full budget:", d["bootstrap"]["width_s"])


def main() -> int:
    fig_architecture()
    fig_passive()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
