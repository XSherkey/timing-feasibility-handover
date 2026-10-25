"""G2b + G4b: does reward-baked knowledge track physics, and what does picking the
wrong plateau point cost?

G2b  evaluate the lambda=8 penalty policies under the +2 s physics.  The knowledge is
     baked into the weights at 16 s, so the prediction is that it degrades like the
     LLM's 16 s rule and unlike the probe-calibrated shield.

G4b  the probe threshold lives on a plateau (14-16 s nominal, 16-18 s perturbed), so
     choosing a neighbouring point costs something.  Measure the cost of each plateau
     point on both physics, per seed.
"""
from __future__ import annotations

import json
import statistics as st
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PY = sys.executable
LOG = ROOT / "results" / "routeA" / "commands.log"
OUT = ROOT / "results" / "routeA_g4"
OUT_2B = ROOT / "results" / "routeA_g2"
W = ["--w-rel", "0.7", "--w-lat", "0.1", "--w-pow", "0.2"]


def run(cmd: list[str]) -> None:
    try:
        with LOG.open("a", encoding="utf-8") as fh:
            fh.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] [G2b/G4b] {' '.join(cmd)}\n")
    except OSError:
        pass
    r = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    if r.returncode != 0:
        raise SystemExit(f"failed: {' '.join(cmd)}\n{r.stdout[-1500:]}\n{r.stderr[-1500:]}")


def g2b() -> None:
    rows = []
    for seed in range(10):
        run_dir = ROOT / "results" / "routeA_f3" / "lam8.0" / f"no_forensics_seed{seed}"
        if not run_dir.exists():
            continue
        rec = {"seed": seed}
        for tag, acq in (("nominal", None), ("sig32", 3.2)):
            p = OUT_2B / f"g2b_lam8_s{seed}_{tag}.json"
            cmd = [PY, "scripts/eval_shield.py", "--run", str(run_dir), "--seed", str(seed), *W,
                   "--label", f"g2b/lam8/s{seed}/{tag}", "--out", str(p)]
            if acq:
                cmd += ["--acq-signaling", str(acq)]
            run(cmd)
            rec[tag] = 100 * json.load(open(p, encoding="utf-8"))[-1]["arctic"][0]
        rows.append(rec)
        print(f"G2b seed{seed}: nominal {rec['nominal']:5.1f}  sig32 {rec['sig32']:5.1f}  "
              f"drop {rec['sig32'] - rec['nominal']:+5.1f}", flush=True)
    OUT_2B.mkdir(parents=True, exist_ok=True)
    (ROOT / "results" / "routeA" / "g2b_penalty_drift.json").write_text(
        json.dumps(rows, indent=2), encoding="utf-8")
    if rows:
        print(f"G2b mean: nominal {st.mean(r['nominal'] for r in rows):.1f}  "
              f"sig32 {st.mean(r['sig32'] for r in rows):.1f}  "
              f"drop {st.mean(r['sig32'] - r['nominal'] for r in rows):+.1f}")


def g4b() -> None:
    rows = []
    for seed in range(5):
        rec = {"seed": seed}
        for tag, acq, leads in (("ref", None, (14, 16, 18)), ("sig32", 3.2, (16, 18, 20))):
            for lead in leads:
                p = OUT / f"g4b_s{seed}_{tag}_tau{lead}.json"
                cmd = [PY, "scripts/eval_shield.py", "--policy", "maxel", "--lead", str(lead),
                       "--seed", str(seed), *W, "--label", f"g4b/s{seed}/{tag}/tau{lead}",
                       "--out", str(p)]
                if acq:
                    cmd += ["--acq-signaling", str(acq)]
                run(cmd)
                rec[f"{tag}_tau{lead}"] = 100 * json.load(open(p, encoding="utf-8"))[-1]["arctic"][0]
        rows.append(rec)
        print(f"G4b seed{seed}: ref 14/16/18 = {rec['ref_tau14']:.1f}/{rec['ref_tau16']:.1f}/{rec['ref_tau18']:.1f} | "
              f"sig32 16/18/20 = {rec['sig32_tau16']:.1f}/{rec['sig32_tau18']:.1f}/{rec['sig32_tau20']:.1f}", flush=True)
    OUT.mkdir(parents=True, exist_ok=True)
    (ROOT / "results" / "routeA" / "g4b_plateau_cost.json").write_text(
        json.dumps(rows, indent=2), encoding="utf-8")
    if rows:
        for tag, off in (("ref", (14, 16, 18)), ("sig32", (16, 18, 20))):
            ms = [st.mean(r[f"{tag}_tau{o}"] for r in rows) for o in off]
            print(f"G4b {tag}: " + "  ".join(f"tau{o}={m:.1f}" for o, m in zip(off, ms)))


def main() -> int:
    g2b()
    g4b()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
