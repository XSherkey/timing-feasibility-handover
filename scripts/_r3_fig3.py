"""Regenerate Fig. 3 from the sealed R2 artefacts so the chart, the caption and the
text agree on one protocol (common episodes, evaluation seed 0).

Series: no shield / tau=16 (mined tau*) / tau=18 (deployed tau_used) / tau=20 (ablation).
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
R2 = ROOT / "results" / "routeA_r2"
ARCH = ROOT / "results" / "verify_1023"
OUT = ROOT.parent / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本" / "figures"
plt.rcParams.update({"font.size": 8, "axes.linewidth": 0.7, "savefig.dpi": 300})


def series(path: Path, cond: str | None = None) -> list[float]:
    d = json.load(open(path, encoding="utf-8"))
    if isinstance(d, dict) and "per_seed" in d:
        return [d["per_seed"][str(s)]["arctic"] for s in range(10)]
    if isinstance(d, list) and cond:
        out = {}
        for r in d:
            if r["label"].startswith("almond_"):
                seed = int(r["label"].split("_s")[1].split("/")[0])
                if r["label"].endswith("/" + cond):
                    out[seed] = 100 * r["arctic"][0]
        return [out[s] for s in range(10)]
    raise SystemExit("unrecognised artefact " + str(path))


def per_seed_files(path: Path) -> list[float]:
    out = []
    for s in range(10):
        d = json.load(open(path.parent / ("%s_seed%d.json" % (path.stem, s)), encoding="utf-8"))
        rec = d[-1] if isinstance(d, list) else d
        out.append(100 * rec["arctic"][0])
    return out


def main() -> int:
    none = series(ARCH / "factorial.json", "none")
    t16 = per_seed_files(R2 / "factorial_tau16.json")
    t18 = per_seed_files(R2 / "factorial_tau18.json")
    t20 = per_seed_files(R2 / "factorial_tau20.json")

    fig, ax = plt.subplots(figsize=(6.6, 3.0))
    xs = np.arange(10)
    series_def = [
        ("no shield", none, "#b0b0b0", -0.30),
        ("$\\tau$ = 16 s (mined $\\tau^*$)", t16, "#9cc3e0", -0.10),
        ("$\\tau$ = 18 s (deployed, $\\tau_{used}$)", t18, "#4a7fb5", 0.10),
        ("$\\tau$ = 20 s (ablation)", t20, "#2e5f8a", 0.30),
    ]
    for lab, v, col, off in series_def:
        v = np.asarray(v, dtype=float)
        ax.bar(xs + off, v, width=0.19, color=col,
               label="%s  (%.2f $\\pm$ %.2f)" % (lab, v.mean(), v.std(ddof=1)))
    ax.set_xlabel("independent policy (seed)")
    ax.set_ylabel("polar handover success (%)")
    ax.set_ylim(40, 100)
    ax.set_xticks(xs)
    ax.set_xticklabels([str(i) for i in range(10)])
    ax.legend(fontsize=6.2, frameon=False, ncol=2, loc="lower center", bbox_to_anchor=(0.5, 1.0))
    ax.grid(axis="y", ls=":", lw=0.5, alpha=0.6)
    ax.set_axisbelow(True)
    fig.tight_layout()
    fig.savefig(OUT / "fig3_policy_independence.png")
    fig.savefig(OUT / "fig3_policy_independence.pdf")
    print("wrote fig3; means: %.2f / %.2f / %.2f / %.2f" %
          (np.mean(none), np.mean(t16), np.mean(t18), np.mean(t20)))
    print("spans:", (min(none), max(none)), (min(t16), max(t16)), (min(t18), max(t18)), (min(t20), max(t20)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
