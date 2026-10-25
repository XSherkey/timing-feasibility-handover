"""R2 / E3: per-attempt oracle shield.

The oracle clamps the polar lead to the acquisition requirement this particular
handover actually needs.  It is an upper reference for any policy-independent
threshold: if the fixed 18 s shield sits well below it, the residual loss is the
price of not knowing T_z per attempt; if the two are close, the ceiling is set by
targeting/window selection rather than by the threshold.

Outputs oracle_factorial_seed*.json (10 seeds, nominal physics) and
oracle_ladder.json (4 drift levels x 5 seeds x 6 arms).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from _r2_run import PY, run_many, read_one  # noqa: E402

OUT = ROOT / "results" / "routeA_r2"
SEEDS10 = list(range(10))
SEEDS5 = list(range(5))
DRIFTS = {"d0": 1.2, "d2": 3.2, "d32": 4.4, "d44": 5.6}
RULE16 = "min_advance:16@latitude_abs_deg>=68"
RULE18 = "min_advance:18@latitude_abs_deg>=68"


def main() -> int:
    mode = sys.argv[1] if len(sys.argv) > 1 else "all"
    OUT.mkdir(parents=True, exist_ok=True)

    if mode in ("all", "smoke"):
        s = SEEDS10[0]
        cmds = [[PY, "scripts/eval_shield.py", "--run", f"results/campaign_1023/almond_fixedarch_seed{s}",
                 "--oracle-shield", "--out", str(OUT / f"_smoke_oracle_seed{s}.json")],
                [PY, "scripts/eval_shield.py", "--run", f"results/campaign_1023/almond_fixedarch_seed{s}",
                 "--rule", RULE16, "--out", str(OUT / f"_smoke_rule16_seed{s}.json")]]
        run_many(cmds, workers=2)
        o = read_one(OUT / f"_smoke_oracle_seed{s}.json")
        r = read_one(OUT / f"_smoke_rule16_seed{s}.json")
        print("smoke oracle: arctic %.2f late %.4f" % (100 * o["arctic"][0], o["polar_causes"].get("late_handover", -1)))
        print("smoke rule16: arctic %.2f late %.4f" % (100 * r["arctic"][0], r["polar_causes"].get("late_handover", -1)))
        if mode == "smoke":
            return 0

    # --- factorial oracle, nominal physics, 10 seeds -------------------------
    cmds = [[PY, "scripts/eval_shield.py", "--run", f"results/campaign_1023/almond_fixedarch_seed{s}",
             "--oracle-shield", "--out", str(OUT / f"oracle_factorial_seed{s}.json")] for s in SEEDS10]
    run_many(cmds, workers=6)
    per = {}
    for s in SEEDS10:
        p = OUT / f"oracle_factorial_seed{s}.json"
        if p.exists():
            rec = read_one(p)
            per[s] = dict(arctic=100 * rec["arctic"][0],
                          late=rec["polar_causes"].get("late_handover") or 0.0,
                          window=rec["polar_causes"].get("window_exceeded") or 0.0,
                          no_route=rec["polar_causes"].get("no_route") or 0.0)
    vals = [v["arctic"] for v in per.values()]
    fac = dict(per_seed={str(k): v for k, v in per.items()},
               mean=round(sum(vals) / len(vals), 2) if vals else None,
               sd=round((sum((x - sum(vals) / len(vals)) ** 2 for x in vals) / (len(vals) - 1)) ** 0.5, 2) if len(vals) > 1 else None,
               late_mean=round(sum(v["late"] for v in per.values()) / max(len(per), 1), 4) if per else None)
    json.dump(fac, open(OUT / "oracle_factorial.json", "w", encoding="utf-8"), indent=2)
    print("oracle factorial:", fac["mean"], "sd", fac["sd"], "late", fac["late_mean"])

    # --- drift ladder --------------------------------------------------------
    (OUT / "ladder").mkdir(parents=True, exist_ok=True)
    ladder = {}
    cmds, index = [], []
    for dname, acq in DRIFTS.items():
        for s in SEEDS5:
            base = ["--acq-signaling", str(acq)]
            arms = {
                "oracle": ["--run", f"results/campaign_1023/almond_fixedarch_seed{s}", "--oracle-shield"],
                "mined16": ["--run", f"results/campaign_1023/almond_fixedarch_seed{s}", "--rule", RULE16],
                "tau18": ["--run", f"results/campaign_1023/almond_fixedarch_seed{s}", "--rule", RULE18],
                "constant18": ["--policy", "maxel", "--lead", "18"],
                "no_knowledge": ["--run", f"results/campaign_1023/almond_fixedarch_seed{s}"],
                "lam8": ["--run", f"results/routeA_f3/lam8.0/no_forensics_seed{s}"],
            }
            for arm, args in arms.items():
                out = OUT / "ladder" / f"{dname}_{arm}_s{s}.json"
                cmds.append([PY, "scripts/eval_shield.py", *args, *base, "--out", str(out)])
                index.append((dname, arm, s, out))
    run_many(cmds, workers=6)

    for dname, arm, s, path in index:
        if not path.exists():
            continue
        rec = read_one(path)
        ladder.setdefault(dname, {}).setdefault(arm, []).append(
            dict(seed=s, arctic=100 * rec["arctic"][0],
                 late=rec["polar_causes"].get("late_handover") or 0.0))
    out_ladder = {}
    for dname, arms in ladder.items():
        out_ladder[dname] = {arm: dict(n=len(v),
                                       mean=round(sum(x["arctic"] for x in v) / len(v), 2),
                                       sd=round((sum((x["arctic"] - sum(y["arctic"] for y in v) / len(v)) ** 2 for x in v) / (len(v) - 1)) ** 0.5, 2) if len(v) > 1 else 0.0,
                                       late=round(sum(x["late"] for x in v) / len(v), 4),
                                       per_seed=[round(x["arctic"], 2) for x in v])
                          for arm, v in arms.items()}
    json.dump(out_ladder, open(OUT / "oracle_ladder.json", "w", encoding="utf-8"), indent=2)
    for dname, arms in out_ladder.items():
        print(dname, {a: v["mean"] for a, v in arms.items()})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
