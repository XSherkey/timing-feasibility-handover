"""H1: is the penalty's brittleness explained by a collapsed advance distribution?

Loads the lambda=8 checkpoints (knowledge baked into the weights) and the no-knowledge
checkpoints, rolls each out under both physics with no shield, and records the polar
handover-advance distribution plus the reliability.  The hypothesis is that the penalty
pushes the distribution onto the threshold (16 s), removing the spread that gives the
unconstrained policy its margin under drift.
"""
from __future__ import annotations

import json
import statistics as st
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
PY = sys.executable
LOG = ROOT / "results" / "routeA" / "commands.log"
OUT = ROOT / "results" / "routeA_h1"
W = ["--w-rel", "0.7", "--w-lat", "0.1", "--w-pow", "0.2"]
BUCKETS = (6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26)
ARMS = {
    "penalty_lam8": "results/routeA_f3/lam8.0/no_forensics_seed{s}",
    "no_knowledge": "results/campaign_1023/no_forensics_seed{s}",
}
PHYSICS = {"ref": None, "sig32": 3.2}


def run(cmd: list[str]) -> None:
    try:
        with LOG.open("a", encoding="utf-8") as fh:
            fh.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] [H1] {' '.join(cmd)}\n")
    except OSError:
        pass
    r = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    if r.returncode != 0:
        raise SystemExit(f"failed: {' '.join(cmd)}\n{r.stdout[-1500:]}\n{r.stderr[-1500:]}")


def hist(adv: list[float]) -> dict:
    a = np.asarray(adv, dtype=float)
    return {str(b): float(np.mean(np.isclose(a, b))) for b in BUCKETS}


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    rows = []
    for arm, pattern in ARMS.items():
        for seed in range(10):
            run_dir = ROOT / pattern.format(s=seed)
            if not run_dir.exists():
                continue
            rec = {"arm": arm, "seed": seed}
            for phys, acq in PHYSICS.items():
                dist = OUT / f"dist_{arm}_s{seed}_{phys}.json"
                ev = OUT / f"eval_{arm}_s{seed}_{phys}.json"
                cmd = [PY, "scripts/eval_shield.py", "--run", str(run_dir), "--seed", str(seed), *W,
                       "--label", f"h1/{arm}/s{seed}/{phys}",
                       "--dump-advance-dist", str(dist), "--out", str(ev)]
                if acq:
                    cmd += ["--acq-signaling", str(acq)]
                run(cmd)
                d = json.load(open(dist, encoding="utf-8"))
                adv = d["advances"]
                e = json.load(open(ev, encoding="utf-8"))[-1]
                rec[phys] = dict(
                    n=len(adv),
                    mean=round(float(np.mean(adv)), 2) if adv else None,
                    sd=round(float(np.std(adv)), 2) if adv else None,
                    share_below16=round(float(np.mean(np.asarray(adv) < 16)), 3) if adv else None,
                    share_below18=round(float(np.mean(np.asarray(adv) < 18)), 3) if adv else None,
                    hist=hist(adv) if adv else {},
                    arctic=round(100 * e["arctic"][0], 1),
                )
            rows.append(rec)
            print(f"{arm:<14} s{seed:<2} ref {rec['ref']['mean']:5.2f}s sd {rec['ref']['sd']:4.2f} "
                  f"<16 {100 * rec['ref']['share_below16']:4.0f}%  HSR {rec['ref']['arctic']:5.1f} | "
                  f"sig32 HSR {rec['sig32']['arctic']:5.1f}", flush=True)

    (ROOT / "results" / "routeA" / "h1_advance_dist.json").write_text(
        json.dumps(rows, indent=2), encoding="utf-8")

    print("\n--- means over seeds ---")
    for arm in ARMS:
        sel = [r for r in rows if r["arm"] == arm]
        if not sel:
            continue
        print(f"{arm:<14} ref: mean {st.mean(r['ref']['mean'] for r in sel):.2f}s  "
              f"sd {st.mean(r['ref']['sd'] for r in sel):.2f}  "
              f"<16 {100 * st.mean(r['ref']['share_below16'] for r in sel):.0f}%  "
              f"HSR {st.mean(r['ref']['arctic'] for r in sel):.1f}  |  "
              f"sig32: mean {st.mean(r['sig32']['mean'] for r in sel):.2f}s  "
              f"HSR {st.mean(r['sig32']['arctic'] for r in sel):.1f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
