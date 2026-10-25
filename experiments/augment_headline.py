"""Augment the headline summary with satisfaction S (cache hits only) and redraw Fig. 5."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from r3lib import OUT, SEEDS, evaluate

ROOT = Path(__file__).resolve().parents[1]
ALMOND = {s: f"results/campaign_1023/almond_seed{s}" for s in SEEDS}
PPO = {s: f"results/campaign_1023/ppomlp_seed{s}" for s in SEEDS}
NOFORE = {s: f"results/campaign_1023/no_forensics_seed{s}" for s in SEEDS}
LAMS = {"0.3": "results/routeA_f3/lam0.3", "0.5": "results/routeA_f3/lam0.5",
        "2": "results/routeA_f3/lam2.0", "8": "results/routeA_f3/lam8.0",
        "16": "results/routeA_g2/lam16", "32": "results/routeA_g2/lam32", "64": "results/routeA_g2/lam64"}

SPEC = {
    "ppomlp_none": dict(runs=PPO),
    "noforensics_none": dict(runs=NOFORE),
    "almond_none": dict(runs=ALMOND),
    "almond_rule16": dict(runs=ALMOND, rule="min_advance:16@latitude_abs_deg>=68"),
    "almond_rule18": dict(runs=ALMOND, rule="min_advance:18@latitude_abs_deg>=68"),
    "ppomlp_rule16": dict(runs=PPO, rule="min_advance:16@latitude_abs_deg>=68"),
    "maxel18": dict(policy="maxel", lead=18.0),
    "oracle": dict(runs=ALMOND, oracle=True),
}
for lam, d in LAMS.items():
    SPEC[f"lam{lam}"] = dict(runs={s: f"{d}/no_forensics_seed{s}" for s in SEEDS})


def main() -> int:
    p = OUT / "headline_consistent" / "summary.json"
    d = json.loads(p.read_text(encoding="utf-8"))
    for arm, spec in SPEC.items():
        sat, sat_arc = [], []
        for s in SEEDS:
            kw = dict(epoch_doy=None)
            if spec.get("policy") == "maxel":
                r = evaluate(f"hl_{arm}_s{s}", policy="maxel", lead=spec["lead"])
            elif spec.get("oracle"):
                r = evaluate(f"hl_{arm}_s{s}", run=spec["runs"][s], oracle=True)
            elif spec.get("rule"):
                r = evaluate(f"hl_{arm}_s{s}", run=spec["runs"][s], rule=spec["rule"])
            else:
                r = evaluate(f"hl_{arm}_s{s}", run=spec["runs"][s])
            sat.append(float(r.get("satisfaction", float("nan"))))
            sat_arc.append(float(r.get("satisfaction_arctic", float("nan"))))
        d["arms"][arm]["satisfaction"] = sat
        d["arms"][arm]["satisfaction_mean"] = float(np.nanmean(sat))
        d["arms"][arm]["satisfaction_sd"] = float(np.nanstd(sat, ddof=1))
        print(f"{arm:18s} S {d['arms'][arm]['satisfaction_mean']:6.2f} +- {d['arms'][arm]['satisfaction_sd']:4.2f}")
    p.write_text(json.dumps(d, indent=2), encoding="utf-8")
    print("summary augmented")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
