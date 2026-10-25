"""R2 / E1b: exact identity proof on the archived arm.

The archived appendix factorial was produced on the `almond_seed*` checkpoints, so
the identity proof has to use those, not `almond_fixedarch`.  We re-run tau=16 and
tau=20 there and compare every seed against results/verify_1023/factorial.json.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from _r2_run import PY, run_many, read_one  # noqa: E402

OUT = ROOT / "results" / "routeA_r2"
SEEDS = list(range(10))
ARMS = {"tau16": 16, "tau20": 20}


def main() -> int:
    cmds = []
    for arm, tau in ARMS.items():
        for s in SEEDS:
            cmds.append([PY, "scripts/eval_shield.py",
                         "--run", f"results/campaign_1023/almond_seed{s}",
                         "--rule", f"min_advance:{tau}@latitude_abs_deg>=68",
                         "--out", str(OUT / f"identity_{arm}_seed{s}.json")])
    run_many(cmds, workers=6)

    old = json.load(open(ROOT / "results" / "verify_1023" / "factorial.json", encoding="utf-8"))
    arch = {}
    for r in old:
        if r["label"].startswith("almond_"):
            seed = int(r["label"].split("_s")[1].split("/")[0])
            cond = r["label"].split("/")[1]
            arch[(seed, cond)] = 100 * r["arctic"][0]

    check = {}
    for arm in ARMS:
        diffs = []
        per = {}
        for s in SEEDS:
            p = OUT / f"identity_{arm}_seed{s}.json"
            if not p.exists():
                continue
            new = 100 * read_one(p)["arctic"][0]
            per[s] = dict(new=new, archived=arch.get((s, arm)))
            diffs.append(abs(new - arch.get((s, arm), float("nan"))))
        check[arm] = dict(per_seed=per, max_abs_diff=round(max(diffs), 6) if diffs else None,
                          bit_identical=all(d < 1e-9 for d in diffs))
    json.dump(check, open(OUT / "factorial_identity_almond.json", "w", encoding="utf-8"), indent=2)
    for arm, c in check.items():
        print(f"{arm}: max |new - archived| = {c['max_abs_diff']}  bit-identical={c['bit_identical']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
