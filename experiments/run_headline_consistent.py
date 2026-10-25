"""Headline protocol unification: rebuild Tables II and III (and therefore Fig. 5) on the same
campaign policies and traffic seed 0 that Tables VII and VIII use.

Arms (all evaluated on the test window, |lat| >= 70 deg, n = 10 campaign seeds):
  ppomlp_none        reward-only PPO-MLP, no shield
  noforensics_none   same architecture, knowledge mining disabled, no shield
  almond_none        full-system policies, no shield
  almond_rule16      full-system policies + mined 16 s rule        (mined-rule campaign arm)
  almond_rule18      full-system policies + tau_used = 18 s        (deployed algorithm)
  ppomlp_rule16      PPO-MLP + mined 16 s rule                      (knowledge as a shield on the baseline)
  maxel18            highest-elevation controller, fixed 18 s lead  (tuned constant)
  lam{...}           reward-penalty arms at seven coefficients
  oracle             per-attempt oracle shield

Run:  python experiments/run_headline_consistent.py
Out:  results/routeA_r3/headline_consistent/summary.json
"""
from __future__ import annotations

import json

from r3lib import OUT, SEEDS, arctic, evaluate, summarise, write

ALMOND = {s: f"results/campaign_1023/almond_seed{s}" for s in SEEDS}
PPO = {s: f"results/campaign_1023/ppomlp_seed{s}" for s in SEEDS}
NOFORE = {s: f"results/campaign_1023/no_forensics_seed{s}" for s in SEEDS}
LAMS = {
    "0.3": "results/routeA_f3/lam0.3", "0.5": "results/routeA_f3/lam0.5",
    "2": "results/routeA_f3/lam2.0", "8": "results/routeA_f3/lam8.0",
    "16": "results/routeA_g2/lam16", "32": "results/routeA_g2/lam32", "64": "results/routeA_g2/lam64",
}

ARMS = {
    "ppomlp_none": dict(kind="plain", runs=PPO),
    "noforensics_none": dict(kind="plain", runs=NOFORE),
    "almond_none": dict(kind="plain", runs=ALMOND),
    "almond_rule16": dict(kind="rule", rule="min_advance:16@latitude_abs_deg>=68", runs=ALMOND),
    "almond_rule18": dict(kind="rule", rule="min_advance:18@latitude_abs_deg>=68", runs=ALMOND),
    "ppomlp_rule16": dict(kind="rule", rule="min_advance:16@latitude_abs_deg>=68", runs=PPO),
    "maxel18": dict(kind="maxel", lead=18.0),
    "oracle": dict(kind="oracle", runs=ALMOND),
}


def main() -> int:
    out = {"policy_set": "campaign", "traffic_seed": 0, "window": "test", "n": len(SEEDS), "arms": {}}
    for arm, spec in ARMS.items():
        vals, causes = [], []
        for s in SEEDS:
            if spec["kind"] == "maxel":
                r = evaluate(f"hl_{arm}_s{s}", policy="maxel", lead=spec["lead"])
            elif spec["kind"] == "oracle":
                r = evaluate(f"hl_{arm}_s{s}", run=spec["runs"][s], oracle=True)
            elif spec["kind"] == "rule":
                r = evaluate(f"hl_{arm}_s{s}", run=spec["runs"][s], rule=spec["rule"])
            else:
                r = evaluate(f"hl_{arm}_s{s}", run=spec["runs"][s])
            vals.append(arctic(r))
            causes.append(r.get("polar_causes") or {})
        mean_causes = {k: sum(c.get(k, 0.0) for c in causes) / len(causes)
                       for k in ("ok", "late_handover", "window_exceeded", "no_route")}
        out["arms"][arm] = dict(polar=vals, summary=summarise(vals), causes=mean_causes)
        print(f"{arm:18s} {summarise(vals)['mean']:6.2f} +- {summarise(vals)['sd']:4.2f} | "
              f"late {100*mean_causes['late_handover']:5.1f}% win {100*mean_causes['window_exceeded']:4.1f}% "
              f"no_route {100*mean_causes['no_route']:4.1f}%")

    for lam, d in LAMS.items():
        vals, causes = [], []
        for s in SEEDS:
            r = evaluate(f"hl_lam{lam}_s{s}", run=f"{d}/no_forensics_seed{s}")
            vals.append(arctic(r))
            causes.append(r.get("polar_causes") or {})
        out["arms"][f"lam{lam}"] = dict(polar=vals, summary=summarise(vals),
                                        causes={k: sum(c.get(k, 0.0) for c in causes) / len(causes)
                                                for k in ("ok", "late_handover", "window_exceeded", "no_route")})
        print(f"lam {lam:>4s}            {summarise(vals)['mean']:6.2f} +- {summarise(vals)['sd']:4.2f}")

    write(OUT / "headline_consistent" / "summary.json", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
