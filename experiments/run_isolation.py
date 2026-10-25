"""T2-01 — contribution isolation factorial (A0-A8).

Every arm is evaluated with the *same* shield semantics and the *same* 2 s margin; the arms
differ only in where the predicate and the magnitude come from, and in whether the audit gate
and the knowledge graph are in the loop.  All selection (predicate source, Threshold, lead)
happens on the **validation window**; the test window and the three lockbox epochs are only
ever scored.

Run:  python experiments/run_isolation.py
Out:  results/routeA_r3/isolation/summary.json
"""
from __future__ import annotations

import itertools
import random
from pathlib import Path

import numpy as np

from r3lib import (LOCKBOX_EPOCHS, OUT, SEEDS, evaluate, arctic, late_share,
                   paired_stats, summarise, tost, write)

import os

QUICK = bool(os.environ.get("R3_QUICK"))
SEL_SEEDS = [0] if QUICK else [0, 1, 2]     # seeds used ONLY to rank candidates on validation

ALMOND = {s: f"results/campaign_1023/almond_seed{s}" for s in (SEEDS[:2] if QUICK else SEEDS)}
PPO = {s: f"results/campaign_1023/ppomlp_seed{s}" for s in (SEEDS[:2] if QUICK else SEEDS)}
if QUICK:
    SEEDS = SEEDS[:2]
MARGIN = 2.0
MAG = 16.0                     # magnitude proposed by the LLM / the human
DEPLOYED = MAG + MARGIN        # tau_used


def rule(mag: float, atoms: str) -> str:
    return f"min_advance:{mag:g}@{atoms}" if atoms else f"min_advance:{mag:g}"


# ---------------------------------------------------------------- candidates
HUMAN = {
    "HP1": rule(DEPLOYED, "latitude_abs_deg>=68"),
    "HP2": rule(DEPLOYED, "latitude_abs_deg>=70"),
    "HP3": rule(DEPLOYED, "latitude_abs_deg>=68,elevation_deg>=15"),
}
GRID = {f"lat>={t:g}": rule(DEPLOYED, f"latitude_abs_deg>={t:g}") for t in range(60, 74, 2)}

RNG = random.Random(20261024)
FIELDS = ["latitude_abs_deg", "elevation_deg", "remaining_visibility_s", "isl_hop_count"]
OPS = [">=", "<="]
RANDOM: dict[str, str] = {}
while len(RANDOM) < (6 if QUICK else 20):
    eff_mag = RNG.choice([6, 8, 10, 12, 14, 16, 18, 20, 22])
    n_atoms = RNG.choice([1, 1, 2])
    atoms = []
    for f in RNG.sample(FIELDS, n_atoms):
        v = {"latitude_abs_deg": RNG.choice([55, 60, 65, 68, 70, 72]),
             "elevation_deg": RNG.choice([10, 15, 20, 30]),
             "remaining_visibility_s": RNG.choice([60, 120, 240]),
             "isl_hop_count": RNG.choice([0, 1, 2])}[f]
        atoms.append(f"{f}{RNG.choice(OPS)}{v:g}")
    name = f"R{len(RANDOM)+1:02d}"
    RANDOM[name] = rule(eff_mag, ",".join(atoms))


def eval_many(label: str, runs: dict[int, str], rule_s: str, seeds: list[int],
              instances: dict[str, float | None]) -> dict[str, list[float]]:
    out: dict[str, list[float]] = {}
    for inst, epoch in instances.items():
        vals = []
        for s in seeds:
            r = evaluate(f"{label}_{inst}_s{s}", run=runs[s], rule=rule_s, epoch_doy=epoch)
            vals.append(arctic(r))
        out[inst] = vals
    return out


def rank_on_validation(cands: dict[str, str], runs: dict[int, str], tag: str) -> tuple[str, dict]:
    """Score every candidate on the validation window and return the argmax rule."""
    scores = {}
    for name, r in cands.items():
        vals = [arctic(evaluate(f"sel_{tag}_{name}_s{s}", run=runs[s], rule=r, window="validation",
                                 epoch_doy=None)) for s in SEL_SEEDS]
        scores[name] = dict(mean=float(np.mean(vals)), per_seed=vals)
    best = max(scores, key=lambda k: scores[k]["mean"])
    return best, scores


def gate_admit(cands: dict[str, str], runs: dict[int, str], tag: str, thresh: float = 5.0):
    """Validation replay of every candidate against the unshielded reference (5 pp rule)."""
    base = {s: arctic(evaluate(f"gatebase_{tag}_s{s}", run=runs[s], window="validation"))
            for s in SEL_SEEDS}
    rows, admitted = {}, []
    for name, r in cands.items():
        delta = []
        for s in SEL_SEEDS:
            v = arctic(evaluate(f"gate_{tag}_{name}_s{s}", run=runs[s], rule=r, window="validation"))
            delta.append(v - base[s])
        d = float(np.mean(delta))
        rows[name] = dict(rule=r, val_delta=d, admitted=bool(d >= thresh))
        if d >= thresh:
            admitted.append(name)
    return rows, admitted, base


def constant_probe(tag: str, instances: dict[str, float | None]) -> dict:
    """A8: highest-elevation controller + lead grid-searched on validation (re-probed per regime)."""
    leads = [14.0, 16.0, 18.0, 20.0, 22.0]
    scores = {L: arctic(evaluate(f"cp_val_{L:g}", policy="maxel", lead=L, window="validation")) for L in leads}
    best_lead = max(scores, key=scores.get)
    out = dict(best_lead=best_lead, val_scores={str(k): v for k, v in scores.items()}, instances={})
    for inst, epoch in instances.items():
        vals = [arctic(evaluate(f"cp_{inst}_s{s}", policy="maxel", lead=best_lead, epoch_doy=epoch))
                for s in SEEDS]
        out["instances"][inst] = dict(polar=vals, summary=summarise(vals))
    return out


def main() -> int:
    instances = {"eval": None}
    for e in (LOCKBOX_EPOCHS[:1] if QUICK else LOCKBOX_EPOCHS):
        instances[f"lb{e:g}"] = e

    summary: dict = {"instances": instances, "margin_s": MARGIN, "magnitude_s": MAG,
                     "deployed_threshold_s": DEPLOYED, "selections": {}}

    # --- predicate-source arms -------------------------------------------------
    best_hp, hp_scores = rank_on_validation(HUMAN, ALMOND, "hp")
    best_grid, grid_scores = rank_on_validation(GRID, ALMOND, "grid")
    rand_rows, rand_admitted, rand_base = gate_admit(RANDOM, ALMOND, "rand")
    summary["selections"].update(human=dict(best=best_hp, scores=hp_scores),
                                 grid=dict(best=best_grid, scores=grid_scores),
                                 random=dict(rows=rand_rows, admitted=rand_admitted))

    if rand_admitted:
        best_rand = max(rand_admitted, key=lambda k: rand_rows[k]["val_delta"])
        rand_best_rule = RANDOM[best_rand]
        rand_mean_rules = [RANDOM[k] for k in rand_admitted]
    else:
        best_rand, rand_best_rule, rand_mean_rules = None, None, []

    arms = {
        "A0_full": rule(DEPLOYED, "latitude_abs_deg>=68"),
        "A1_human": HUMAN[best_hp],
        "A2_grid": GRID[best_grid],
        "A4_noKM": rule(DEPLOYED, "latitude_abs_deg>=68"),
        "A5_noGate": rule(DEPLOYED, "latitude_abs_deg>=68"),
        "A7_probeOnly": HUMAN[best_hp],
    }
    if rand_best_rule:
        arms["A3_randomBest"] = rand_best_rule

    results = {}
    for arm, r in arms.items():
        res = eval_many(arm, ALMOND, r, SEEDS, instances)
        results[arm] = dict(rule=r, polar={k: summarise(v) for k, v in res.items()}, per_seed=res)
    # A3 mean over admitted random candidates
    if rand_mean_rules:
        mean_rows = {inst: [] for inst in instances}
        for r in rand_mean_rules:
            sub = eval_many("A3rand", ALMOND, r, SEL_SEEDS, instances)
            for inst in instances:
                mean_rows[inst].extend(sub[inst])
        results["A3_randomMean"] = dict(rules=rand_mean_rules,
                                        polar={k: summarise(v) for k, v in mean_rows.items()},
                                        per_seed=mean_rows)

    # --- A8 constant controller ------------------------------------------------
    results["A8_constantProbe"] = constant_probe("a8", instances)

    # --- paired contrasts vs A0 -------------------------------------------------
    contrasts = {}
    a0 = results["A0_full"]["per_seed"]
    for arm in results:
        if arm == "A0_full" or "per_seed" not in results[arm]:
            continue
        contrasts[arm] = {}
        for inst in instances:
            a = results[arm]["per_seed"].get(inst, [])
            b = a0.get(inst, [])
            n = min(len(a), len(b))
            st = paired_stats(a[:n], b[:n])
            st["tost"] = tost(a[:n], b[:n], margin=1.0)
            contrasts[arm][inst] = st
    summary["contrasts_vs_A0"] = contrasts
    summary["arms"] = results

    # --- decision rule (pre-registered in the review) ---------------------------
    dec = {}
    for arm in ("A7_probeOnly", "A1_human", "A2_grid", "A4_noKM", "A5_noGate"):
        if arm in contrasts:
            upper = max((contrasts[arm][i]["ci95"][1] or 0.0) for i in instances)
            dec[arm] = dict(max_ci_upper_pp=upper, equivalent=bool(upper < 1.0))
    summary["decision"] = dec
    write(OUT / "isolation" / "summary.json", summary)
    print("decision:", dec)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
