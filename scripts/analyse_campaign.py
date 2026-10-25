"""Assemble the manuscript's result tables from a campaign directory.

Produces ``results/analysis/*.json`` and a human-readable ``summary.md`` with:

* Table 8 / Fig. 6  reliability by latitude bin and region, mean +- std over seeds
* Table 8 / Fig. 7  convergence: episodes to 90% of asymptote and to S >= 75
* paired tests against ALMOND (Wilcoxon, t, Holm, effect sizes)
* Table 9 inputs: convergence ratios with bootstrap CIs
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from almond.analysis.stats import (
    bootstrap_ratio_ci,
    episodes_to_fraction,
    holm,
    paired_test,
    summarise,
)

DISPLAY = {
    "almond": "ALMOND",
    "almond_fixedarch": "ALMOND-FixedArch",
    "no_forensics": "ALMOND w/o forensics",
    "no_memory": "ALMOND w/o persistence",
    "no_counterfactual": "ALMOND w/o counterfactual",
    "no_nas": "ALMOND w/o LLM-NAS",
    "ppomlp": "PPO-MLP (hand-crafted)",
    "static_llm": "Static-LLM",
    "eureka": "Eureka-style",
    "oracle": "Oracle-PPO",
    "unseeded_evonas": "Unseeded-EvoNAS",
}

ORDER = [
    "almond",
    "almond_fixedarch",
    "oracle",
    "no_forensics",
    "no_memory",
    "no_counterfactual",
    "no_nas",
    "static_llm",
    "eureka",
    "ppomlp",
    "unseeded_evonas",
]

REGIONS = ("arctic", "subarctic", "midlat", "equatorial", "overall")
BINS = ("0-15", "15-30", "30-45", "45-55", "55-65", "65-70", "70-75", "75-90")


def load_runs(campaign: Path) -> dict[str, list[dict]]:
    out: dict[str, list[dict]] = defaultdict(list)
    for p in sorted(campaign.glob("*/run_summary.json")):
        try:
            r = json.loads(p.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        if not r.get("ok"):
            continue
        out[r["method"]].append(r)
    for k in out:
        out[k].sort(key=lambda r: r["seed"])
    return out


def curve_series(run: dict) -> tuple[list[float], list[float]]:
    xs = [c["episodes"] for c in run.get("curve", [])]
    ys = [c.get("S", float("nan")) for c in run.get("curve", [])]
    return xs, ys


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--campaign", default="results/campaign")
    ap.add_argument("--out", default="results/analysis")
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    runs = load_runs(Path(args.campaign))
    if not runs:
        print("no completed runs found")
        return 1
    methods = [m for m in ORDER if m in runs] + [m for m in runs if m not in ORDER]

    # ---------------- reliability by region ---------------- #
    table_region: dict[str, dict] = {}
    for m in methods:
        rs = runs[m]
        entry = {}
        for reg in REGIONS:
            vals = []
            for r in rs:
                v = r["final"].get(reg, {}).get("hsr")
                if v is not None and np.isfinite(v):
                    vals.append(v * 100)
            s = summarise(vals)
            entry[reg] = s.as_dict()
        entry["satisfaction"] = summarise([r["final"]["satisfaction"] for r in rs]).as_dict()
        entry["satisfaction_arctic"] = summarise(
            [r["final"].get("satisfaction_arctic", float("nan")) for r in rs]
        ).as_dict()
        params = [r.get("params", float("nan")) for r in rs]
        entry["params"] = summarise(params).as_dict()
        # PPO on this task has an absorbing passive-policy optimum, so the seed
        # distribution is bimodal.  Report the convergence rate and the median
        # explicitly rather than hiding it inside a mean.
        arc_vals = [r["final"]["arctic"]["hsr"] * 100 for r in rs]
        conv = [v for v in arc_vals if v >= 80.0]
        entry["converged_rate"] = len(conv) / max(len(arc_vals), 1)
        entry["arctic_converged_median"] = float(np.median(conv)) if conv else float("nan")
        entry["arctic_median"] = float(np.median(arc_vals)) if arc_vals else float("nan")
        if arc_vals:
            q75, q25 = np.percentile(arc_vals, [75, 25])
            entry["arctic_iqr"] = float(q75 - q25)
        else:
            entry["arctic_iqr"] = float("nan")
        entry["forensic_commits"] = float(np.mean([len(r.get("forensics", [])) for r in rs]))
        entry["kg_active"] = float(np.mean([r.get("kg", {}).get("n_active", 0) for r in rs]))
        table_region[m] = entry

    # ---------------- reliability by latitude bin ---------------- #
    table_bins: dict[str, dict] = {}
    for m in methods:
        entry = {}
        for b in BINS:
            vals = [r["final"]["bins"][b]["hsr"] * 100 for r in runs[m]
                    if b in r["final"].get("bins", {}) and r["final"]["bins"][b]["hsr"] is not None]
            entry[b] = summarise(vals).as_dict()
        table_bins[m] = entry

    # ---------------- convergence ---------------- #
    table_conv: dict[str, dict] = {}
    episodes_90: dict[str, list[float]] = {}
    episodes_s75: dict[str, list[float]] = {}
    for m in methods:
        e90, e75, peaks = [], [], []
        for r in runs[m]:
            xs, ys = curve_series(r)
            if len(xs) < 3:
                continue
            e90.append(episodes_to_fraction(xs, ys, frac=0.9))
            e75.append(episodes_to_fraction(xs, ys, absolute=75.0))
            peaks.append(float(np.nanmax(ys)))
        episodes_90[m] = e90
        episodes_s75[m] = e75
        table_conv[m] = dict(
            episodes_90=summarise(e90).as_dict(),
            episodes_s75=summarise(e75).as_dict(),
            peak_S=summarise(peaks).as_dict(),
        )

    # ---------------- paired tests vs ALMOND ---------------- #
    ref = "almond"
    tests_region: dict[str, list] = {}
    tests_conv: dict[str, list] = {}
    if ref in runs:
        ref_by_seed = {r["seed"]: r for r in runs[ref]}
        for reg in REGIONS:
            fam = []
            for m in methods:
                if m == ref:
                    continue
                common = sorted(set(ref_by_seed) & {r["seed"] for r in runs[m]})
                if not common:
                    continue
                a = [ref_by_seed[s]["final"][reg]["hsr"] * 100 for s in common]
                b = [{r["seed"]: r for r in runs[m]}[s]["final"][reg]["hsr"] * 100 for s in common]
                fam.append(paired_test(m, a, b))
            holm(fam)
            tests_region[reg] = [t.as_dict() for t in fam]
        fam = []
        for m in methods:
            if m == ref:
                continue
            common = sorted(set(ref_by_seed) & {r["seed"] for r in runs[m]})
            if len(common) < 2:
                continue
            ra = {s: episodes_90[ref][i] for i, s in enumerate(sorted(set(ref_by_seed))) if i < len(episodes_90[ref])}
            fam.append(None)
        # convergence ratio (ALMOND vs each baseline), bootstrap CI on the ratio
        ratios = {}
        for m in methods:
            if m == ref or not episodes_90.get(m):
                continue
            r, lo, hi = bootstrap_ratio_ci(episodes_90[ref], episodes_90[m])
            ratios[m] = dict(ratio=float(r), lo=float(lo), hi=float(hi))
        table_conv_ratios = ratios
    else:
        table_conv_ratios = {}

    payload = dict(
        methods=methods,
        n_seeds={m: len(runs[m]) for m in methods},
        region=table_region,
        bins=table_bins,
        convergence=table_conv,
        convergence_ratio=table_conv_ratios,
        paired_region=tests_region,
    )
    (out / "tables.json").write_text(json.dumps(payload, indent=2, default=float), encoding="utf-8")

    # per-method per-seed raw metrics for the figures
    raw = {
        m: [
            dict(
                seed=r["seed"],
                final=r["final"],
                curve=[dict(episodes=c["episodes"], S=c.get("S"), hsr_arctic=c.get("hsr_arctic")) for c in r.get("curve", [])],
                params=r.get("params"),
                wall_s=r.get("wall_s"),
            )
            for r in runs[m]
        ]
        for m in methods
    }
    (out / "raw.json").write_text(json.dumps(raw, indent=2, default=float), encoding="utf-8")

    # ---------------- human-readable summary ---------------- #
    lines = []
    lines.append("# Campaign summary\n")
    lines.append(f"methods: {len(methods)}  seeds: " + ", ".join(f"{m}={len(runs[m])}" for m in methods) + "\n")
    hdr = (
        f"{'method':<26}"
        + "".join(f"{r + ' HSR%':>14}" for r in REGIONS)
        + f"{'S':>10}{'params':>9}{'conv':>7}{'arc.med':>9}{'arc.IQR':>9}"
    )
    lines.append("## Reliability (mean +- std over seeds)\n")
    lines.append("```")
    lines.append(hdr)
    for m in methods:
        e = table_region[m]
        row = f"{DISPLAY.get(m, m):<26}"
        for reg in REGIONS:
            row += f"{e[reg]['mean']:8.1f}+-{e[reg]['std']:4.1f}"
        row += (
            f"{e['satisfaction']['mean']:10.1f}{e['params']['mean']:9.0f}"
            f"{e['converged_rate'] * 100:6.0f}%{e['arctic_median']:9.1f}{e['arctic_iqr']:9.1f}"
        )
        lines.append(row)
    lines.append("```\n")
    lines.append("## Convergence (episodes to 90% of asymptote / to S>=75)\n")
    lines.append("```")
    lines.append(f"{'method':<26}{'ep@90%':>12}{'ep@S75':>12}{'peak S':>10}")
    for m in methods:
        c = table_conv[m]
        lines.append(
            f"{DISPLAY.get(m, m):<26}{c['episodes_90']['mean']:8.0f}+-{c['episodes_90']['std']:3.0f}"
            f"{c['episodes_s75']['mean']:8.0f}+-{c['episodes_s75']['std']:3.0f}{c['peak_S']['mean']:10.1f}"
        )
    lines.append("```\n")
    if table_conv_ratios:
        lines.append("## Convergence-speed ratio vs ALMOND (baseline / ALMOND, >1 means ALMOND faster)\n")
        lines.append("```")
        for m, v in table_conv_ratios.items():
            lines.append(f"{DISPLAY.get(m, m):<26}{v['ratio']:6.2f}  95% CI [{v['lo']:.2f}, {v['hi']:.2f}]")
        lines.append("```\n")
    lines.append("## Paired tests vs ALMOND (arctic HSR)\n")
    lines.append("```")
    lines.append(f"{'baseline':<26}{'median diff':>12}{'p(Wilcoxon)':>13}{'p(Holm)':>10}{'d':>7}{'r_rb':>7}")
    for t in tests_region.get("arctic", []):
        lines.append(
            f"{DISPLAY.get(t['name'], t['name']):<26}{t['median_diff']:12.2f}{t['p_wilcoxon']:13.4f}"
            f"{t['p_holm']:10.4f}{t['cohen_d']:7.2f}{t['rank_biserial']:7.2f}"
        )
    lines.append("```")
    (out / "summary.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
