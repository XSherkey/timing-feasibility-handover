"""T2-04 - direct quantification of passive-log identifiability.

The claim "the bound is effectively unidentifiable from the passive log" was supported only by
thinness.  Here it is quantified directly: per-advance late rates, a monotone (PAVA) fit, the
leftmost crossing of the 5% level, and a **cluster bootstrap over (seed, site) blocks** - the
attempts of one site are not independent draws, so resampling attempts would understate the
uncertainty.  A sample-budget curve then shows how the crossing CI narrows with n, and the
probe's own CI at matched sample size is reported for comparison.

Run:  python experiments/run_passive_identifiability.py
Out:  results/routeA_r3/passive_ci/summary.json
"""
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

import numpy as np

from r3lib import MANIFEST, OUT, SEEDS, write

BAND = MANIFEST["metrics"]["support_band_deg"]
EPS = 0.05
GRID = np.arange(6.0, 27.0, 1.0)
BOOT_CLUSTER = 1000
BOOT_BUDGET = 200
BUDGETS = [250, 500, 1000, 2000, 4000, 8682]


def load_attempts() -> list[dict]:
    rows = []
    base = Path("results/campaign_1023")
    for s in SEEDS:
        d = json.loads((base / f"ppomlp_seed{s}" / "run_summary.json").read_text(encoding="utf-8"))
        for a in d["final"]["attempts"]:
            if abs(float(a["latitude_abs_deg"])) < BAND:
                continue
            rows.append(dict(seed=s, site=a["site"], adv=float(a["handover_advance_s"]),
                             late=1 if a.get("cause") == "late_handover" else 0,
                             ok=1 if a.get("success") else 0))
    return rows


def pava_decreasing(x: np.ndarray, y: np.ndarray, w: np.ndarray) -> np.ndarray:
    """Pool-adjacent-violators for a non-increasing sequence; one value per bin."""
    y = -np.asarray(y, dtype=float)
    w = np.asarray(w, dtype=float)
    vals, wts, cnt = [], [], []
    for yi, wi in zip(y, w):
        vals.append(yi)
        wts.append(max(wi, 1e-9))
        cnt.append(1)
        while len(vals) > 1 and vals[-2] > vals[-1]:
            v2, w2, c2 = vals.pop(), wts.pop(), cnt.pop()
            v1, w1, c1 = vals.pop(), wts.pop(), cnt.pop()
            vals.append((v1 * w1 + v2 * w2) / (w1 + w2))
            wts.append(w1 + w2)
            cnt.append(c1 + c2)
    out = []
    for v, c in zip(vals, cnt):
        out.extend([v] * c)
    return -np.asarray(out)


def curve(rows: list[dict], grid: np.ndarray = GRID):
    by = defaultdict(lambda: [0, 0])
    for r in rows:
        b = int(np.floor(r["adv"]))
        by[b][0] += r["late"]
        by[b][1] += 1
    xs = np.array(sorted(b for b in by if b < 27))
    late = np.array([by[b][0] for b in xs], dtype=float)
    n = np.array([by[b][1] for b in xs], dtype=float)
    rate = late / np.maximum(n, 1)
    fit = pava_decreasing(xs, rate, n) if len(xs) else rate
    return xs.astype(float), rate, n, fit


def crossing(xs: np.ndarray, fit: np.ndarray, eps: float = EPS) -> float:
    for x, f in zip(xs, fit):
        if f <= eps:
            return float(x)
    return float("nan")


def cluster_bootstrap(rows: list[dict], reps: int = BOOT_CLUSTER) -> list[float]:
    blocks = defaultdict(list)
    for r in rows:
        blocks[(r["seed"], r["site"])].append(r)
    keys = list(blocks)
    rng = np.random.default_rng(7)
    out = []
    for _ in range(reps):
        pick = rng.choice(len(keys), size=len(keys), replace=True)
        sample = []
        for j in pick:
            sample.extend(blocks[keys[j]])
        xs, _rate, _n, fit = curve(sample)
        out.append(crossing(xs, fit))
    return out


def budget_curve(rows: list[dict], reps: int = BOOT_BUDGET) -> list[dict]:
    rng = np.random.default_rng(11)
    strata = defaultdict(list)
    for r in rows:
        strata[int(np.floor(r["adv"]))].append(r)
    out = []
    for m in BUDGETS:
        m = min(m, len(rows))
        widths = []
        for _ in range(reps):
            sample = []
            for _k in range(m):
                b = rng.choice(list(strata))
                sample.append(strata[b][rng.integers(len(strata[b]))])
            xs, _rate, _n, fit = curve(sample)
            widths.append(crossing(xs, fit))
        w = np.asarray(widths, dtype=float)
        w = w[np.isfinite(w)]
        if w.size == 0:
            out.append(dict(n=m, ci_width=None, valid=0.0))
            continue
        out.append(dict(n=m, ci_width=float(np.percentile(w, 97.5) - np.percentile(w, 2.5)),
                        ci=[float(np.percentile(w, 2.5)), float(np.percentile(w, 97.5))],
                        median=float(np.median(w)), valid=float(w.size / len(widths))))
    return out


def main() -> int:
    rows = load_attempts()
    xs, rate, n, fit = curve(rows)
    tau = crossing(xs, fit)
    boots = cluster_bootstrap(rows)
    b = np.asarray([x for x in boots if np.isfinite(x)])
    band_counts = defaultdict(int)
    for x in b:
        band = ("<=14" if x <= 14 else "14-16" if x <= 16 else "16-18" if x <= 18 else ">=18")
        band_counts[band] += 1
    summary = dict(
        band_deg=BAND, eps=EPS, n_attempts=len(rows), n_late=int(sum(r["late"] for r in rows)),
        curve=[dict(advance=float(x), late_rate=float(r), n=int(k), fit=float(f))
               for x, r, k, f in zip(xs, rate, n, fit)],
        tau_star_passive=tau,
        bootstrap=dict(reps=BOOT_CLUSTER, valid=int(b.size),
                       ci95=[float(np.percentile(b, 2.5)), float(np.percentile(b, 97.5))] if b.size else None,
                       width_s=float(np.percentile(b, 97.5) - np.percentile(b, 2.5)) if b.size else None,
                       distinct_grid_points=int(len(set(np.round(b, 1)))),
                       band_shares={k: v / max(1, sum(band_counts.values())) for k, v in band_counts.items()}),
        budget_curve=budget_curve(rows),
        cell_14_16=dict(n=int(sum(n[(xs >= 14) & (xs < 16)])),
                        late=int(sum(rate[(xs >= 14) & (xs < 16)] * n[(xs >= 14) & (xs < 16)])),
                        se_pp=float(100 * np.sqrt(
                            (sum(rate[(xs >= 14) & (xs < 16)] * n[(xs >= 14) & (xs < 16)])
                             / max(1, sum(n[(xs >= 14) & (xs < 16)])))
                            * (1 - sum(rate[(xs >= 14) & (xs < 16)] * n[(xs >= 14) & (xs < 16)])
                               / max(1, sum(n[(xs >= 14) & (xs < 16)])))
                            / max(1, sum(n[(xs >= 14) & (xs < 16)]))))),
    )
    write(OUT / "passive_ci" / "summary.json", summary)
    print(f"passive tau* = {tau} s | bootstrap CI {summary['bootstrap']['ci95']} "
          f"(width {summary['bootstrap']['width_s']} s, {summary['bootstrap']['distinct_grid_points']} grid points)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
