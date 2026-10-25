"""R2 / E2: the lockbox evaluation.

Protocol (fixed before any lockbox data is seen):
  * the mined rule (16 s, lat>=68), the gate decision and lambda=8 are frozen;
  * the only step redone is the probe, run on the *validation* window of the default
    twin -> tau* = 16 s for both representative seeds (0 and 4), so the deployed
    threshold is tau_used = min(16 + 2, 24) = 18 s.  This value is not revisited;
  * the lockbox instances shift the orbital phase (epoch_doy) so that no episode of
    the evaluation window overlaps the campaign window.

Arms x 10 policy seeds x 3 lockbox instances, plus a traffic-instance robustness
check on two extra evaluation seeds for the two headline arms.
"""
from __future__ import annotations

import json
import statistics as st
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from _r2_run import PY, run_many, read_one  # noqa: E402

OUT = ROOT / "results" / "routeA_r2"
LOCK = OUT / "lockbox"
EPOCHS = {"e299": 299.25, "e306": 306.25, "e290": 290.25}
SEEDS = list(range(10))
RULE16 = "min_advance:16@latitude_abs_deg>=68"
RULE18 = "min_advance:18@latitude_abs_deg>=68"
ARMS = {
    "full": ["--run", "results/campaign_1023/almond_fixedarch_seed{s}"],
    "full_m16": ["--run", "results/campaign_1023/almond_fixedarch_seed{s}", "--rule", RULE16],
    "full_t18": ["--run", "results/campaign_1023/almond_fixedarch_seed{s}", "--rule", RULE18],
    "const18": ["--policy", "maxel", "--lead", "18"],
    "ppomlp": ["--run", "results/campaign_1023/ppomlp_seed{s}"],
    "ppomlp_m16": ["--run", "results/campaign_1023/ppomlp_seed{s}", "--rule", RULE16],
    "lam8": ["--run", "results/routeA_f3/lam8.0/no_forensics_seed{s}"],
    "lam8_m16": ["--run", "results/routeA_f3/lam8.0/no_forensics_seed{s}", "--rule", RULE16],
}


def main() -> int:
    LOCK.mkdir(parents=True, exist_ok=True)
    cmds, index = [], []
    for ename, doy in EPOCHS.items():
        for arm, tmpl in ARMS.items():
            for s in SEEDS:
                args = [a.format(s=s) if "{s}" in a else a for a in tmpl]
                out = LOCK / f"{ename}_{arm}_s{s}.json"
                cmds.append([PY, "scripts/eval_shield.py", *args,
                             "--epoch-doy", str(doy), "--seed", str(s), "--out", str(out)])
                index.append((ename, arm, s, out))
    print(f"running {len(cmds)} lockbox evaluations", flush=True)
    codes = run_many(cmds, workers=6)
    print("failures:", sum(1 for c in codes if c), flush=True)

    table: dict[str, dict[str, list]] = {}
    for ename, arm, s, path in index:
        if not path.exists():
            continue
        rec = read_one(path)
        table.setdefault(ename, {}).setdefault(arm, []).append(
            dict(seed=s, arctic=100 * rec["arctic"][0],
                 late=rec["polar_causes"].get("late_handover") or 0.0,
                 win=rec["polar_causes"].get("window_exceeded") or 0.0,
                 route=rec["polar_causes"].get("no_route") or 0.0))

    summary = {}
    for ename, arms in table.items():
        summary[ename] = {}
        for arm, rows in arms.items():
            v = [r["arctic"] for r in rows]
            summary[ename][arm] = dict(n=len(v), mean=round(st.mean(v), 2),
                                       sd=round(st.stdev(v), 2) if len(v) > 1 else 0.0,
                                       min=round(min(v), 2), max=round(max(v), 2),
                                       late=round(st.mean(r["late"] for r in rows), 4),
                                       per_seed=[round(x, 2) for x in v])

    # traffic-instance robustness: two extra eval seeds on the two headline arms
    extra, extra_cmds, extra_index = {}, [], []
    for ename, doy in EPOCHS.items():
        for es in (100, 200):
            for arm in ("full_t18", "ppomlp_m16"):
                for s in range(5):
                    args = [a.format(s=s) if "{s}" in a else a
                            for a in ARMS[arm]]
                    out = LOCK / f"{ename}_{arm}_s{s}_eval{es}.json"
                    extra_cmds.append([PY, "scripts/eval_shield.py", *args,
                                       "--epoch-doy", str(doy), "--seed", str(es),
                                       "--out", str(out)])
                    extra_index.append((ename, arm, es, out))
    run_many(extra_cmds, workers=6)
    for ename, arm, es, path in extra_index:
        if path.exists():
            rec = read_one(path)
            extra.setdefault(ename, {}).setdefault(arm, {}).setdefault(str(es), []).append(
                100 * rec["arctic"][0])
    summary["traffic_robustness"] = {
        ename: {arm: {es: round(st.mean(v), 2) for es, v in d.items()}
                for arm, d in arms.items()}
        for ename, arms in extra.items()}

    json.dump(summary, open(OUT / "lockbox_summary.json", "w", encoding="utf-8"), indent=2)

    # ---- verdict -----------------------------------------------------------
    verdict_rows = []
    for ename in EPOCHS:
        a = summary.get(ename, {})
        if not a:
            continue
        ok_full = a["full_t18"]["mean"] >= a["ppomlp_m16"]["mean"] - 1.0
        ok_shield = a["full_t18"]["mean"] > a["full"]["mean"]
        ok_full_vs_pp = a["full_t18"]["mean"] > a["ppomlp"]["mean"]
        ok_lam = a["lam8"]["mean"] < a["full_t18"]["mean"]
        verdict_rows.append(dict(instance=ename, full_t18=a["full_t18"]["mean"],
                                 ppomlp_m16=a["ppomlp_m16"]["mean"],
                                 full=a["full"]["mean"], ppomlp=a["ppomlp"]["mean"],
                                 lam8=a["lam8"]["mean"],
                                 full_ge_ppomlp_minus1=ok_full, shield_beats_none=ok_shield,
                                 full_beats_ppomlp=ok_full_vs_pp, lam8_below_shield=ok_lam))
    passed = all(r["full_ge_ppomlp_minus1"] and r["shield_beats_none"] and
                 r["full_beats_ppomlp"] and r["lam8_below_shield"] for r in verdict_rows)
    json.dump(dict(rows=verdict_rows, passed=passed,
                   tau_used=18, calibration="validation window, tau*=16 for seeds 0 and 4"),
              open(OUT / "lockbox_verdict.json", "w", encoding="utf-8"), indent=2)

    lines = ["# Lockbox evaluation (R2 / E2)", "",
             f"Calibration: validation-window probe, tau* = 16 s (seeds 0, 4); "
             f"tau_used = min(16+2, 24) = **18 s**, frozen before any lockbox rollout.", "",
             f"Instances (epoch_doy): " + ", ".join(f"{k}={v}" for k, v in EPOCHS.items()),
             "", "| instance | arm | n | mean | sd | min | max |", "|---|---|---|---|---|---|---|"]
    for ename in EPOCHS:
        for arm, r in summary.get(ename, {}).items():
            lines.append(f"| {ename} | {arm} | {r['n']} | {r['mean']} | {r['sd']} | {r['min']} | {r['max']} |")
    lines += ["", "## Verdict", "",
              "| instance | full+t18 | ppomlp+m16 | full | ppomlp | lam8 | pass |",
              "|---|---|---|---|---|---|---|"]
    for r in verdict_rows:
        ok = r["full_ge_ppomlp_minus1"] and r["shield_beats_none"] and r["full_beats_ppomlp"] and r["lam8_below_shield"]
        lines.append(f"| {r['instance']} | {r['full_t18']} | {r['ppomlp_m16']} | {r['full']} | "
                     f"{r['ppomlp']} | {r['lam8']} | {'YES' if ok else 'NO'} |")
    lines += ["", f"**Overall: {'PASSED' if passed else 'FAILED'}**", ""]
    Path(OUT / "lockbox.md").write_text("\n".join(lines), encoding="utf-8")

    for r in verdict_rows:
        print(r)
    print("passed:", passed)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
