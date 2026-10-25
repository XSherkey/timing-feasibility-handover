"""F5: does the gap decomposition survive an alternative physics?

Two alternative twins (4 h caches already on disk):
  * ``noseam``  - the polar seam penalty is disabled
  * ``feeder3`` - three feeder slots per gateway instead of ten

For each: train almond / ppomlp / no_forensics on seeds 0-4, then evaluate every
frozen checkpoint with (a) no shield and (b) an 18 s shield above 68 deg.  The
acceptance is about direction, not exact values:
  1. before the shield, almond ~ ppomlp (policy-independence),
  2. the failure mix is still dominated by ``late_handover``,
  3. the shield lifts both to the same region ceiling.
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PY = sys.executable
LOG = ROOT / "results" / "routeA" / "commands.log"
OUT = ROOT / "results" / "routeA_f5"
W = ["--w-rel", "0.7", "--w-lat", "0.1", "--w-pow", "0.2"]
RULE = "min_advance:18@latitude_abs_deg>=68"


def run(cmd: list[str]) -> None:
    try:
        with LOG.open("a", encoding="utf-8") as fh:
            fh.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] [F5] {' '.join(cmd)}\n")
    except OSError:
        pass
    r = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    if r.returncode != 0:
        raise SystemExit(f"failed: {' '.join(cmd)}\n{r.stdout[-2000:]}\n{r.stderr[-2000:]}")


def physics_flags(cfg: str, for_eval: bool = False) -> list[str]:
    hours = ["--hours" if for_eval else "--twin-hours", "4"]
    if cfg == "noseam":
        return hours + ["--no-seam"]
    if cfg == "feeder3":
        return hours + ["--feeder-slots", "3"]
    return hours


def main() -> int:
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--configs", default="noseam,feeder3")
    ap.add_argument("--skip-train", action="store_true")
    args = ap.parse_args()

    OUT.mkdir(parents=True, exist_ok=True)
    results = {}
    for cfg in [c for c in args.configs.split(",") if c.strip()]:
        flags = physics_flags(cfg)
        if not args.skip_train:
            run([PY, "scripts/run_campaign.py", "--methods", "almond,ppomlp,no_forensics",
                 "--seeds", "0-4", "--episodes", "9600", "--eval-every", "1200",
                 "--device", "cpu", "--spec-file", "results/nas/llm_spec.json",
                 *flags, "--out", str(OUT / cfg)])
        results[cfg] = {}
        for method in ("almond", "ppomlp", "no_forensics"):
            results[cfg][method] = []
            for seed in range(5):
                run_dir = OUT / cfg / f"{method}_seed{seed}"
                rec = {"seed": seed}
                for tag, rule in (("none", None), ("shield18", RULE)):
                    path = OUT / cfg / f"eval_{method}_s{seed}_{tag}.json"
                    cmd = [PY, "scripts/eval_shield.py", "--run", str(run_dir), "--seed", str(seed),
                           *W, *physics_flags(cfg, for_eval=True),
                           "--label", f"{cfg}/{method}/s{seed}/{tag}", "--out", str(path)]
                    if rule:
                        cmd += ["--rule", rule]
                    run(cmd)
                    r = json.load(open(path, encoding="utf-8"))[-1]
                    rec[tag] = 100 * r["arctic"][0]
                    rec[tag + "_late"] = 100 * r["polar_causes"].get("late_handover", 0.0)
                results[cfg][method].append(rec)
                print(f"{cfg:<8}{method:<14}seed{seed}  none {rec['none']:5.1f}  "
                      f"shield18 {rec['shield18']:5.1f}  late {rec['none_late']:5.1f}%", flush=True)

    # merge with an earlier run so that processing one config does not erase another
    table_path = ROOT / "results" / "routeA" / "f5_table.json"
    merged = json.load(open(table_path, encoding="utf-8")) if table_path.exists() else {}
    merged.update(results)
    table_path.write_text(json.dumps(merged, indent=2), encoding="utf-8")
    print("\nwrote", table_path, "configs:", sorted(merged))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
