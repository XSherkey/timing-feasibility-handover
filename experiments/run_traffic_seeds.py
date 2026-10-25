"""B1: separate the three variance sources - policy seed, traffic seed, epoch - on the same frozen arms.

The paper's n = 10 is the policy seed.  A traffic seed is the environment RNG that draws sites, start
times and session arrivals, so re-running a frozen policy with a different traffic seed gives independent
episode blocks at no training cost.  This script reports, for the load-bearing arms:

  * every (policy seed x traffic seed) cell,
  * a variance decomposition (between-policy vs between-traffic),
  * the ordering between arms inside each traffic seed.

Run:  python experiments/run_traffic_seeds.py
Out:  results/routeA_r3/traffic_seeds/summary.json
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from r3lib import OUT, arctic, evaluate, summarise, write  # noqa: E402

POLICIES = [0, 1, 2, 3, 4]
TRAFFIC = [0, 1, 2, 3, 4]
ALMOND = {s: f"results/campaign_1023/almond_seed{s}" for s in POLICIES}
LAM8 = {s: f"results/routeA_f3/lam8.0/no_forensics_seed{s}" for s in POLICIES}

ARMS = {
    "no_shield": dict(kind="none", runs=ALMOND),
    "mined_16": dict(kind="rule", rule="min_advance:16@latitude_abs_deg>=68", runs=ALMOND),
    "deployed_18": dict(kind="rule", rule="min_advance:18@latitude_abs_deg>=68", runs=ALMOND),
    "tuned_constant": dict(kind="maxel", lead=18.0),
    "reward_lam8": dict(kind="none", runs=LAM8),
}


def var_split(cells: np.ndarray) -> dict:
    """cells: (policy, traffic).  Two-way ANOVA without replication."""
    p, q = cells.shape
    grand = cells.mean()
    ss_p = q * ((cells.mean(axis=1) - grand) ** 2).sum()
    ss_t = p * ((cells.mean(axis=0) - grand) ** 2).sum()
    ss_e = ((cells - cells.mean(axis=1, keepdims=True) - cells.mean(axis=0, keepdims=True) + grand) ** 2).sum()
    tot = ss_p + ss_t + ss_e
    return dict(share_policy=float(ss_p / tot) if tot else 0.0,
                share_traffic=float(ss_t / tot) if tot else 0.0,
                share_resid=float(ss_e / tot) if tot else 0.0,
                sd_policy=float(cells.mean(axis=1).std(ddof=1)),
                sd_traffic=float(cells.mean(axis=0).std(ddof=1)))


def main() -> int:
    out = {"policies": POLICIES, "traffic_seeds": TRAFFIC,
           "note": "traffic seed = env RNG seed (sites, start times, Poisson arrivals); policies frozen"}

    for arm, spec in ARMS.items():
        cells = np.full((len(POLICIES), len(TRAFFIC)), np.nan)
        for i, s in enumerate(POLICIES):
            for j, tr in enumerate(TRAFFIC):
                if spec["kind"] == "maxel":
                    r = evaluate(f"ts_{arm}_s{s}_t{tr}", policy="maxel", lead=spec["lead"], seed=tr)
                elif spec["kind"] == "rule":
                    r = evaluate(f"ts_{arm}_s{s}_t{tr}", run=spec["runs"][s], rule=spec["rule"], seed=tr)
                else:
                    r = evaluate(f"ts_{arm}_s{s}_t{tr}", run=spec["runs"][s], seed=tr)
                cells[i, j] = arctic(r)
        out[arm] = dict(cells=cells.tolist(),
                        by_traffic=[float(x) for x in cells.mean(axis=0)],
                        by_policy=[float(x) for x in cells.mean(axis=1)],
                        summary=summarise(cells.ravel().tolist()),
                        **var_split(cells))
        print(f"{arm:<16} mean {cells.mean():6.2f}  policy-sd {out[arm]['sd_policy']:5.2f} "
              f"traffic-sd {out[arm]['sd_traffic']:5.2f}  "
              f"share(policy) {out[arm]['share_policy']:.2f} share(traffic) {out[arm]['share_traffic']:.2f}")

    # does the ordering survive a change of traffic seed?
    order = {}
    for j, tr in enumerate(TRAFFIC):
        col = {a: out[a]["cells"][i][j] for a in ARMS for i in range(len(POLICIES))}
        per_arm = {a: float(np.mean([out[a]["cells"][i][j] for i in range(len(POLICIES))])) for a in ARMS}
        order[f"traffic{tr}"] = per_arm
        print(f"traffic {tr}: " + "  ".join(f"{a}={v:.1f}" for a, v in per_arm.items()))
    out["per_traffic_means"] = order

    write(OUT / "traffic_seeds" / "summary.json", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
