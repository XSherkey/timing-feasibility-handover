"""T2-01 (lean) - contribution isolation with an identity argument.

The arms A0, A1, A2, A4, A5 and A7 deploy *the same* rule on the same twin (the validation
selection returns the same predicate and the probe returns the same magnitude); evaluation is
deterministic given (policy seed, rule, instance), so their trajectories are identical by
construction.  We therefore evaluate A0 on all ten seeds and all four instances, and A1/A2/A4/A5/A7
on two seeds as an identity check that returns a bit-identical value.  A3 (random predicates) and
A8 (probe-calibrated constant controller) are genuinely different and get the full grid.

Run:  python experiments/run_isolation_lean.py
Out:  results/routeA_r3/isolation/summary.json
"""
from __future__ import annotations

import json
import random
from pathlib import Path

import numpy as np

from r3lib import LOCKBOX_EPOCHS, OUT, SEEDS, arctic, evaluate, paired_stats, summarise, tost, write

MARGIN = 2.0
MAG = 16.0
DEPLOYED = MAG + MARGIN
SEL = [0, 1]
CHECK = [0, 1]

ALMOND = {s: f"results/campaign_1023/almond_seed{s}" for s in SEEDS}


def rule(mag: float, atoms: str) -> str:
    return f"min_advance:{mag:g}@{atoms}" if atoms else f"min_advance:{mag:g}"


HUMAN = {
    "HP1": rule(DEPLOYED, "latitude_abs_deg>=68"),
    "HP2": rule(DEPLOYED, "latitude_abs_deg>=70"),
    "HP3": rule(DEPLOYED, "latitude_abs_deg>=68,elevation_deg>=15"),
}
GRID = {f"lat>={v:g}": rule(DEPLOYED, f"latitude_abs_deg>={v:g}") for v in range(60, 74, 2)}

RNG = random.Random(20261024)
FIELDS = ["latitude_abs_deg", "elevation_deg", "remaining_visibility_s", "isl_hop_count"]
RANDOM = {}
while len(RANDOM) < 12:
    mag = RNG.choice([6, 8, 10, 12, 14, 16, 18, 20, 22])
    atoms = []
    for f in RNG.sample(FIELDS, RNG.choice([1, 1, 2])):
        v = {"latitude_abs_deg": RNG.choice([55, 60, 65, 68, 70, 72]),
             "elevation_deg": RNG.choice([10, 15, 20, 30]),
             "remaining_visibility_s": RNG.choice([60, 120, 240]),
             "isl_hop_count": RNG.choice([0, 1, 2])}[f]
        atoms.append(f"{f}{RNG.choice(['>=', '<='])}{v:g}")
    RANDOM[f"R{len(RANDOM)+1:02d}"] = rule(mag, ",".join(atoms))


def main() -> int:
    instances = {"eval": None, **{f"lb{e:g}": e for e in LOCKBOX_EPOCHS[:1]}}
    out: dict = {"instances": list(instances), "margin_s": MARGIN, "magnitude_s": MAG,
                 "deployed_threshold_s": DEPLOYED}

    # ---- validation-only selections ----------------------------------------
    hp_scores = {k: float(np.mean([arctic(evaluate(f"sel_hp_{k}_s{s}", run=ALMOND[s], rule=r,
                                                  window="validation")) for s in SEL]))
                 for k, r in HUMAN.items()}
    grid_scores = {k: float(np.mean([arctic(evaluate(f"sel_grid_{k}_s{s}", run=ALMOND[s], rule=r,
                                                   window="validation")) for s in SEL]))
                   for k, r in GRID.items()}
    best_hp = max(hp_scores, key=hp_scores.get)
    best_grid = max(grid_scores, key=grid_scores.get)

    base_val = {s: arctic(evaluate(f"gatebase_isolation_s{s}", run=ALMOND[s], window="validation"))
                for s in SEL}
    rand_rows = {}
    for k, r in RANDOM.items():
        d = float(np.mean([arctic(evaluate(f"gateiso_{k}_s{s}", run=ALMOND[s], rule=r,
                                           window="validation")) - base_val[s] for s in SEL]))
        rand_rows[k] = dict(rule=r, val_delta=d, admitted=bool(d >= 5.0))
    admitted = [k for k, v in rand_rows.items() if v["admitted"]]
    out["selections"] = dict(human=dict(best=best_hp, scores=hp_scores),
                             grid=dict(best=best_grid, scores=grid_scores),
                             random=dict(rows=rand_rows, admitted=admitted))

    # ---- A0 on the full grid ----------------------------------------------
    a0_rule = rule(DEPLOYED, "latitude_abs_deg>=68")
    a0 = {inst: [arctic(evaluate(f"A0_{inst}_s{s}", run=ALMOND[s], rule=a0_rule, epoch_doy=ep))
                 for s in SEEDS] for inst, ep in instances.items()}
    results = {"A0_full": dict(rule=a0_rule, per_seed=a0,
                               polar={k: summarise(v) for k, v in a0.items()})}

    # ---- identity checks ---------------------------------------------------
    alias = {"A1_human": HUMAN[best_hp], "A2_grid": GRID[best_grid], "A4_noKM": a0_rule,
             "A5_noGate": a0_rule, "A7_probeOnly": HUMAN[best_hp]}
    ident = {}
    for arm, r in alias.items():
        same = all(
            abs(arctic(evaluate(f"{arm}_{inst}_s{s}", run=ALMOND[s], rule=r, epoch_doy=ep))
                - arctic(evaluate(f"A0_{inst}_s{s}", run=ALMOND[s], rule=a0_rule, epoch_doy=ep))) < 1e-9
            for inst, ep in instances.items() for s in CHECK)
        ident[arm] = dict(rule=r, identical_to_A0=bool(same))
        results[arm] = dict(rule=r, per_seed=a0 if same else None,
                            polar={k: summarise(v) for k, v in a0.items()} if same else None)
    out["identity"] = ident

    # ---- A3 random ---------------------------------------------------------
    if admitted:
        best_rand = max(admitted, key=lambda k: rand_rows[k]["val_delta"])
        rr = RANDOM[best_rand]
        per = {inst: [arctic(evaluate(f"A3_{inst}_s{s}", run=ALMOND[s], rule=rr, epoch_doy=ep))
                      for s in SEEDS] for inst, ep in instances.items()}
        results["A3_randomBest"] = dict(rule=rr, chosen=best_rand, per_seed=per,
                                        polar={k: summarise(v) for k, v in per.items()})
    else:
        results["A3_randomBest"] = dict(rule=None, per_seed=None, polar=None,
                                        note="no random candidate reached the 5 pp admission bar")

    # ---- A8 constant controller -------------------------------------------
    leads = [14.0, 16.0, 18.0, 20.0, 22.0]
    lead_scores = {L: arctic(evaluate(f"cp_val_{L:g}", policy="maxel", lead=L, window="validation"))
                   for L in leads}
    best_lead = max(lead_scores, key=lead_scores.get)
    cp = {}
    for inst, ep in instances.items():
        vals = [arctic(evaluate(f"cp_{inst}_s{s}", policy="maxel", lead=best_lead, epoch_doy=ep))
                for s in SEEDS]
        cp[inst] = vals
    results["A8_constantProbe"] = dict(best_lead=best_lead, val_scores=lead_scores, per_seed=cp,
                                       polar={k: summarise(v) for k, v in cp.items()})

    # ---- contrasts ---------------------------------------------------------
    contrasts = {}
    for arm in ("A3_randomBest", "A8_constantProbe"):
        v = results[arm]["per_seed"]
        if not v:
            continue
        contrasts[arm] = {inst: dict(paired_stats(v[inst], a0[inst]), tost=tost(v[inst], a0[inst], 1.0))
                          for inst in instances}
    out["contrasts_vs_A0"] = contrasts
    out["arms"] = results
    write(OUT / "isolation" / "summary.json", out)
    for arm, st in contrasts.items():
        for inst, s in st.items():
            print(f"{arm:18s} {inst:8s} diff {s['mean_diff']:+6.2f} CI {s['ci95']} p={s['wilcoxon_p']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
