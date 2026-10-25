"""Generate the manuscript figures from the campaign analysis.

Figures
-------
fig6_reliability   handover success by latitude bin (mean +- 1 sd over seeds) and
                   Arctic HSR bars with 95% confidence intervals
fig7_convergence   intent satisfaction during training (mean +- 1 sd)
fig8_search        architecture-search history and quality-at-budget
fig9_auditor       auditor stage detection rates by candidate class
fig10_latency      latency distributions of the discovered policy
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

PALETTE = {
    "almond": "#1f4e79",
    "almond_fixedarch": "#2e75b6",
    "no_forensics": "#8faadc",
    "no_memory": "#9dc3e6",
    "no_counterfactual": "#b4c7e7",
    "no_nas": "#c9d9ef",
    "oracle": "#c00000",
    "ppomlp": "#ed7d31",
    "static_llm": "#a5a5a5",
    "eureka": "#ffc000",
    "unseeded_evonas": "#70ad47",
}
DISPLAY = {
    "almond": "ALMOND",
    "almond_fixedarch": "ALMOND-FixedArch",
    "no_forensics": "ALMOND w/o forensics",
    "no_memory": "ALMOND w/o persistence",
    "no_counterfactual": "ALMOND w/o counterfactual",
    "no_nas": "ALMOND w/o LLM-NAS",
    "ppomlp": "PPO-MLP",
    "static_llm": "Static-LLM",
    "eureka": "Eureka-style",
    "oracle": "Oracle-PPO",
    "unseeded_evonas": "Unseeded-EvoNAS",
}
ORDER_MAIN = ["almond", "oracle", "almond_fixedarch", "eureka", "static_llm", "ppomlp"]
BINS = ["0-15", "15-30", "30-45", "45-55", "55-65", "65-70", "70-75", "75-90"]

plt.rcParams.update({
    "font.size": 9,
    "axes.grid": True,
    "grid.alpha": 0.3,
    "grid.linestyle": ":",
    "axes.spines.top": False,
    "axes.spines.right": False,
    "figure.dpi": 150,
    "savefig.bbox": "tight",
})


def fig_reliability(tables, out: Path):
    bins = tables["bins"]
    fig, axes = plt.subplots(1, 2, figsize=(9.0, 3.4), gridspec_kw={"width_ratios": [1.35, 1]})
    ax = axes[0]
    x = np.arange(len(BINS))
    for m in ORDER_MAIN:
        if m not in bins:
            continue
        mean = np.array([bins[m][b]["mean"] for b in BINS])
        std = np.array([bins[m][b]["std"] for b in BINS])
        ax.plot(x, mean, marker="o", ms=3.5, lw=1.6, label=DISPLAY.get(m, m), color=PALETTE.get(m))
        ax.fill_between(x, mean - std, mean + std, color=PALETTE.get(m), alpha=0.15, lw=0)
    ax.axvspan(5.5, 7.5, color="grey", alpha=0.10, lw=0)
    ax.text(6.5, 52, ">70° N", ha="center", fontsize=8, color="dimgrey")
    ax.set_xticks(x)
    ax.set_xticklabels(BINS, rotation=35, ha="right")
    ax.set_xlabel("latitude bin (deg)")
    ax.set_ylabel("handover success rate (%)")
    ax.set_ylim(30, 102)
    ax.legend(fontsize=7, ncol=2, frameon=False, loc="lower left")

    ax = axes[1]
    methods = [m for m in tables["methods"] if m in tables["region"]]
    methods = sorted(methods, key=lambda m: -tables["region"][m]["arctic"]["mean"])
    y = np.arange(len(methods))
    vals = [tables["region"][m]["arctic"]["mean"] for m in methods]
    lo = [tables["region"][m]["arctic"]["mean"] - tables["region"][m]["arctic"]["ci_low"] for m in methods]
    hi = [tables["region"][m]["arctic"]["ci_high"] - tables["region"][m]["arctic"]["mean"] for m in methods]
    ax.barh(y, vals, xerr=[lo, hi], color=[PALETTE.get(m, "#888") for m in methods],
            height=0.65, error_kw=dict(lw=1, capsize=2))
    ax.set_yticks(y)
    ax.set_yticklabels([DISPLAY.get(m, m) for m in methods], fontsize=7)
    ax.set_xlabel("Arctic HSR (%), mean with 95% CI")
    ax.set_xlim(0, 105)
    ax.axvline(95, color="k", ls="--", lw=0.8, alpha=0.6)
    fig.tight_layout()
    fig.savefig(out / "fig6_reliability.png")
    plt.close(fig)


def fig_convergence(raw, out: Path):
    fig, ax = plt.subplots(figsize=(4.6, 3.3))
    for m in ORDER_MAIN:
        if m not in raw:
            continue
        runs = [r for r in raw[m] if r.get("curve")]
        if not runs:
            continue
        xs = [c["episodes"] for c in runs[0]["curve"]]
        ys = []
        for r in runs:
            y = [c.get("S", np.nan) for c in r["curve"]]
            if len(y) == len(xs):
                ys.append(y)
        if not ys:
            continue
        Y = np.array(ys, dtype=float)
        mean = np.nanmean(Y, axis=0)
        std = np.nanstd(Y, axis=0)
        ax.plot(xs, mean, lw=1.7, marker="o", ms=2.5, color=PALETTE.get(m), label=DISPLAY.get(m, m))
        ax.fill_between(xs, mean - std, mean + std, color=PALETTE.get(m), alpha=0.13, lw=0)
    ax.axhline(75, color="k", ls="--", lw=0.8, alpha=0.6)
    ax.text(0.99, 76, "target S = 75", ha="right", fontsize=7, color="dimgrey", transform=ax.get_yaxis_transform())
    ax.set_xlabel("training episodes")
    ax.set_ylabel("intent satisfaction S")
    ax.legend(fontsize=7, frameon=False)
    fig.tight_layout()
    fig.savefig(out / "fig7_convergence.png")
    plt.close(fig)


def fig_search(nas: dict, out: Path):
    if not nas:
        return
    fig, axes = plt.subplots(1, 2, figsize=(8.4, 3.1))
    ax = axes[0]
    for key, label, colour in (("llm", "ALMOND-seeded evolution", PALETTE["almond"]),
                               ("random", "Unseeded-EvoNAS", PALETTE["unseeded_evonas"])):
        d = nas.get(key)
        if not d:
            continue
        hist = d.get("nas", {}).get("history", [])
        if not hist:
            continue
        evals = [h["evals"] for h in hist]
        best = [h["best_reward"] for h in hist]
        ax.step(evals, best, where="post", color=colour, lw=1.8, label=label)
    ax.set_xlabel("architectures evaluated")
    ax.set_ylabel("best-so-far task reward")
    ax.legend(fontsize=7, frameon=False)
    ax = axes[1]
    for key, label, colour in (("llm", "ALMOND-seeded", PALETTE["almond"]),
                               ("random", "Unseeded", PALETTE["unseeded_evonas"])):
        d = nas.get(key)
        if not d:
            continue
        front = d["nas"].get("front", [])
        if not front:
            continue
        ax.scatter([p["params"] for p in front], [p["reward"] for p in front],
                   s=28, color=colour, label=label, alpha=0.85)
    ax.set_xlabel("trainable parameters")
    ax.set_ylabel("task reward (Pareto front)")
    ax.legend(fontsize=7, frameon=False)
    fig.tight_layout()
    fig.savefig(out / "fig8_search.png")
    plt.close(fig)


def fig_auditor(stress: dict, out: Path):
    if not stress:
        return
    classes = list(stress["summary"].keys())
    fig, ax = plt.subplots(figsize=(4.8, 3.0))
    x = np.arange(len(classes))
    sem = [stress["summary"][c]["semantic_detect"] * 100 for c in classes]
    phy = [stress["summary"][c]["physics_detect"] * 100 for c in classes]
    ax.bar(x - 0.19, sem, width=0.36, label="semantic stage", color=PALETTE["almond_fixedarch"])
    ax.bar(x + 0.19, phy, width=0.36, label="physics stage", color=PALETTE["oracle"])
    ax.set_xticks(x)
    ax.set_xticklabels(classes, rotation=20, ha="right", fontsize=8)
    ax.set_ylabel("detection rate (%)")
    ax.set_ylim(0, 108)
    ax.legend(fontsize=7, frameon=False)
    fig.tight_layout()
    fig.savefig(out / "fig9_auditor.png")
    plt.close(fig)


def fig_latency(lat: dict, out: Path):
    if not lat or "variants" not in lat:
        return
    fig, ax = plt.subplots(figsize=(4.8, 3.0))
    names = [k for k, v in lat["variants"].items() if "mean_ms" in v]
    means = [lat["variants"][k]["mean_ms"] for k in names]
    p99 = [lat["variants"][k]["p99_ms"] for k in names]
    x = np.arange(len(names))
    ax.bar(x - 0.19, means, width=0.36, label="mean", color=PALETTE["almond"])
    ax.bar(x + 0.19, p99, width=0.36, label="p99", color=PALETTE["eureka"])
    ax.axhline(15.0, color="k", ls="--", lw=0.8, alpha=0.7)
    ax.text(0.01, 15.6, "15 ms envelope", fontsize=7, color="dimgrey")
    ax.set_xticks(x)
    ax.set_xticklabels([n.replace("_", "\n") for n in names], fontsize=7)
    ax.set_ylabel("single-batch latency (ms)")
    ax.legend(fontsize=7, frameon=False)
    fig.tight_layout()
    fig.savefig(out / "fig10_latency.png")
    plt.close(fig)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--analysis", default="results/analysis")
    ap.add_argument("--out", default="figures")
    args = ap.parse_args()
    a = Path(args.analysis)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    tables_p = a / "tables.json"
    raw_p = a / "raw.json"
    tables = json.loads(tables_p.read_text(encoding="utf-8")) if tables_p.exists() else None
    raw = json.loads(raw_p.read_text(encoding="utf-8")) if raw_p.exists() else None
    nas = {}
    for key, f in (("llm", "results/nas/llm_spec.json"), ("random", "results/nas/random_spec.json")):
        p = Path(f)
        if p.exists():
            nas[key] = json.loads(p.read_text(encoding="utf-8"))
    stress = None
    sp = Path("results/auditor_stress.json")
    if sp.exists():
        stress = json.loads(sp.read_text(encoding="utf-8"))
    lat = None
    lp = Path("results/latency_benchmark.json")
    if lp.exists():
        lat = json.loads(lp.read_text(encoding="utf-8"))

    if tables:
        fig_reliability(tables, out)
        print("wrote fig6_reliability.png")
    if raw:
        fig_convergence(raw, out)
        print("wrote fig7_convergence.png")
    if nas:
        fig_search(nas, out)
        print("wrote fig8_search.png")
    if stress:
        fig_auditor(stress, out)
        print("wrote fig9_auditor.png")
    if lat:
        fig_latency(lat, out)
        print("wrote fig10_latency.png")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
