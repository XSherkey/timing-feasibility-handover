"""Review-25 item: does the lockbox ordering survive a change of traffic seed?

The three lockbox instances shift the twin epoch but keep traffic seed 0.  This run repeats the two
load-bearing contrasts (deployed 18 s vs no shield, and vs the tuned constant) at two further traffic
seeds on the evaluation window and on the +7 d lockbox instance.

Run:  python experiments/run_lockbox_traffic.py
Out:  results/routeA_r3/lockbox_traffic/summary.json
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from r3lib import LOCKBOX_EPOCHS, OUT, SEEDS, arctic, evaluate, summarise, write  # noqa: E402

ALMOND = {s: f"results/campaign_1023/almond_seed{s}" for s in SEEDS}
TRAFFIC = [0, 1, 2]
INSTANCES = {"eval": None, "lb+7": LOCKBOX_EPOCHS[0] if LOCKBOX_EPOCHS else 299.25}
ARMS = {
    "no_shield": dict(kind="none"),
    "deployed_18": dict(kind="rule", rule="min_advance:18@latitude_abs_deg>=68"),
    "tuned_constant": dict(kind="maxel", lead=18.0),
}


def main() -> int:
    out = {"traffic_seeds": TRAFFIC, "instances": {}, "arms": list(ARMS)}
    for inst, epoch in INSTANCES.items():
        cell = {}
        for arm, spec in ARMS.items():
            per_traffic = {}
            for tr in TRAFFIC:
                vals = []
                for s in SEEDS:
                    if spec["kind"] == "maxel":
                        r = evaluate(f"lbt_{inst}_{arm}_t{tr}_s{s}", policy="maxel", lead=spec["lead"],
                                     epoch_doy=epoch, seed=tr)
                    elif spec["kind"] == "rule":
                        r = evaluate(f"lbt_{inst}_{arm}_t{tr}_s{s}", run=ALMOND[s], rule=spec["rule"],
                                     epoch_doy=epoch, seed=tr)
                    else:
                        r = evaluate(f"lbt_{inst}_{arm}_t{tr}_s{s}", run=ALMOND[s], epoch_doy=epoch, seed=tr)
                    vals.append(arctic(r))
                per_traffic[tr] = dict(polar=vals, summary=summarise(vals))
                print(f"{inst:<6} {arm:<15} traffic {tr}  {per_traffic[tr]['summary']['mean']:6.2f}")
            cell[arm] = per_traffic
        out["instances"][inst] = cell

    # ordering check: deployed beats no shield, and ties the constant, at every seed
    print("\nordering per (instance, traffic):")
    for inst in INSTANCES:
        for tr in TRAFFIC:
            d = out["instances"][inst]["deployed_18"][tr]["summary"]["mean"]
            n = out["instances"][inst]["no_shield"][tr]["summary"]["mean"]
            c = out["instances"][inst]["tuned_constant"][tr]["summary"]["mean"]
            print(f"  {inst} t{tr}: deployed {d:6.2f} | no shield {n:6.2f} | constant {c:6.2f} | "
                  f"d-n {d - n:+6.2f} | d-c {d - c:+5.2f}")

    write(OUT / "lockbox_traffic" / "summary.json", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
