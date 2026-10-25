"""Redraw Fig. 9 panel (b) with both the i.i.d. and the cluster bootstrap."""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT.parent / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本" / "figures"
RES = ROOT / "results" / "routeA_r3"
plt.rcParams.update({"font.size": 8, "axes.linewidth": 0.7, "savefig.dpi": 300})


def main() -> int:
    d = json.loads((RES / "passive_ci" / "summary.json").read_text(encoding="utf-8"))
    bc = json.loads((RES / "passive_ci" / "budget_curves.json").read_text(encoding="utf-8"))
    xs = np.array([c["advance"] for c in d["curve"]])
    rate = np.array([c["late_rate"] for c in d["curve"]])
    n = np.array([c["n"] for c in d["curve"]])
    fit = np.array([c["fit"] for c in d["curve"]])
    se = 100 * np.sqrt(np.clip(rate * (1 - rate), 0, None) / np.maximum(n, 1))

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(7.0, 2.8))
    ax1.errorbar(xs, 100 * rate, yerr=1.96 * se, fmt="o", ms=3, color="#4a7fb5",
                 ecolor="#9cc3e0", elinewidth=0.8, capsize=2, label="passive log (binomial 95% CI)")
    ax1.plot(xs, 100 * fit, "-", color="#c0392b", lw=1.2, label="PAVA monotone fit")
    ax1.axhline(5, ls="--", lw=0.8, color="#555555")
    ax1.text(xs.min() + 0.2, 6.4, "eps = 5%", fontsize=6.5, color="#555555")
    ci = d["bootstrap"]["ci95"]
    ax1.axvspan(ci[0], ci[1], color="#c0392b", alpha=0.10, lw=0,
                label="cluster-bootstrap crossing CI [%.0f, %.0f] s" % (ci[0], ci[1]))
    ax1.set_xlabel("handover advance a (s)")
    ax1.set_ylabel("late-handover rate (%)")
    ax1.set_xlim(xs.min() - 0.5, min(xs.max(), 26) + 0.5)
    ax1.legend(fontsize=5.6, frameon=False, loc="upper right")
    ax1.grid(ls=":", lw=0.4, alpha=0.6)
    ax1.set_title("(a) passive support", fontsize=7)

    n_iid = [c["n"] for c in bc["iid"]]
    w_iid = [c["width"] for c in bc["iid"]]
    n_cl = [c["n"] for c in bc["cluster"]]
    w_cl = [c["width"] for c in bc["cluster"]]
    ax2.plot(n_iid, w_iid, "o-", ms=3, lw=1.1, color="#7fb3d5",
             label="i.i.d. resampling of attempts")
    ax2.plot(n_cl, w_cl, "s-", ms=3, lw=1.2, color="#c0392b",
             label="cluster bootstrap over (seed, site)")
    ax2.axhline(2.0, ls="--", lw=0.8, color="#555555")
    ax2.text(n_cl[0] * 1.05, 2.15, "one grid step (2 s)", fontsize=6.4, color="#555555")
    ax2.set_xlabel("attempts drawn from the passive log")
    ax2.set_ylabel("95% CI width of the crossing (s)")
    ax2.set_xscale("log")
    ax2.set_ylim(0, max(max(w_cl), 9) * 1.12)
    ax2.legend(fontsize=5.8, frameon=False, loc="upper right")
    ax2.grid(ls=":", lw=0.4, alpha=0.6)
    ax2.set_title("(b) sample budget", fontsize=7)
    fig.tight_layout()
    fig.savefig(OUT / "fig9_passive_support.png")
    fig.savefig(OUT / "fig9_passive_support.pdf")
    print("fig9 redrawn")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
