"""Add the narrative-16s-rule arm at the two remaining drift regimes so every ladder column is consistent."""
from __future__ import annotations

import json
from pathlib import Path

from r3lib import OUT, SEEDS, arctic, evaluate, summarise

NOFORE = {s: f"results/campaign_1023/no_forensics_seed{s}" for s in SEEDS}
R16 = "min_advance:16@latitude_abs_deg>=68"


def main() -> int:
    p = OUT / "ladder_consistent" / "summary.json"
    d = json.loads(p.read_text(encoding="utf-8"))
    for acq, tag in ((4.4, "plus3p2s"), (5.6, "plus4p4s")):
        vals = [arctic(evaluate(f"lad_{tag}_narrative_16s_rule_s{s}", run=NOFORE[s], rule=R16, acq=acq))
                for s in SEEDS]
        d["regimes"][tag]["narrative_16s_rule"] = dict(polar=vals, summary=summarise(vals))
        print(tag, "narrative_16s_rule", round(summarise(vals)["mean"], 2))
    p.write_text(json.dumps(d, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
