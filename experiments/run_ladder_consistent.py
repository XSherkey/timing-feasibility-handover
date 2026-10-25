"""Fig. 8 (the six-reference ladder) under the unified protocol: campaign policies, traffic seed 0,
ten policy seeds, nominal and +2 s of acquisition drift."""
from __future__ import annotations

from r3lib import OUT, SEEDS, arctic, evaluate, summarise, write

ALMOND = {s: f"results/campaign_1023/almond_seed{s}" for s in SEEDS}
PPO = {s: f"results/campaign_1023/ppomlp_seed{s}" for s in SEEDS}
NOFORE = {s: f"results/campaign_1023/no_forensics_seed{s}" for s in SEEDS}
LAM8 = {s: f"results/routeA_f3/lam8.0/no_forensics_seed{s}" for s in SEEDS}
R16 = "min_advance:16@latitude_abs_deg>=68"
R18 = "min_advance:18@latitude_abs_deg>=68"

ARMS = {
    "no_knowledge": dict(runs=NOFORE),
    "reward_lam8": dict(runs=LAM8),
    "narrative_16s_rule": dict(runs=NOFORE, rule=R16),
    "tuned_constant_18": dict(policy="maxel", lead=18.0),
    "deployed_probe_shield": dict(runs=ALMOND, rule=R18),
    "oracle": dict(runs=ALMOND, oracle=True),
}


def main() -> int:
    out = {"policy_set": "campaign", "traffic_seed": 0, "n": len(SEEDS), "regimes": {}}
    for acq, tag in ((1.2, "nominal"), (3.2, "plus2s")):
        out["regimes"][tag] = {}
        for arm, spec in ARMS.items():
            vals = []
            for s in SEEDS:
                if spec.get("policy") == "maxel":
                    r = evaluate(f"lad_{tag}_{arm}_s{s}", policy="maxel", lead=spec["lead"], acq=acq)
                elif spec.get("oracle"):
                    r = evaluate(f"lad_{tag}_{arm}_s{s}", run=spec["runs"][s], oracle=True, acq=acq)
                elif spec.get("rule"):
                    r = evaluate(f"lad_{tag}_{arm}_s{s}", run=spec["runs"][s], rule=spec["rule"], acq=acq)
                else:
                    r = evaluate(f"lad_{tag}_{arm}_s{s}", run=spec["runs"][s], acq=acq)
                vals.append(arctic(r))
            out["regimes"][tag][arm] = dict(polar=vals, summary=summarise(vals))
            print(f"{tag:8s} {arm:22s} {summarise(vals)['mean']:6.2f}")
    write(OUT / "ladder_consistent" / "summary.json", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
