"""Final protocol unification: the frozen-policy factorial (Tables C1-C3, Fig. 2) on campaign
policies with traffic seed 0.

Arms (test window, |lat| >= 70 deg, n = 10 campaign seeds):
  none, rule16, rule18, rule20, oracle
C3 (drift response per seed) is rebuilt from the already-unified drift_margin run.

Run:  python experiments/run_factorial_consistent.py
Out:  results/routeA_r3/factorial_consistent/summary.json
"""
from __future__ import annotations

from r3lib import OUT, SEEDS, arctic, evaluate, late_share, summarise, write

ALMOND = {s: f"results/campaign_1023/almond_seed{s}" for s in SEEDS}
ARMS = {
    "none": dict(),
    "rule16": dict(rule="min_advance:16@latitude_abs_deg>=68"),
    "rule18": dict(rule="min_advance:18@latitude_abs_deg>=68"),
    "rule20": dict(rule="min_advance:20@latitude_abs_deg>=68"),
    "oracle": dict(oracle=True),
}


def main() -> int:
    out = {"policy_set": "campaign", "traffic_seed": 0, "window": "test", "n": len(SEEDS), "arms": {}}
    for arm, spec in ARMS.items():
        polar, late = [], []
        for s in SEEDS:
            if spec.get("oracle"):
                r = evaluate(f"fc_{arm}_s{s}", run=ALMOND[s], oracle=True)
            elif spec.get("rule"):
                r = evaluate(f"fc_{arm}_s{s}", run=ALMOND[s], rule=spec["rule"])
            else:
                r = evaluate(f"fc_{arm}_s{s}", run=ALMOND[s])
            polar.append(arctic(r))
            lv = late_share(r)
            late.append(0.0 if lv != lv else lv)
        out["arms"][arm] = dict(polar=polar, late=late, summary=summarise(polar),
                                late_summary=summarise(late))
        print(arm, "polar", round(summarise(polar)["mean"], 2), "+-", round(summarise(polar)["sd"], 2),
              "| late", round(summarise(late)["mean"], 2), "%")
    write(OUT / "factorial_consistent" / "summary.json", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
