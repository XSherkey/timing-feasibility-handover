"""Mechanism analysis: is the polar failure a *timing-feasibility* problem?

Hypothesis (TFA): an attempt with preparation advance ``a`` succeeds iff
``a >= T_setup(z)`` for the regime ``z = (latitude, elevation, plane change)``,
where ``T_setup`` is a random variable of the link/protocol, independent of the
policy.  If true, then

  * the polar failure zone is explained by the *shift* of the T_setup
    distribution (not by the policy's inability to learn),
  * the required advance is the upper quantile of T_setup in that regime,
  * an arm's reliability is predicted by the fraction of its attempts whose
    advance dominates that quantile.

This script measures all three from the per-attempt traces already stored in
``results/*/{method}_seed*/run_summary.json`` (no re-simulation needed), and
prints the numbers the theory document quotes.

Usage
-----
    python scripts/mechanism_analysis.py --root results/campaign_1023
    python scripts/mechanism_analysis.py --root results/campaign_1023 --json out.json
"""
from __future__ import annotations

import argparse
import glob
import json
import os
from collections import defaultdict

import numpy as np

ARCTIC_LAT = 70.0
#: advance thresholds to probe (seconds)
THRESHOLDS = (6.0, 9.0, 12.0, 15.0, 18.0)


def load(root: str) -> dict[str, list[dict]]:
    """method -> list of attempts pooled over seeds."""
    out: dict[str, list[dict]] = defaultdict(list)
    for p in sorted(glob.glob(os.path.join(root, "*_seed*", "run_summary.json"))):
        d = json.load(open(p, encoding="utf-8"))
        if not d.get("ok"):
            continue
        method = d.get("method") or os.path.basename(os.path.dirname(p)).rsplit("_seed", 1)[0]
        out[method].extend(d["final"]["attempts"])
    return out


def qsummary(x: np.ndarray) -> dict:
    if x.size == 0:
        return dict(n=0)
    return dict(
        n=int(x.size),
        p50=float(np.percentile(x, 50)),
        p75=float(np.percentile(x, 75)),
        p90=float(np.percentile(x, 90)),
        p95=float(np.percentile(x, 95)),
        max=float(x.max()),
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="results/campaign_1023")
    ap.add_argument("--json", default=None)
    args = ap.parse_args()

    arms = load(args.root)
    if not arms:
        print(f"no runs under {args.root}")
        return 1

    # ---------------------------------------------------------------- #
    # A. setup-time distribution F_z, by region and elevation band
    # ---------------------------------------------------------------- #
    print("=" * 78)
    print("A. T_setup distribution of SUCCESSFUL attempts, by region")
    print("   (t_setup_s is a property of geometry + protocol, not of the policy,")
    print("    so pooling over arms gives the feasibility curve F_z)")
    print("=" * 78)

    rows = []
    for latname, lo, hi in (("polar >70", 70.0, 90.0), ("mid 55-70", 55.0, 70.0),
                            ("equat <15", 0.0, 15.0)):
        vals = []
        for att in sum(arms.values(), []):
            lat = abs(att["latitude_abs_deg"])
            if lo <= lat < hi and att["success"]:
                v = att.get("t_setup_s")
                if v is not None and np.isfinite(v):
                    vals.append(v)
        s = qsummary(np.asarray(vals))
        rows.append(dict(region=latname, **s))
        if s["n"]:
            print(f"  {latname:<10} n={s['n']:6d}  p50={s['p50']:5.2f}  p75={s['p75']:5.2f}  "
                  f"p90={s['p90']:5.2f}  p95={s['p95']:5.2f}  max={s['max']:5.2f}")

    print("\n   same, polar split by elevation and plane change (the rule's predicate)")
    split = []
    for label, lo_e, hi_e, plane in (("polar, el<15, plane change", 0, 15, 1),
                                     ("polar, el<15, same plane", 0, 15, 0),
                                     ("polar, el>=15", 15, 90, None)):
        vals = []
        for att in sum(arms.values(), []):
            lat = abs(att["latitude_abs_deg"])
            if not (70.0 <= lat <= 90.0 and att["success"]):
                continue
            if not (lo_e <= att["elevation_deg"] < hi_e):
                continue
            if plane is not None and int(att.get("plane_change", 0)) != plane:
                continue
            v = att.get("t_setup_s")
            if v is not None and np.isfinite(v):
                vals.append(v)
        s = qsummary(np.asarray(vals))
        split.append(dict(regime=label, **s))
        if s["n"]:
            print(f"  {label:<28} n={s['n']:6d}  p50={s['p50']:5.2f}  p90={s['p90']:5.2f}  p95={s['p95']:5.2f}")

    # ---------------------------------------------------------------- #
    # B. failure-cause attribution in the polar region
    # ---------------------------------------------------------------- #
    print("\n" + "=" * 78)
    print("B. polar failure causes (share of all polar attempts)")
    print("=" * 78)
    causes = defaultdict(lambda: defaultdict(int))
    for m, atts in arms.items():
        for att in atts:
            if abs(att["latitude_abs_deg"]) < ARCTIC_LAT:
                continue
            causes[m][att["cause"]] += 1
    keys = sorted({k for c in causes.values() for k in c})
    print(f"  {'arm':<20}" + "".join(f"{k:>16}" for k in keys))
    for m in sorted(causes):
        tot = sum(causes[m].values())
        print(f"  {m:<20}" + "".join(f"{100 * causes[m][k] / tot:15.1f}%" for k in keys))

    # ---------------------------------------------------------------- #
    # C. does advance dominate the required quantile?  (per arm)
    # ---------------------------------------------------------------- #
    polar_q90 = next((r["p90"] for r in rows if r["region"].startswith("polar")), 12.0)
    polar_q95 = next((r["p95"] for r in rows if r["region"].startswith("polar")), 15.0)
    print("\n" + "=" * 78)
    print(f"C. polar attempts with advance >= q90={polar_q90:.2f}s / q95={polar_q95:.2f}s")
    print("=" * 78)
    print(f"  {'arm':<20}{'n_polar':>8}{'mean_adv':>10}{'>=q90':>8}{'>=q95':>8}{'>=12s':>8}{'HSR':>8}")
    per_arm = []
    for m in sorted(arms):
        ad, succ = [], []
        for att in arms[m]:
            if abs(att["latitude_abs_deg"]) < ARCTIC_LAT:
                continue
            ad.append(att["handover_advance_s"])
            succ.append(bool(att["success"]))
        if not ad:
            continue
        ad = np.asarray(ad, dtype=float)
        succ = np.asarray(succ)
        rec = dict(
            arm=m, n=int(ad.size), mean_adv=float(ad.mean()),
            frac_ge_q90=float((ad >= polar_q90).mean()),
            frac_ge_q95=float((ad >= polar_q95).mean()),
            frac_ge_12=float((ad >= 12.0).mean()),
            hsr=float(succ.mean()),
        )
        per_arm.append(rec)
        print(f"  {m:<20}{rec['n']:>8d}{rec['mean_adv']:>10.2f}"
              f"{100 * rec['frac_ge_q90']:>7.1f}%{100 * rec['frac_ge_q95']:>7.1f}%"
              f"{100 * rec['frac_ge_12']:>7.1f}%{100 * rec['hsr']:>7.1f}%")

    # ---------------------------------------------------------------- #
    # D. conditional success curve: P(success | advance bucket, elevation band)
    # ---------------------------------------------------------------- #
    print("\n" + "=" * 78)
    print("D. P(success | advance) in the polar region, by elevation band")
    print("   (if TFA holds, the curve is monotone in advance and saturates at the")
    print("    quantile where advance stops censoring T_setup)")
    print("=" * 78)
    buckets = [(0, 4), (4, 6), (6, 8), (8, 10), (10, 12), (12, 16), (16, 100)]
    for lo_e, hi_e in ((0, 15), (15, 30), (30, 90)):
        print(f"\n  elevation {lo_e}-{hi_e} deg")
        print(f"    {'advance':>12}{'n':>8}{'P(success)':>12}{'late':>8}{'window':>8}")
        for b0, b1 in buckets:
            n = ok = late = win = 0
            for m, atts in arms.items():
                for att in atts:
                    if abs(att["latitude_abs_deg"]) < ARCTIC_LAT:
                        continue
                    if not (lo_e <= att["elevation_deg"] < hi_e):
                        continue
                    a = att["handover_advance_s"]
                    if not (b0 <= a < b1):
                        continue
                    n += 1
                    ok += bool(att["success"])
                    late += att["cause"] == "late_handover"
                    win += att["cause"] == "window_exceeded"
            if n:
                print(f"    {b0:4.0f}-{b1:<6.0f}{n:>8d}{100 * ok / n:>11.1f}%"
                      f"{100 * late / n:>7.1f}%{100 * win / n:>7.1f}%")

    if args.json:
        json.dump(dict(setup_quantiles=rows, polar_split=split, per_arm=per_arm,
                       polar_q90=polar_q90, polar_q95=polar_q95),
                  open(args.json, "w", encoding="utf-8"), indent=2)
        print(f"\nwrote {args.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
