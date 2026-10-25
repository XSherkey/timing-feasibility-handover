"""G3: multi-seed drift sweep around the constant's failure boundary.

F1b found the crossover at +2..+3.2 s on a single seed.  This repeats it on several
seeds with the probe at ``--episodes 8`` (F4 showed 2 episodes is too noisy), so the
claim "the constant has a ~2 s margin, the calibrated threshold tracks the physics"
rests on a curve rather than one point.
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
OUT = ROOT / "results" / "routeA_g3"
W = ["--w-rel", "0.7", "--w-lat", "0.1", "--w-pow", "0.2"]
DRIFTS = [1.2, 3.2, 4.4, 5.6]
LEADS = [18, 20, 22, 24]


def run(cmd: list[str]) -> str:
    try:
        with LOG.open("a", encoding="utf-8") as fh:
            fh.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] [G3] {' '.join(cmd)}\n")
    except OSError:
        pass
    r = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    if r.returncode != 0:
        raise SystemExit(f"failed: {' '.join(cmd)}\n{r.stdout[-1500:]}\n{r.stderr[-1500:]}")
    return r.stdout


def main() -> int:
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", default="0,1,2")
    ap.add_argument("--out-dir", default="routeA_g3")
    ap.add_argument("--table", default="g3_drift_table.json")
    args = ap.parse_args()
    seeds = [int(s) for s in args.seeds.split(",") if s.strip()]
    out = ROOT / "results" / args.out_dir
    out.mkdir(parents=True, exist_ok=True)
    table = []
    for seed in seeds:
        for acq in DRIFTS:
            pp = out / f"probe_s{seed}_acq{acq}.json"
            run([PY, "scripts/probe_feasibility.py",
                 "--run", f"results/campaign_1023/almond_seed{seed}",
                 "--regime", "polar", "--episodes", "8", "--acq-signaling", str(acq),
                 "--seed", str(seed), "--out", str(pp)])
            tau = float(json.load(open(pp, encoding="utf-8"))["tau_star"])
            hsr = {}
            for lead in LEADS:
                ep = out / f"eval_s{seed}_acq{acq}_lead{lead}.json"
                run([PY, "scripts/eval_shield.py", "--policy", "maxel", "--lead", str(lead),
                     "--acq-signaling", str(acq), "--seed", str(seed), *W,
                     "--label", f"g3/s{seed}/acq{acq}/lead{lead}", "--out", str(ep)])
                hsr[lead] = 100 * json.load(open(ep, encoding="utf-8"))[-1]["arctic"][0]
            rec = dict(seed=seed, acq=acq, drift=round(acq - 1.2, 1), tau_star=tau,
                       fixed18=hsr[18], calib=hsr[min(LEADS, key=lambda L: abs(L - tau))],
                       calib_lead=int(min(LEADS, key=lambda L: abs(L - tau))), by_lead=hsr)
            table.append(rec)
            print(f"seed{seed} drift+{rec['drift']:.1f}s tau*={tau:4.1f} "
                  f"fixed18={rec['fixed18']:5.1f} calib={rec['calib']:5.1f} "
                  f"best={max(hsr.values()):5.1f}", flush=True)

    (ROOT / "results" / "routeA" / args.table).write_text(
        json.dumps(table, indent=2), encoding="utf-8")
    print("\n--- means over seeds ---")
    for acq in DRIFTS:
        rows = [r for r in table if r["acq"] == acq]
        f = [r["fixed18"] for r in rows]
        c = [r["calib"] for r in rows]
        print(f"drift +{acq - 1.2:4.1f}s  fixed18 {st.mean(f):5.1f} (sd {st.stdev(f):4.1f})  "
              f"calib {st.mean(c):5.1f} (sd {st.stdev(c):4.1f})  n={len(rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
