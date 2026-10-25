"""Add the no-shield arm to the consistent lockbox table (campaign policies, traffic seed 0)."""
from __future__ import annotations

import json
from pathlib import Path

from r3lib import LOCKBOX_EPOCHS, OUT, SEEDS, arctic, evaluate, summarise

ALMOND = {s: f"results/campaign_1023/almond_seed{s}" for s in SEEDS}
PPO = {s: f"results/campaign_1023/ppomlp_seed{s}" for s in SEEDS}


def main() -> int:
    p = OUT / "lockbox_consistent" / "summary.json"
    d = json.loads(p.read_text(encoding="utf-8"))
    inst_epoch = {"eval": None, **{f"lb{e:g}": e for e in LOCKBOX_EPOCHS}}
    for inst, epoch in inst_epoch.items():
        for arm, runs in (("no_shield", ALMOND), ("ppomlp_no_shield", PPO)):
            if arm in d["instances"][inst]:
                continue
            vals = [arctic(evaluate(f"lbx_{inst}_{arm}_s{s}", run=runs[s], epoch_doy=epoch))
                    for s in SEEDS]
            d["instances"][inst][arm] = dict(polar=vals, summary=summarise(vals))
            print(inst, arm, round(sum(vals) / len(vals), 2))
    p.write_text(json.dumps(d, indent=2), encoding="utf-8")
    print("summary updated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
