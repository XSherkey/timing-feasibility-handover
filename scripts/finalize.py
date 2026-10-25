"""Torch-free finaliser: campaign statistics, tables, figures and TBD values.

Everything here reads only ``run_summary.json`` and the experiment JSONs, so it
does not import torch.  That matters on a machine where importing torch had
degraded to several minutes per process: the analysis and the figures must not
depend on the deep-learning stack at all.

Outputs
-------
results/analysis/tables.json      per-method region statistics, convergence, CI
results/analysis/summary.md       human-readable table
results/nas/backend_note.json     which model served the campaign
docs/tbd_values.json              values consumed by the manuscript filler
figures/fig6..fig10               the manuscript figures
"""
from __future__ import annotations

import argparse
import json
import math
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
BANDS = [("arctic", "arctic (>70°)"), ("subarctic", "subarctic (65-70°)"),
         ("midlat", "midlat (30-65°)"), ("equatorial", "equatorial (<30°)")]
METHODS = ["almond", "almond_fixedarch", "eureka", "unseeded_evonas",
           "ppomlp", "oracle", "static_llm", "no_forensics"]
DISPLAY = {
    "almond": "ALMOND", "almond_fixedarch": "ALMOND-FixedArch", "eureka": "Eureka-style",
    "unseeded_evonas": "Unseeded-EvoNAS", "ppomlp": "PPO-MLP", "oracle": "Oracle-PPO",
    "static_llm": "Static-LLM", "no_forensics": "ALMOND w/o forensics",
}
PALETTE = {
    "almond": "#1f4e79", "almond_fixedarch": "#2e75b6", "no_forensics": "#8faadc",
    "oracle": "#c00000", "ppomlp": "#ed7d31", "static_llm": "#a5a5a5",
    "eureka": "#ffc000", "unseeded_evonas": "#70ad47",
}


def t_ci(x: np.ndarray, z: float = 1.96) -> tuple[float, float]:
    if len(x) < 2:
        return float(x[0]), float(x[0])
    half = z * x.std(ddof=1) / math.sqrt(len(x))
    return float(x.mean() - half), float(x.mean() + half)


def load_runs(campaign: Path) -> dict[str, list[dict]]:
    out: dict[str, list[dict]] = defaultdict(list)
    for p in sorted(campaign.glob("*/run_summary.json")):
        try:
            with open(p, encoding="utf-8") as fh:
                r = json.load(fh)
        except (json.JSONDecodeError, OSError):
            continue
        if r.get("ok"):
            out[r["method"]].append(r)
    for v in out.values():
        v.sort(key=lambda r: r["seed"])
    return out


def ep90(runs: list[dict]) -> list[float]:
    """Episodes to 90 % of each run's own final satisfaction."""
    out = []
    for r in runs:
        curve = r.get("curve") or []
        if len(curve) < 2:
            out.append(float("nan"))
            continue
        ys = [c.get("S", float("nan")) for c in curve]
        xs = [c.get("episodes", 0) for c in curve]
        tail = np.nanmean(ys[-2:])
        target = 0.9 * tail
        hit = [x for x, y in zip(xs, ys) if np.isfinite(y) and y >= target]
        out.append(float(hit[0]) if hit else float(xs[-1]))
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--campaign", default="results/campaign")
    ap.add_argument("--out", default="results/analysis")
    ap.add_argument("--figures", default="figures")
    args = ap.parse_args()
    camp = ROOT / args.campaign
    runs = load_runs(camp)
    if not runs:
        print("no runs found")
        return 1
    out = ROOT / args.out
    out.mkdir(parents=True, exist_ok=True)
    figs = ROOT / args.figures
    figs.mkdir(parents=True, exist_ok=True)

    tables: dict = dict(methods=[m for m in METHODS if m in runs], region={}, conv={}, seeds={})
    for m, rs in runs.items():
        tables["seeds"][m] = len(rs)
        tables["region"][m] = {}
        for key, _label in BANDS + [("overall", "overall")]:
            vals = np.array([r["final"][key]["hsr"] * 100 for r in rs
                             if key in r.get("final", {}) and r["final"][key].get("hsr") is not None])
            if not len(vals):
                continue
            lo, hi = t_ci(vals)
            tables["region"][m][key] = dict(
                mean=float(vals.mean()), std=float(vals.std(ddof=1)) if len(vals) > 1 else 0.0,
                ci_low=lo, ci_high=hi, median=float(np.median(vals)),
                q25=float(np.percentile(vals, 25)), q75=float(np.percentile(vals, 75)),
                n=int(len(vals)),
            )
        arc = np.array([r["final"]["arctic"]["hsr"] * 100 for r in rs])
        sat = np.array([r["final"]["satisfaction"] for r in rs])
        e90 = np.array(ep90(rs), dtype=float)
        tables["conv"][m] = dict(
            converged=int((arc >= 80).sum()), n=int(len(arc)),
            rate=float((arc >= 80).mean()),
            ep90_median=float(np.nanmedian(e90)), ep90_std=float(np.nanstd(e90)),
            satisfaction=float(sat.mean()), satisfaction_std=float(sat.std(ddof=1)) if len(sat) > 1 else 0.0,
            params=int(rs[0].get("params", 0)),
        )
    (out / "tables.json").write_text(json.dumps(tables, indent=2), encoding="utf-8")

    # ---- summary.md ---------------------------------------------------- #
    lines = ["# Campaign summary", "",
             f"methods: {len(tables['methods'])}  seeds: "
             + ", ".join(f"{m}={tables['seeds'][m]}" for m in tables["methods"]), "",
             "```",
             f"{'method':<20}{'arctic':>10}{'subarct':>9}{'midlat':>9}{'equat':>8}{'overall':>9}"
             f"{'S':>7}{'conv':>7}{'median':>8}{'IQR':>7}{'ep90':>8}",
             ]
    for m in tables["methods"]:
        r = tables["region"][m]
        c = tables["conv"][m]
        iqr = r["arctic"]["q75"] - r["arctic"]["q25"]
        lines.append(
            f"{DISPLAY.get(m, m):<20}"
            f"{r['arctic']['mean']:9.1f}±{r['arctic']['std']:.1f}"
            f"{r['subarctic']['mean']:8.1f}±{r['subarctic']['std']:.1f}"
            f"{r['midlat']['mean']:8.1f}±{r['midlat']['std']:.1f}"
            f"{r['equatorial']['mean']:7.1f}±{r['equatorial']['std']:.1f}"
            f"{r['overall']['mean']:8.1f}±{r['overall']['std']:.1f}"
            f"{c['satisfaction']:7.1f}"
            f"{c['converged']:3d}/{c['n']:<3d}"
            f"{r['arctic']['median']:8.1f}{iqr:7.1f}{c['ep90_median']:8.0f}"
        )
    lines += ["```", "", "95% CI of Arctic HSR:", "```"]
    for m in tables["methods"]:
        a = tables["region"][m]["arctic"]
        ci = (a["ci_high"] - a["ci_low"]) / 2
        lines.append(f"{DISPLAY.get(m, m):<20} {a['mean']:6.1f} ± {ci:5.1f} "
                     f"[{a['ci_low']:6.1f}, {a['ci_high']:6.1f}]  n={a['n']}")
    lines.append("```")
    (out / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    # ---- figures -------------------------------------------------------- #
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plt.rcParams.update({"font.size": 9, "axes.grid": True, "grid.alpha": 0.3,
                         "grid.linestyle": ":", "axes.spines.top": False,
                         "axes.spines.right": False, "figure.dpi": 150,
                         "savefig.bbox": "tight"})

    # fig6: region profile + Arctic bars with CI
    order = [m for m in METHODS if m in tables["region"]]
    fig, axes = plt.subplots(1, 2, figsize=(9.2, 3.4), gridspec_kw={"width_ratios": [1.15, 1]})
    ax = axes[0]
    x = np.arange(len(BANDS))
    for m in order:
        mean = [tables["region"][m][k]["mean"] for k, _ in BANDS]
        std = [tables["region"][m][k]["std"] for k, _ in BANDS]
        ax.errorbar(x, mean, yerr=std, marker="o", ms=4, lw=1.6, capsize=2.5,
                    label=DISPLAY.get(m, m), color=PALETTE.get(m))
    ax.set_xticks(x)
    ax.set_xticklabels([lb for _, lb in BANDS], rotation=18, ha="right", fontsize=7.5)
    ax.set_ylabel("handover success rate (%)")
    ax.set_ylim(0, 104)
    ax.legend(fontsize=6.6, frameon=False, ncol=2, loc="lower left")
    ax = axes[1]
    srt = sorted(order, key=lambda m: tables["region"][m]["arctic"]["mean"])
    y = np.arange(len(srt))
    vals = [tables["region"][m]["arctic"]["mean"] for m in srt]
    lo = [tables["region"][m]["arctic"]["mean"] - tables["region"][m]["arctic"]["ci_low"] for m in srt]
    hi = [tables["region"][m]["arctic"]["ci_high"] - tables["region"][m]["arctic"]["mean"] for m in srt]
    ax.barh(y, vals, xerr=[lo, hi], color=[PALETTE.get(m, "#888") for m in srt],
            height=0.66, error_kw=dict(lw=1, capsize=2))
    ax.set_yticks(y)
    ax.set_yticklabels([f"{DISPLAY.get(m, m)} ({tables['conv'][m]['converged']}/{tables['conv'][m]['n']})"
                        for m in srt], fontsize=7)
    ax.set_xlabel("Arctic HSR (%), mean with 95% CI")
    ax.set_xlim(0, 108)
    ax.axvline(95, color="k", ls="--", lw=0.8, alpha=0.6)
    fig.tight_layout()
    fig.savefig(figs / "fig6_reliability.png")
    plt.close(fig)

    # fig7: convergence curves (mean ± sd across seeds)
    fig, ax = plt.subplots(figsize=(4.8, 3.3))
    for m in order:
        seqs = [(c["episodes"], c.get("S")) for r in runs[m] for c in (r.get("curve") or [])]
        if not seqs:
            continue
        xs = [s[0] for s in seqs if s[0] == seqs[0][0]]
        per = defaultdict(list)
        for r in runs[m]:
            for c in (r.get("curve") or []):
                per[c["episodes"]].append(c.get("S", float("nan")))
        if not per:
            continue
        ex = sorted(per)
        mean = np.array([np.nanmean(per[e]) for e in ex])
        sd = np.array([np.nanstd(per[e]) for e in ex])
        ax.plot(ex, mean, lw=1.7, marker="o", ms=2.5, color=PALETTE.get(m), label=DISPLAY.get(m, m))
        ax.fill_between(ex, mean - sd, mean + sd, color=PALETTE.get(m), alpha=0.12, lw=0)
    ax.axhline(75, color="k", ls="--", lw=0.8, alpha=0.6)
    ax.set_xlabel("training episodes")
    ax.set_ylabel("intent satisfaction S (validation)")
    ax.legend(fontsize=6.5, frameon=False, ncol=2)
    fig.tight_layout()
    fig.savefig(figs / "fig7_convergence.png")
    plt.close(fig)

    # fig8: search anytime + outcome + deployment (forensics ablation)
    sweep_l = ROOT / "results/nas/sweep_llm.json"
    sweep_r = ROOT / "results/nas/sweep_random.json"
    if sweep_l.exists() and sweep_r.exists():
        sw = {k: json.loads(p.read_text(encoding="utf-8"))
              for k, p in (("llm", sweep_l), ("random", sweep_r))}
        fig, axes = plt.subplots(1, 3, figsize=(10.4, 3.05),
                                 gridspec_kw={"width_ratios": [1.2, 0.8, 1.0]})
        ax = axes[0]
        for key, lab, col in (("llm", "ALMOND-seeded", PALETTE["almond"]),
                              ("random", "Unseeded", PALETTE["unseeded_evonas"])):
            seqs = []
            for r in sw[key].get("runs", []):
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
        ax.set_xlabel("architectures evaluated")
        ax.set_ylabel("best-so-far proxy reward")
        ax.legend(fontsize=7, frameon=False, loc="lower right")
        ax = axes[1]
        for i, (key, lab, col) in enumerate((("llm", "ALMOND-\nseeded", PALETTE["almond"]),
                                             ("random", "Unseeded", PALETTE["unseeded_evonas"]))):
            vals = [r["best_reward"] for r in sw[key].get("runs", []) if r.get("best_reward") is not None]
            if not vals:
                continue
            jit = np.linspace(-0.1, 0.1, len(vals)) if len(vals) > 1 else [0.0]
            ax.scatter(np.full(len(vals), i) + jit, vals, s=28, color=col, zorder=3)
            ax.hlines(np.median(vals), i - 0.27, i + 0.27, color="k", lw=1.4)
            ax.text(i, max(vals) + 0.04, f"med {np.median(vals):.2f}", ha="center", fontsize=6.8)
        ax.set_xticks([0, 1])
        ax.set_xticklabels(["ALMOND-\nseeded", "Unseeded"], fontsize=8)
        ax.set_xlim(-0.6, 1.6)
        ax.set_ylabel("best proxy reward per search")
        ax = axes[2]
        groups = [("almond", "with\nforensics", PALETTE["almond"]),
                  ("no_forensics", "without\nforensics", PALETTE["no_forensics"]),
                  ("ppomlp", "PPO-MLP", PALETTE["ppomlp"])]
        for i, (m, lab, col) in enumerate(groups):
            if m not in runs:
                continue
            vals = np.array([r["final"]["arctic"]["hsr"] * 100 for r in runs[m]])
            jit = np.linspace(-0.14, 0.14, len(vals)) if len(vals) > 1 else [0.0]
            ax.scatter(np.full(len(vals), i) + jit, vals, s=24, color=col, zorder=3)
            ax.hlines(np.median(vals), i - 0.3, i + 0.3, color="k", lw=1.5)
            ax.text(i, 103, f"{np.median(vals):.0f}%", ha="center", fontsize=7)
        ax.set_xticks(range(len(groups)))
        ax.set_xticklabels([g[1] for g in groups], fontsize=7.5)
        ax.set_xlim(-0.6, len(groups) - 0.4)
        ax.set_ylim(-4, 110)
        ax.set_ylabel("deployed Arctic HSR (%)")
        fig.tight_layout()
        fig.savefig(figs / "fig8_search.png")
        plt.close(fig)

    # fig9 / fig10 from the experiment JSONs
    stress_p = ROOT / "results/auditor_stress.json"
    if stress_p.exists():
        s = json.loads(stress_p.read_text(encoding="utf-8"))
        cls = [c for c in ("invalid", "inconsistent", "misleading", "adversarial", "control") if c in s["summary"]]
        labels = {"invalid": "physically\ninvalid", "inconsistent": "intent-\ninconsistent",
                  "misleading": "misleading\n(spurious)", "adversarial": "adversarial\n(latency)",
                  "control": "valid\ncontrol"}
        fig, ax = plt.subplots(figsize=(7.4, 3.0))
        y = np.arange(len(cls))
        phy = np.array([s["summary"][c]["physics_detect"] * s["summary"][c]["n"] for c in cls])
        sem = np.array([s["summary"][c]["semantic_detect"] * s["summary"][c]["n"] for c in cls])
        bad = np.array([0 if c == "control" else (s["summary"][c]["false_acceptance"] or 0) * s["summary"][c]["n"]
                        for c in cls])
        good = np.array([max(0.0, s["summary"][c]["n"] - phy[i] - sem[i] - bad[i]) if c == "control" else 0.0
                         for i, c in enumerate(cls)])
        ax.barh(y, phy, color="#c00000", label="rejected by the physics stage")
        ax.barh(y, sem, left=phy, color="#2e75b6", label="rejected by the semantic stage")
        ax.barh(y, bad, left=phy + sem, color="#ffc000", label="accepted — wrongly")
        ax.barh(y, good, left=phy + sem + bad, color="#70ad47", label="accepted — correctly")
        for i, c in enumerate(cls):
            n = int(s["summary"][c]["n"])
            ax.text(n + 0.5, i, f"{int(round(bad[i] + good[i]))}/{n} accepted", va="center",
                    fontsize=7, color="dimgrey")
        ax.set_yticks(y)
        ax.set_yticklabels([labels[c] for c in cls], fontsize=8)
        ax.invert_yaxis()
        ax.set_xlabel("injected candidate constraints (count)")
        ax.set_xlim(0, max(s["summary"][c]["n"] for c in cls) * 1.42)
        ax.legend(fontsize=6.8, frameon=False, loc="upper center", bbox_to_anchor=(0.5, -0.30), ncol=2)
        ov = s.get("overall", {})
        ax.set_title(f"auditor outcome per candidate class — false acceptance "
                     f"{ov.get('false_acceptance', 0) * 100:.1f}%, false rejection "
                     f"{ov.get('false_rejection', 0) * 100:.1f}%", fontsize=8, loc="left")
        fig.tight_layout()
        fig.savefig(figs / "fig9_auditor.png")
        plt.close(fig)

    lat_p = ROOT / "results/latency_benchmark.json"
    if lat_p.exists():
        lat = json.loads(lat_p.read_text(encoding="utf-8"))
        v = lat["variants"]
        names = [k for k in ("ort_cpu_fp32", "ort_cuda_fp32", "ort_cpu_fp16",
                             "ort_cpu_int8", "torch_cpu_fp32") if k in v]
        disp = {"ort_cpu_fp32": "ORT CPU\nFP32", "ort_cuda_fp32": "ORT CUDA\nFP32",
                "ort_cpu_fp16": "ORT CPU\nFP16", "ort_cpu_int8": "ORT CPU\nINT8",
                "torch_cpu_fp32": "PyTorch\nCPU"}
        means = [v[k]["mean_ms"] for k in names]
        p99 = [v[k]["p99_ms"] for k in names]
        fig, axes = plt.subplots(1, 2, figsize=(9.6, 2.9), gridspec_kw={"width_ratios": [1.0, 1.05]})
        ax = axes[0]
        x = np.arange(len(names))
        ax.bar(x - 0.19, means, width=0.36, label="mean", color="#1f4e79")
        ax.bar(x + 0.19, p99, width=0.36, label="p99", color="#ffc000")
        top = max(p99)
        for xi, (mm, pp) in enumerate(zip(means, p99)):
            ax.text(xi - 0.19, mm + top * 0.02, f"{mm:.3f}", ha="center", fontsize=5.8,
                    rotation=90, va="bottom")
            ax.text(xi + 0.19, pp + top * 0.02, f"{pp:.3f}", ha="center", fontsize=5.8,
                    rotation=90, va="bottom")
        ax.set_xticks(x)
        ax.set_xticklabels([disp.get(k, k) for k in names], fontsize=7)
        ax.set_ylabel("single-batch latency (ms)")
        ax.set_ylim(0, top * 1.6)
        ax.legend(fontsize=7, frameon=False, loc="upper left", ncol=2)
        ax.set_title(f"(a) measured, {lat.get('params', 0):,} parameters", fontsize=8.5, loc="left")
        ax = axes[1]
        head = [15.0 / m for m in means]
        ax.barh(range(len(names)), head, color=["#1f4e79" if h == max(head) else "#2e75b6" for h in head])
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
        ax.set_xlabel("headroom = 15 ms / measured mean (log)")
        ax.set_title("(b) margin to the on-board envelope", fontsize=8.5, loc="left")
        fig.tight_layout()
        fig.savefig(figs / "fig10_latency.png")
        plt.close(fig)

    print("\n".join(lines))
    print("\nfigures ->", figs)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
