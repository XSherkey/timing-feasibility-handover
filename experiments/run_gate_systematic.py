"""T2-05 - systematic evaluation of the audit gate on a fixed candidate bank.

Twenty candidates are drawn from the constraint grammar and their *true* held-out effect is
measured once (test window).  The gate then sees only a short validation replay and must decide.
Because the CLI cannot vary the number of replay episodes directly, the replay budget is varied
through the number of traffic scenarios replayed (1 scenario = the short replay, 3 = the long
replay); this is stated in the paper.

Run:  python experiments/run_gate_systematic.py
Out:  results/routeA_r3/gate_systematic/summary.json
"""
from __future__ import annotations

import itertools
import json
from pathlib import Path

import numpy as np

from r3lib import OUT, SEEDS, arctic, evaluate, summarise, write

SEL_SEEDS = [0, 1, 2]
MARGIN = 2.0
ADMIT_PP = 5.0

# (label, rule) - a bank that mixes magnitudes, scopes, and structural effects
BANK = [
    ("G01", "min_advance:18@latitude_abs_deg>=68"),                  # the system's own proposal
    ("G02", "min_advance:8@latitude_abs_deg>=68"),                   # under-protection
    ("G03", "min_advance:18@latitude_abs_deg>=0"),                  # global scope, harmful
    ("G04", "min_advance:28@latitude_abs_deg>=68"),                 # over-protection far above plateau
    ("G05", "min_advance:18@elevation_deg>=15"),                    # wrong field
    ("G06", "min_advance:18@latitude_abs_deg>=70"),                 # near-miss scope
    ("G07", "prefer_same_plane:0@latitude_abs_deg>=68"),            # structural
    ("G08", "min_advance:18@latitude_abs_deg>=68,elevation_deg>=15"),
    ("G09", "min_advance:18@latitude_abs_deg>=68,latitude_abs_deg<=75"),
    ("G10", "min_advance:26@latitude_abs_deg>=0"),
    ("G11", "cap_advance:20@latitude_abs_deg>=68"),                 # cap, may hurt
    ("G12", "min_advance:18@remaining_visibility_s>=240"),
    ("G13", "min_advance:18@isl_hop_count<=0"),
    ("G14", "prefer_long_visibility:0@latitude_abs_deg>=68"),
    ("G15", "forbid_unrouted_target:0@latitude_abs_deg>=0"),
    ("G16", "min_advance:22@latitude_abs_deg>=68"),
    ("G17", "min_advance:18@latitude_abs_deg>=60"),
    ("G18", "min_advance:12@latitude_abs_deg>=68"),
    ("G19", "min_advance:30@latitude_abs_deg>=68"),
    ("G20", "prefer_same_plane:0@latitude_abs_deg>=0"),
    # deliberately harmful: caps that cut the lead below the acquisition requirement
    ("G21", "cap_advance:6@latitude_abs_deg>=68"),
    ("G22", "cap_advance:8@latitude_abs_deg>=68"),
    ("G23", "cap_advance:10@latitude_abs_deg>=0"),
    ("G24", "cap_advance:12@latitude_abs_deg>=68"),
    ("G25", "prefer_long_visibility:0@latitude_abs_deg>=0"),
    ("G26", "cap_advance:4@latitude_abs_deg>=68"),
]


def main() -> int:
    rows = []
    base_test = {s: arctic(evaluate(f"gate_base_test_s{s}", run=f"results/campaign_1023/almond_seed{s}"))
                 for s in SEL_SEEDS}
    base_val_short = {s: arctic(evaluate(f"gate_base_val1_s{s}", run=f"results/campaign_1023/almond_seed{s}",
                                         window="validation", traffic=1.0)) for s in SEL_SEEDS}
    base_val_long = {s: arctic(evaluate(f"gate_base_val3_s{s}", run=f"results/campaign_1023/almond_seed{s}",
                                        window="validation")) for s in SEL_SEEDS}
    for name, rule in BANK:
        short, long_, test = [], [], []
        for s in SEL_SEEDS:
            run = f"results/campaign_1023/almond_seed{s}"
            short.append(arctic(evaluate(f"gate_{name}_short_s{s}", run=run, rule=rule,
                                         window="validation", traffic=1.0)) - base_val_short[s])
            long_.append(arctic(evaluate(f"gate_{name}_long_s{s}", run=run, rule=rule,
                                         window="validation")) - base_val_long[s])
            test.append(arctic(evaluate(f"gate_{name}_test_s{s}", run=run, rule=rule)) - base_test[s])
        rows.append(dict(id=name, rule=rule,
                         delta_short=float(np.mean(short)), delta_long=float(np.mean(long_)),
                         delta_test=float(np.mean(test)),
                         sd_long=float(np.std(long_, ddof=1))))
        print(f"{name} {rule[:44]:44s} short {rows[-1]['delta_short']:+6.2f} "
              f"long {rows[-1]['delta_long']:+6.2f} test {rows[-1]['delta_test']:+6.2f}")

    # classifier of the *true* effect
    def cls(d: float) -> str:
        return "harmful" if d <= -1.0 else ("good" if d >= ADMIT_PP else "neutral")

    for r in rows:
        r["class"] = cls(r["delta_test"])
        for budget, key in (("short", "delta_short"), ("long", "delta_long")):
            r[f"admit_{budget}"] = bool(r[key] >= ADMIT_PP)
    conf = {}
    for budget in ("short", "long"):
        c = {k: dict(admit=0, reject=0) for k in ("harmful", "neutral", "good")}
        for r in rows:
            c[r["class"]]["admit" if r[f"admit_{budget}"] else "reject"] += 1
        false_accept = c["harmful"]["admit"] / max(1, c["harmful"]["admit"] + c["harmful"]["reject"])
        false_reject = c["good"]["reject"] / max(1, c["good"]["admit"] + c["good"]["reject"])
        # system-level HSR: gate on commits the best admitted candidate; gate off commits them all
        admitted = [r for r in rows if r[f"admit_{budget}"]]
        best = max(admitted, key=lambda r: r["delta_test"]) if admitted else None
        worst = min(rows, key=lambda r: r["delta_test"])
        conf[budget] = dict(confusion=c, false_accept=false_accept, false_reject=false_reject,
                            n_admitted=len(admitted),
                            hsr_gate_on_pp=best["delta_test"] if best else None,
                            hsr_gate_off_worst_pp=worst["delta_test"],
                            mean_delta_admitted_pp=float(np.mean([r["delta_test"] for r in admitted]))
                            if admitted else None)
    out = dict(admit_pp=ADMIT_PP, bank=rows, gate=conf,
               base_test={str(k): v for k, v in base_test.items()})
    write(OUT / "gate_systematic" / "summary.json", out)
    print("gate:", json.dumps(conf["long"], indent=1)[:400])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
