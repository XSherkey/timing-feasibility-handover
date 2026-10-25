"""H2: conservative calibration under asymmetric cost.

G4b showed under-protection costs ~5 pp per 2 s while over-protection is nearly free
until the 26 s cap.  So the probe threshold should be used with a safety margin:

    tau_used = min(tau_probed + m, 26 - 2)

This script (1) probes each (seed, physics) with 8 episodes per advance, then
(2) evaluates the frozen policy with tau_used for m in {0, 2, 4}.
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
OUT = ROOT / "results" / "routeA_h2"
W = ["--w-rel", "0.7", "--w-lat", "0.1", "--w-pow", "0.2"]
SEEDS = [0, 1, 2, 3, 4]
PHYSICS = {"ref": 1.2, "sig32": 3.2, "drift44": 4.4}
MARGINS = [0, 2, 4]
AMAX = 26.0


def run(cmd: list[str]) -> None:
    try:
        with LOG.open("a", encoding="utf-8") as fh:
            fh.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] [H2] {' '.join(cmd)}\n")
    except OSError:
        pass
    r = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    if r.returncode != 0:
        raise SystemExit(f"failed: {' '.join(cmd)}\n{r.stdout[-1500:]}\n{r.stderr[-1500:]}")


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    table = []
    for phys, acq in PHYSICS.items():
        for seed in SEEDS:
            pp = OUT / f"probe_s{seed}_{phys}.json"
            run([PY, "scripts/probe_feasibility.py", "--run", f"results/campaign_1023/almond_seed{seed}",
                 "--regime", "polar", "--episodes", "8", "--seed", str(seed),
                 "--acq-signaling", str(acq), "--out", str(pp)])
            tau = float(json.load(open(pp, encoding="utf-8"))["tau_star"])
            rec = {"physics": phys, "seed": seed, "tau_probed": tau,
                   "tau_used": {str(m): min(tau + m, AMAX - 2) for m in MARGINS}}
            for m in MARGINS:
                lead = int(min(tau + m, AMAX - 2))
                ep = OUT / f"eval_s{seed}_{phys}_m{m}.json"
                run([PY, "scripts/eval_shield.py", "--policy", "maxel", "--lead", str(lead),
                     "--acq-signaling", str(acq), "--seed", str(seed), *W,
                     "--label", f"h2/{phys}/s{seed}/m{m}/tau{lead}", "--out", str(ep)])
                rec[f"m{m}"] = round(100 * json.load(open(ep, encoding="utf-8"))[-1]["arctic"][0], 1)
            table.append(rec)
            print(f"{phys:<8} s{seed} tau*={tau:4.1f}  " +
                  "  ".join(f"m{m}={rec[f'm{m}']:5.1f}" for m in MARGINS), flush=True)

    (ROOT / "results" / "routeA" / "h2_margin.json").write_text(
        json.dumps(table, indent=2), encoding="utf-8")
    print("\n--- means ---")
    for phys in PHYSICS:
        sel = [r for r in table if r["physics"] == phys]
        line = "  ".join(f"m{m}={st.mean(r[f'm{m}'] for r in sel):5.1f}"
                         f"(min {min(r[f'm{m}'] for r in sel):5.1f})" for m in MARGINS)
        print(f"{phys:<8} {line}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
