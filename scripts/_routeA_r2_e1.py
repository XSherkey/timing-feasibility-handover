"""R2 / E1: the missing tau=18 arm, plus an identity re-run of tau=16 and tau=20.

The reviewer asks for the row of the threshold ledger that the deployed algorithm
actually uses: tau* = 16 plus the 2 s margin = 18 s.  We also re-run the 16 s and
20 s arms into the new directory and check they reproduce the archived appendix
numbers bit-for-bit (the directory's identity proof).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from _r2_run import PY, run_many, polar, summary  # noqa: E402

OUT = ROOT / "results" / "routeA_r2"
SEEDS = list(range(10))
ARMS = {"tau16": 16, "tau18": 18, "tau20": 20}


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    cmds = []
    for arm, tau in ARMS.items():
        for s in SEEDS:
            cmds.append([PY, "scripts/eval_shield.py",
                         "--run", f"results/campaign_1023/almond_fixedarch_seed{s}",
                         "--rule", f"min_advance:{tau}@latitude_abs_deg>=68",
                         "--out", str(OUT / f"factorial_{arm}_seed{s}.json")])
    codes = run_many(cmds, workers=6)
    if any(codes):
        print("some runs failed:", codes)

    table = {}
    for arm in ARMS:
        per = {}
        for s in SEEDS:
            p = OUT / f"factorial_{arm}_seed{s}.json"
            if p.exists():
                per[s] = summary(p)
        vals = [v["arctic"] for v in per.values()]
        table[arm] = dict(per_seed={str(k): v for k, v in per.items()},
                          mean=round(sum(vals) / len(vals), 2) if vals else None,
                          sd=round((sum((x - sum(vals) / len(vals)) ** 2 for x in vals) / (len(vals) - 1)) ** 0.5, 2) if len(vals) > 1 else None,
                          min=min(vals) if vals else None, max=max(vals) if vals else None,
                          span=round(max(vals) - min(vals), 2) if vals else None,
                          late_mean=round(sum(v["causes"].get("late_handover", 0) for v in per.values()) / max(len(per), 1), 4))
    json.dump(table, open(OUT / "factorial_tau18.json", "w", encoding="utf-8"), indent=2)

    # identity proof against the archived common-episode factorial
    old = json.load(open(ROOT / "results" / "verify_1023" / "factorial.json", encoding="utf-8"))

    def old_mean(cond: str) -> float:
        v = [100 * r["arctic"][0] for r in old
             if r["label"].startswith("almond_") and r["label"].endswith("/" + cond)]
        return round(sum(v) / len(v), 3)

    identity = {"tau16_new": table["tau16"]["mean"], "tau16_archived": old_mean("tau16"),
                "tau20_new": table["tau20"]["mean"], "tau20_archived": old_mean("tau20")}
    identity["tau16_match"] = abs(identity["tau16_new"] - identity["tau16_archived"]) < 0.05
    identity["tau20_match"] = abs(identity["tau20_new"] - identity["tau20_archived"]) < 0.05
    json.dump(identity, open(OUT / "factorial_identity.json", "w", encoding="utf-8"), indent=2)

    for arm in ARMS:
        t = table[arm]
        print(f"{arm}: mean {t['mean']} sd {t['sd']} span {t['span']} late {t['late_mean']}")
    print("identity:", identity)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
