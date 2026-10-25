"""T2-03 - cross-intent transfer at n = 10 (shared graph vs fresh graph per intent).

Reads results/multi_{shared,fresh}_s{0..9}/summary.json, pairs the two arms on the policy seed,
and reports per-intent polar HSR with the exact Wilcoxon test, the bootstrap CI of the mean
difference and Cohen's d_z.  Seeds whose intent-0 mining did not commit a rule are reported
separately, because "shared" and "fresh" are identical there by construction.

Run:  python experiments/analyse_cross_intent.py
Out:  results/routeA_r3/cross_intent/summary.json
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from r3lib import OUT, ROOT, holm, paired_stats, summarise, tost, write

INTENTS = ["reliability_first", "latency_first", "power_first", "balanced"]


def load(mode: str, seed: int) -> list[dict] | None:
    p = ROOT / "results" / f"multi_{mode}_s{seed}" / "summary.json"
    if not p.exists():
        return None
    return json.loads(p.read_text(encoding="utf-8"))


def main() -> int:
    rows = {"shared": {}, "fresh": {}}
    for mode in ("shared", "fresh"):
        for s in range(10):
            d = load(mode, s)
            if d is None:
                print("missing", mode, s)
                continue
            rows[mode][s] = d

    seeds = sorted(set(rows["shared"]) & set(rows["fresh"]))
    out = {"seeds": seeds, "per_intent": {}, "committed": {}, "contrasts": {}}
    # which seeds committed a rule at intent 0 (kg_active=1)?
    committed = [s for s in seeds if rows["shared"][s][0].get("kg_active") == 1]
    out["committed"] = dict(seeds=committed, n=len(committed),
                            note="intent-0 mining committed a rule; on the other seeds the shared "
                                 "and fresh arms are identical by construction")

    for k, intent in enumerate(INTENTS):
        sh = [100 * rows["shared"][s][k]["arctic"] for s in seeds]
        fr = [100 * rows["fresh"][s][k]["arctic"] for s in seeds]
        cell = dict(intent=intent, shared=summarise(sh), fresh=summarise(fr),
                    pair=paired_stats(sh, fr), tost=tost(sh, fr, 1.0))
        if k > 0 and committed:
            sh_c = [100 * rows["shared"][s][k]["arctic"] for s in committed]
            fr_c = [100 * rows["fresh"][s][k]["arctic"] for s in committed]
            cell["restricted_to_committed"] = dict(
                n=len(committed), shared=summarise(sh_c), fresh=summarise(fr_c),
                pair=paired_stats(sh_c, fr_c))
        out["per_intent"][intent] = cell

    ps = {k: v["pair"]["wilcoxon_p"] for k, v in out["per_intent"].items() if v["pair"]["wilcoxon_p"]}
    out["holm"] = holm(ps)
    write(OUT / "cross_intent" / "summary.json", out)
    for intent, c in out["per_intent"].items():
        print("%-18s shared %6.2f  fresh %6.2f  diff %+6.2f  p=%s  CI %s"
              % (intent, c["shared"]["mean"], c["fresh"]["mean"], c["pair"]["mean_diff"],
                 ("%.4f" % c["pair"]["wilcoxon_p"]) if c["pair"]["wilcoxon_p"] else "None",
                 [round(x, 2) for x in c["pair"]["ci95"]]))
    print("committed seeds:", committed)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
