"""Complete the oracle ladder at the two remaining drift regimes (unified protocol)."""
from __future__ import annotations

import json
from pathlib import Path

from r3lib import OUT, SEEDS, arctic, evaluate, summarise

ALMOND = {s: f"results/campaign_1023/almond_seed{s}" for s in SEEDS}
NOFORE = {s: f"results/campaign_1023/no_forensics_seed{s}" for s in SEEDS}
LAM8 = {s: f"results/routeA_f3/lam8.0/no_forensics_seed{s}" for s in SEEDS}
R16 = "min_advance:16@latitude_abs_deg>=68"

ARMS = {
    "no_knowledge": dict(runs=NOFORE),
    "reward_lam8": dict(runs=LAM8),
    "mined_16": dict(runs=ALMOND, rule=R16),
    "oracle": dict(runs=ALMOND, oracle=True),
}


def main() -> int:
    p = OUT / "ladder_consistent" / "summary.json"
    d = json.loads(p.read_text(encoding="utf-8"))
    for acq, tag in ((4.4, "plus3p2s"), (5.6, "plus4p4s")):
        d["regimes"].setdefault(tag, {})
        for arm, spec in ARMS.items():
            vals = []
            for s in SEEDS:
                if spec.get("oracle"):
                    r = evaluate(f"lad_{tag}_{arm}_s{s}", run=spec["runs"][s], oracle=True, acq=acq)
                elif spec.get("rule"):
                    r = evaluate(f"lad_{tag}_{arm}_s{s}", run=spec["runs"][s], rule=spec["rule"], acq=acq)
                else:
                    r = evaluate(f"lad_{tag}_{arm}_s{s}", run=spec["runs"][s], acq=acq)
                vals.append(arctic(r))
            d["regimes"][tag][arm] = dict(polar=vals, summary=summarise(vals))
            print(tag, arm, round(summarise(vals)["mean"], 2))
    p.write_text(json.dumps(d, indent=2), encoding="utf-8")
    print("ladder completed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
