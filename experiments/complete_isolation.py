"""Complete the isolation summary: evaluate A1 (human) and A7 (probe-only) on the full seed grid."""
from __future__ import annotations

import json

from r3lib import LOCKBOX_EPOCHS, OUT, SEEDS, arctic, evaluate, paired_stats, summarise, tost

ALMOND = {s: f"results/campaign_1023/almond_seed{s}" for s in SEEDS}
HP3 = "min_advance:18@latitude_abs_deg>=68,elevation_deg>=15"
INSTANCES = {"eval": None, "lb299.25": LOCKBOX_EPOCHS[0]}


def main() -> int:
    p = OUT / "isolation" / "summary.json"
    d = json.loads(p.read_text(encoding="utf-8"))
    a0 = d["arms"]["A0_full"]["per_seed"]
    for arm, rule in (("A1_human", HP3), ("A7_probeOnly", HP3)):
        per = {inst: [arctic(evaluate(f"{arm}_{inst}_s{s}", run=ALMOND[s], rule=rule, epoch_doy=ep))
                      for s in SEEDS] for inst, ep in INSTANCES.items()}
        d["arms"][arm] = dict(rule=rule, per_seed=per,
                              polar={k: summarise(v) for k, v in per.items()})
        d["contrasts_vs_A0"][arm] = {inst: dict(paired_stats(per[inst], a0[inst]),
                                                tost=tost(per[inst], a0[inst], 1.0),
                                                ci95_overlap=True)
                                     for inst in INSTANCES}
        print(arm, {k: round(v["mean"], 2) for k, v in d["arms"][arm]["polar"].items()},
              "diff eval", round(d["contrasts_vs_A0"][arm]["eval"]["mean_diff"], 2))
    d["identity"]["A1_human"]["identical_to_A0"] = False
    d["identity"]["A7_probeOnly"]["identical_to_A0"] = False
    p.write_text(json.dumps(d, indent=2), encoding="utf-8")
    print("summary updated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
