"""T2-02 (consistent protocol) - rebuild the lockbox table with ONE policy set and ONE traffic seed.

Every earlier lockbox number mixed two things: the fixed-architecture replica policies and a
traffic seed equal to the policy-seed index.  This run fixes both: campaign policies
(results/campaign_1023/*_seed{s}), traffic seed 0 for every evaluation, n = 10 policy seeds, and the
same four instances (evaluation window + three epoch-shifted lockbox twins).

Run:  python experiments/run_lockbox_consistent.py
Out:  results/routeA_r3/lockbox_consistent/summary.json
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from r3lib import LOCKBOX_EPOCHS, OUT, SEEDS, arctic, evaluate, summarise, write

ALMOND = {s: f"results/campaign_1023/almond_seed{s}" for s in SEEDS}
PPO = {s: f"results/campaign_1023/ppomlp_seed{s}" for s in SEEDS}
LAM8 = {s: f"results/routeA_f3/lam8.0/no_forensics_seed{s}" for s in SEEDS}

ARMS = {
    "mined_16": dict(kind="rule", rule="min_advance:16@latitude_abs_deg>=68", runs=ALMOND),
    "deployed_18": dict(kind="rule", rule="min_advance:18@latitude_abs_deg>=68", runs=ALMOND),
    "tuned_constant": dict(kind="maxel", lead=18.0),
    "ppomlp_mined_16": dict(kind="rule", rule="min_advance:16@latitude_abs_deg>=68", runs=PPO),
    "reward_lam8": dict(kind="none", runs=LAM8),
    "oracle": dict(kind="oracle", runs=ALMOND),
}


def main() -> int:
    instances = {"eval": None, **{f"lb{e:g}": e for e in LOCKBOX_EPOCHS}}
    out = {"policy_set": "campaign (almond_seed*/ppomlp_seed*/no_forensics_seed*)",
           "traffic_seed": 0, "n": len(SEEDS), "instances": {}}
    for inst, epoch in instances.items():
        cell = {}
        for arm, spec in ARMS.items():
            vals = []
            for s in SEEDS:
                if spec["kind"] == "maxel":
                    r = evaluate(f"lbx_{inst}_{arm}_s{s}", policy="maxel", lead=spec["lead"], epoch_doy=epoch)
                elif spec["kind"] == "oracle":
                    r = evaluate(f"lbx_{inst}_{arm}_s{s}", run=spec["runs"][s], oracle=True, epoch_doy=epoch)
                elif spec["kind"] == "rule":
                    r = evaluate(f"lbx_{inst}_{arm}_s{s}", run=spec["runs"][s], rule=spec["rule"],
                                 epoch_doy=epoch)
                else:
                    r = evaluate(f"lbx_{inst}_{arm}_s{s}", run=spec["runs"][s], epoch_doy=epoch)
                vals.append(arctic(r))
            cell[arm] = dict(polar=vals, summary=summarise(vals))
        out["instances"][inst] = cell
        print(inst, {k: round(v["summary"]["mean"], 2) for k, v in cell.items()})
    write(OUT / "lockbox_consistent" / "summary.json", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
