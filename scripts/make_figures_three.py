"""Figures 8-10 for the revised manuscript.

fig8  architecture search, three views that can actually support/refute an
      efficiency claim: anytime best-so-far reward (mean with the seed band),
      evaluations needed to reach a fixed reward level (per-seed strip), and the
      aggregated Pareto front in the (parameters, reward) plane.
fig9  auditor outcome per candidate class as a 100% stacked bar, so no class is
      an empty column: which stage rejects, and where false acceptance happens.
fig10 inference latency on an axis scaled to the data, plus a logarithmic
      "headroom against the 15 ms on-board envelope" panel.
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

PAL = dict(almond="#1f4e79", alt="#2e75b6", uni="#70ad47",
           bad="#c00000", grey="#a5a5a5", amber="#ffc000", blue="#2e75b6")
CLASS_LABEL = {
    "invalid": "physically\ninvalid",
    "inconsistent": "intent-\ninconsistent",
    "misleading": "misleading\n(spurious)",
    "adversarial": "adversarial\n(latency)",
    "control": "valid\ncontrol",
}
plt.rcParams.update({
    "font.size": 9, "axes.grid": True, "grid.alpha": 0.3, "grid.linestyle": ":",
    "axes.spines.top": False, "axes.spines.right": False,
    "figure.dpi": 150, "savefig.bbox": "tight",
})


# --------------------------------------------------------------------------- #
def _anytime(ax, sweep: dict, key: str, label: str, colour: str, threshold: float | None):
    runs = sweep.get("runs", [])
    traces = [r["trace"] for r in runs if r.get("trace")]
    if not traces:
        return None
    n = min(len(t) for t in traces)
    ev = np.arange(1, n + 1)
    Y = np.array([[t[i][key] for i in range(n)] for t in traces], dtype=float)
    mean, lo, hi = Y.mean(0), Y.min(0), Y.max(0)
    ax.step(ev, mean, where="post", color=colour, lw=1.9, label=label)
    ax.fill_between(ev, lo, hi, step="post", color=colour, alpha=0.13, lw=0)
    if threshold is not None:
        firsts = []
        for row in Y:
            hit = np.flatnonzero(row >= threshold)
            firsts.append(int(hit[0]) + 1 if len(hit) else np.nan)
        return np.array(firsts, dtype=float)
    return None


def fig_search(llm: dict, rnd: dict, out: Path, campaign: Path | None = None):
    """Three panels: search anytime, search outcome per seed, deployment outcome.

    The third panel is the one that matters: it compares the same pipeline with the
    *searched* architecture and with a *fixed* GCN, one seed per point, because the
    architecture turns out to dominate the deployment metric far more than the
    search objective does.
    """
    fig, axes = plt.subplots(1, 3, figsize=(10.4, 3.05),
                             gridspec_kw={"width_ratios": [1.25, 0.85, 0.95]})
    ax = axes[0]
    for sweep, lab, col in ((llm, "ALMOND-seeded", PAL["almond"]), (rnd, "Unseeded", PAL["uni"])):
        # prefer the per-evaluation trace; fall back to the per-generation history
        seqs = []
        for r in sweep.get("runs", []):
            pts = r.get("trace") or r.get("history") or []
            pts = [p for p in pts if p.get("best_reward") is not None and p.get("evals")]
            if len(pts) >= 2:
                seqs.append(([p["evals"] for p in pts], [p["best_reward"] for p in pts]))
        if not seqs:
            continue
        n = min(len(s[0]) for s in seqs)
        ev = np.array(seqs[0][0][:n])
        Y = np.array([s[1][:n] for s in seqs], float)
        ax.step(ev, Y.mean(0), where="post", color=col, lw=1.9, label=lab)
        ax.fill_between(ev, Y.min(0), Y.max(0), step="post", color=col, alpha=0.13, lw=0)
    ax.axhline(0.0, color="k", lw=0.6, alpha=0.4)
    ax.set_xlabel("architectures evaluated")
    ax.set_ylabel("best-so-far proxy reward")
    ax.legend(fontsize=7, frameon=False, loc="lower right")

    ax = axes[1]
    for i, (sweep, lab, col) in enumerate(((llm, "ALMOND-\nseeded", PAL["almond"]),
                                           (rnd, "Unseeded", PAL["uni"]))):
        vals = [r["best_reward"] for r in sweep.get("runs", []) if r.get("best_reward") is not None]
        if not vals:
            continue
        jit = np.linspace(-0.10, 0.10, len(vals)) if len(vals) > 1 else [0.0]
        ax.scatter(np.full(len(vals), i) + jit, vals, s=28, color=col, zorder=3)
        ax.hlines(np.median(vals), i - 0.27, i + 0.27, color="k", lw=1.4)
        ax.text(i, max(vals) + 0.05, f"med {np.median(vals):.2f}", ha="center", fontsize=6.8)
    ax.set_xticks([0, 1])
    ax.set_xticklabels(["ALMOND-\nseeded", "Unseeded"], fontsize=8)
    ax.set_xlim(-0.6, 1.6)
    ax.set_ylabel("best proxy reward per search")

    ax = axes[2]
    if campaign is not None and campaign.exists():
        groups = [("almond", "searched\nMLP", PAL["almond"]),
                  ("almond_fixedarch", "fixed\nGCN", PAL["uni"])]
        for i, (method, lab, col) in enumerate(groups):
            vals = []
            for p in sorted(campaign.glob(f"{method}_seed*/run_summary.json")):
                d = json.loads(p.read_text(encoding="utf-8"))
                if d.get("ok"):
                    vals.append(d["final"]["arctic"]["hsr"] * 100)
            if not vals:
                continue
            jit = np.linspace(-0.14, 0.14, len(vals)) if len(vals) > 1 else [0.0]
            ax.scatter(np.full(len(vals), i) + jit, vals, s=26, color=col, zorder=3)
            ax.hlines(np.median(vals), i - 0.30, i + 0.30, color="k", lw=1.5)
            ax.text(i, 103, f"med {np.median(vals):.0f}%", ha="center", fontsize=6.8)
        ax.set_xticks([0, 1])
        ax.set_xticklabels([g[1] for g in groups], fontsize=8)
        ax.set_xlim(-0.6, 1.6)
        ax.set_ylim(-4, 110)
        ax.set_ylabel("deployed Arctic HSR (%)")
        ax.set_title("same pipeline, one seed per point", fontsize=7, loc="left")
    fig.tight_layout()
    fig.savefig(out / "fig8_search.png")
    plt.close(fig)


# --------------------------------------------------------------------------- #
def fig_auditor(stress: dict, out: Path):
    s = stress["summary"]
    classes = [c for c in ("invalid", "inconsistent", "misleading", "adversarial", "control") if c in s]
    fig, ax = plt.subplots(figsize=(7.4, 3.0))
    y = np.arange(len(classes))
    phy = np.array([s[c]["physics_detect"] * s[c]["n"] for c in classes], dtype=float)
    sem = np.array([s[c]["semantic_detect"] * s[c]["n"] for c in classes], dtype=float)
    bad = np.array([0 if c == "control" else (s[c]["false_acceptance"] or 0) * s[c]["n"]
                    for c in classes], dtype=float)
    good = np.array([max(0.0, s[c]["n"] - phy[i] - sem[i] - bad[i]) if c == "control" else 0.0
                     for i, c in enumerate(classes)], dtype=float)
    ax.barh(y, phy, color=PAL["bad"], label="rejected by the physics stage")
    ax.barh(y, sem, left=phy, color=PAL["blue"], label="rejected by the semantic stage")
    ax.barh(y, bad, left=phy + sem, color=PAL["amber"], label="accepted — wrongly")
    ax.barh(y, good, left=phy + sem + bad, color=PAL["uni"], label="accepted — correctly")
    for i, c in enumerate(classes):
        n = int(s[c]["n"])
        acc = int(round(bad[i] + good[i]))
        note = f"{acc}/{n} accepted" + ("" if c != "control" else " (correct)")
        ax.text(n + 0.5, i, note, va="center", fontsize=7, color="dimgrey")
    ax.set_yticks(y)
    ax.set_yticklabels([CLASS_LABEL.get(c, c) for c in classes], fontsize=8)
    ax.invert_yaxis()
    ax.set_xlabel("injected candidate constraints (count)")
    ax.set_xlim(0, max(s[c]["n"] for c in classes) * 1.42)
    ax.legend(fontsize=6.8, frameon=False, loc="upper center",
              bbox_to_anchor=(0.5, -0.30), ncol=2)
    overall = stress.get("overall", {})
    ax.set_title(
        f"auditor outcome per candidate class — overall false acceptance "
        f"{overall.get('false_acceptance', 0) * 100:.1f}%, false rejection "
        f"{overall.get('false_rejection', 0) * 100:.1f}%",
        fontsize=8, loc="left",
    )
    fig.tight_layout()
    fig.savefig(out / "fig9_auditor.png")
    plt.close(fig)


# --------------------------------------------------------------------------- #
def fig_latency(lat: dict, out: Path, envelope_ms: float = 15.0):
    v = lat["variants"]
    names = [k for k in ("ort_cpu_fp32", "ort_cuda_fp32", "ort_cpu_fp16", "ort_cpu_int8",
                         "torch_cpu_fp32") if k in v]
    disp = {"ort_cpu_fp32": "ORT CPU\nFP32", "ort_cuda_fp32": "ORT CUDA\nFP32",
            "ort_cpu_fp16": "ORT CPU\nFP16", "ort_cpu_int8": "ORT CPU\nINT8",
            "torch_cpu_fp32": "PyTorch\nCPU"}
    means = [v[k]["mean_ms"] for k in names]
    p99 = [v[k]["p99_ms"] for k in names]
    fig, axes = plt.subplots(1, 2, figsize=(9.6, 2.9), gridspec_kw={"width_ratios": [1.0, 1.05]})
    ax = axes[0]
    x = np.arange(len(names))
    ax.bar(x - 0.19, means, width=0.36, label="mean", color=PAL["almond"])
    ax.bar(x + 0.19, p99, width=0.36, label="p99", color=PAL["amber"])
    top = max(p99)
    for xi, (m, p) in enumerate(zip(means, p99)):
        ax.text(xi - 0.19, m + top * 0.02, f"{m:.3f}", ha="center", fontsize=5.8,
                rotation=90, va="bottom")
        ax.text(xi + 0.19, p + top * 0.02, f"{p:.3f}", ha="center", fontsize=5.8,
                rotation=90, va="bottom")
    ax.set_xticks(x)
    ax.set_xticklabels([disp.get(k, k) for k in names], fontsize=7)
    ax.set_ylabel("single-batch latency (ms)")
    ax.set_ylim(0, top * 1.60)
    ax.legend(fontsize=7, frameon=False, loc="upper left", ncol=2)
    ax.set_title(f"(a) measured, {lat.get('params', 0):,} parameters", fontsize=8.5, loc="left")

    ax = axes[1]
    head = [envelope_ms / m for m in means]
    ax.barh(range(len(names)), head, color=[PAL["almond"] if h == max(head) else PAL["alt"] for h in head])
    ax.set_xscale("log")
    ax.set_xlim(0.8, max(head) * 3.2)
    ax.axvline(1.0, color="k", ls="--", lw=0.9)
    ax.text(1.06, -0.62, "1× = envelope", fontsize=6.4, color="dimgrey")
    for i, h in enumerate(head):
        ax.text(h * 1.10, i, f"×{h:.0f}", va="center", fontsize=7)
    ax.set_yticks(range(len(names)))
    ax.set_yticklabels([disp.get(k, k).replace("\n", " ") for k in names], fontsize=7)
    ax.invert_yaxis()
    ax.set_ylim(len(names) - 0.35, -0.75)
    ax.set_xlabel(f"headroom = {envelope_ms:g} ms / measured mean (log)")
    ax.set_title("(b) margin to the on-board envelope", fontsize=8.5, loc="left")
    fig.tight_layout()
    fig.savefig(out / "fig10_latency.png")
    plt.close(fig)


# --------------------------------------------------------------------------- #
def main() -> int:
    out = Path("figures")
    out.mkdir(parents=True, exist_ok=True)
    nas_dir = Path("results/nas")
    llm_p, rnd_p = nas_dir / "sweep_llm.json", nas_dir / "sweep_random.json"
    if llm_p.exists() and rnd_p.exists():
        llm = json.loads(llm_p.read_text(encoding="utf-8"))
        rnd = json.loads(rnd_p.read_text(encoding="utf-8"))
        fig_search(llm, rnd, out, campaign=Path("results/campaign"))
        print("wrote fig8_search.png")
    else:
        print("fig8 skipped: run scripts/run_nas_sweep.py first")
    sp = Path("results/auditor_stress.json")
    if sp.exists():
        fig_auditor(json.loads(sp.read_text(encoding="utf-8")), out)
        print("wrote fig9_auditor.png")
    lp = Path("results/latency_benchmark.json")
    if lp.exists():
        fig_latency(json.loads(lp.read_text(encoding="utf-8")), out)
        print("wrote fig10_latency.png")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
