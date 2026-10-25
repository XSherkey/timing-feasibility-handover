"""Review-26 item 1: precision of the threshold estimate at equal budget, and the cluster structure.

Three estimators are compared on the same passive attempt logs:

  naive  - 95th percentile of the realised requirement among *successful* attempts (ignores censoring);
  KM     - Kaplan-Meier survival of the requirement, with late attempts right-censored at their advance;
  probe  - the same KM estimator, but on attempts whose advance is *forced* uniformly over the grid, which is
           what the probe does; at equal budget this is a simulation of the probe's observation scheme, not a
           second campaign.

Clusters are (policy seed, site), the blocking unit of the paper's cluster bootstrap.

Out: results/routeA_r3/precision/summary.json
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
ATT = ROOT / ".tmp" / "att"
OUT = ROOT / "results" / "routeA_r3" / "precision"
GRID = np.arange(6.0, 26.5, 2.0)
EPS = 0.05
TRUTH = 16.0          # probe crossing, five seeds, Section V-C
BUDGETS = [300, 600, 1200, 2400]
REPS = 300


def load():
    rows = []
    for s in range(5):
        p = ATT / f"attempts_s{s}.json"
        for a in json.loads(p.read_text(encoding="utf-8")):
            if abs(a["latitude_abs_deg"]) < 70.0:
                continue
            if a["cause"] == "no_route":
                continue
            rows.append(dict(seed=s, site=a["site"], adv=float(a["handover_advance_s"]),
                             tz=float(a["t_setup_s"]), ok=bool(a["success"]),
                             late=a["cause"] == "late_handover"))
    return rows


def km_curve(sample):
    """Kaplan-Meier survival of T_z with right-censoring at the advance for late attempts."""
    tz = np.array([r["tz"] if r["ok"] else r["adv"] for r in sample], dtype=float)
    ev = np.array([1 if r["ok"] else 0 for r in sample], dtype=int)
    order = np.argsort(tz)
    tz, ev = tz[order], ev[order]
    surv, s = [], 1.0
    n = len(tz)
    i = 0
    while i < n:
        t = tz[i]
        d = int(ev[i:n][tz[i:n] == t].sum())
        c = int((tz[i:n] == t).sum()) - d
        if n > 0:
            if d:
                s *= (1.0 - d / n)
            surv.append((t, s))
        n -= (d + c)
        i += int((tz[i:] == t).sum())
    return surv


def crossing(sample):
    """Leftmost grid advance at which the estimated survival drops to or below eps."""
    surv = km_curve(sample)
    for g in GRID:
        s_at = 1.0
        for t, s in surv:
            if t <= g:
                s_at = s
        if s_at <= EPS:
            return float(g)
    return float(GRID[-1])


def naive_estimate(sample):
    ok = [r["tz"] for r in sample if r["ok"]]
    if len(ok) < 20:
        return None
    return float(np.percentile(ok, 95))


def probe_sample(sample, rng):
    """Force advances uniformly on the grid and keep only what an observer could know."""
    out = []
    for r in sample:
        forced = float(rng.choice(GRID))
        if forced >= r["tz"]:
            out.append(dict(r, adv=forced, ok=True, late=False))
        else:
            out.append(dict(r, adv=forced, ok=False, late=True))
    return out


def main() -> int:
    rows = load()
    sites = sorted({(r["seed"], r["site"]) for r in rows})
    sizes = []
    means = []
    for key in sites:
        vals = [r["tz"] for r in rows if (r["seed"], r["site"]) == key]
        sizes.append(len(vals))
        means.append(float(np.mean(vals)))
    summary = dict(n_attempts=len(rows), n_late=int(sum(1 for r in rows if r["late"])),
                   n_clusters=len(sites), cluster_size_median=float(np.median(sizes)),
                   cluster_size_max=int(max(sizes)), cluster_mean_sd=float(np.std(means, ddof=1)),
                   cluster_mean_range=[float(min(means)), float(max(means))], budgets={})
    print(f"attempts {len(rows)}, clusters {len(sites)}, "
          f"size med {np.median(sizes):.0f} max {max(sizes)}, cluster-mean sd {np.std(means, ddof=1):.2f}s")

    rng = np.random.default_rng(2026)
    for b in BUDGETS:
        res = {"naive": [], "km": [], "probe": [], "naive_cluster": [], "km_cluster": []}
        for _ in range(REPS):
            iid = [rows[i] for i in rng.integers(0, len(rows), size=b)]
            # cluster bootstrap: resample (seed, site) blocks with replacement
            pick = rng.integers(0, len(sites), size=len(sites))
            clus = []
            for k in pick:
                key = sites[k]
                block = [r for r in rows if (r["seed"], r["site"]) == key]
                if block:
                    clus.extend(block[i] for i in rng.integers(0, len(block), size=max(1, b // len(sites))))
            clus = clus[:b]
            if len(clus) < 60:
                continue
            res["km"].append(crossing(iid))
            nv = naive_estimate(iid)
            if nv is not None:
                res["naive"].append(nv)
            res["probe"].append(crossing(probe_sample(iid, rng)))
            if len(clus) >= 60:
                res["km_cluster"].append(crossing(clus))
                nvc = naive_estimate(clus)
                if nvc is not None:
                    res["naive_cluster"].append(nvc)
        cell = {}
        for k, v in res.items():
            if not v:
                continue
            v = np.array(v, dtype=float)
            cell[k] = dict(median=float(np.median(v)), err=float(np.median(np.abs(v - TRUTH))),
                           lo=float(np.percentile(v, 2.5)), hi=float(np.percentile(v, 97.5)),
                           width=float(np.percentile(v, 97.5) - np.percentile(v, 2.5)), reps=int(len(v)))
        summary["budgets"][str(b)] = cell
        print(f"n={b:5d}  KM err {cell['km']['err']:.2f} width {cell['km']['width']:.2f} | "
              f"KM-cluster err {cell.get('km_cluster', {}).get('err', float('nan')):.2f} "
              f"width {cell.get('km_cluster', {}).get('width', float('nan')):.2f} | "
              f"probe err {cell['probe']['err']:.2f} width {cell['probe']['width']:.2f} | "
              f"naive err {cell['naive']['err']:.2f}")

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print("written", OUT / "summary.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
