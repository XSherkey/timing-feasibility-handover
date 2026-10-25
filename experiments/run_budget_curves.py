"""Panel (b) of Fig. 9, corrected: the cluster branch previously ignored its own subsample and
bootstrapped the *full* log at every budget, so the curve was RNG noise (8, 7.0, 3.0 ...) rather than a
budget effect. This version draws a subsample of the stated size (whole (seed, site) blocks for the
cluster arm, individual attempts for the i.i.d. arm), then bootstraps *within that subsample* using the
matching unit. At the full budget both arms reduce to the full-data CI.
"""
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / "results" / "routeA_r3"
BAND = 68.0
BUDGETS = [250, 500, 1000, 2000, 4000, 8682]
REPS = 1000
EPS = 0.05


def load():
    rows = []
    for s in range(10):
        d = json.loads((ROOT / "results" / "campaign_1023" / f"ppomlp_seed{s}" / "run_summary.json")
                       .read_text(encoding="utf-8"))
        for a in d["final"]["attempts"]:
            if abs(float(a["latitude_abs_deg"])) < BAND:
                continue
            rows.append(dict(seed=s, site=a["site"], adv=float(a["handover_advance_s"]),
                             late=1 if a.get("cause") == "late_handover" else 0))
    return rows


def pava_decreasing(y, w):
    y = -np.asarray(y, float)
    w = np.asarray(w, float)
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


def crossing(rows) -> float:
    if not rows:
        return np.nan
    by = defaultdict(lambda: [0, 0])
    for r in rows:
        b = int(np.floor(r["adv"]))
        by[b][0] += r["late"]
        by[b][1] += 1
    xs = np.array(sorted(b for b in by if b < 27), dtype=float)
    if xs.size == 0:
        return np.nan
    late = np.array([by[b][0] for b in xs], float)
    n = np.array([by[b][1] for b in xs], float)
    fit = pava_decreasing(late / np.maximum(n, 1), n)
    for x, f in zip(xs, fit):
        if f <= EPS:
            return float(x)
    return np.nan


def width(v) -> float:
    v = np.asarray([x for x in v if np.isfinite(x)])
    return float(np.percentile(v, 97.5) - np.percentile(v, 2.5)) if v.size else float("nan")


def main() -> int:
    rows = load()
    blocks = defaultdict(list)
    for r in rows:
        blocks[(r["seed"], r["site"])].append(r)
    keys = list(blocks)
    rng = np.random.default_rng(7)
    out = dict(iid=[], cluster=[], reps=REPS, method="subsample the budget, then bootstrap inside it")
    for n in BUDGETS:
        n = min(n, len(rows))
        # ---- subsample: i.i.d. attempts vs whole blocks until the budget is met
        idx = rng.choice(len(rows), size=n, replace=False)
        sub_iid = [rows[i] for i in idx]
        perm = rng.permutation(len(keys))
        sub_cl, tot = [], 0
        for j in perm:
            sub_cl.extend(blocks[keys[j]])
            tot += len(blocks[keys[j]])
            if tot >= n:
                break
        sub_blocks = defaultdict(list)
        for r in sub_cl:
            sub_blocks[(r["seed"], r["site"])].append(r)
        sub_keys = list(sub_blocks)

        w_iid, w_cl = [], []
        for _ in range(REPS):
            boot = [sub_iid[i] for i in rng.integers(0, len(sub_iid), len(sub_iid))]
            w_iid.append(crossing(boot))
        for _ in range(REPS):
            boot = []
            for j in rng.choice(len(sub_keys), size=len(sub_keys), replace=True):
                boot.extend(sub_blocks[sub_keys[j]])
            w_cl.append(crossing(boot))
        out["iid"].append(dict(n=n, width=width(w_iid)))
        out["cluster"].append(dict(n=n, width=width(w_cl)))
        print(f"n={n:5d}  iid {out['iid'][-1]['width']:.2f}  cluster {out['cluster'][-1]['width']:.2f}")
    (RES / "passive_ci" / "budget_curves.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
