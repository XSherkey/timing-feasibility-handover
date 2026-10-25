"""F1b: at what drift magnitude does a fixed constant break, and does calibration track?

F1 showed that +2 s of extra acquisition time does NOT break an 18 s constant: the
constant had ~2 s of margin, so the perturbation stayed inside it.  This sweep finds
the boundary instead of assuming it.

For each drift d (extra signalling seconds):
  * fixed18  - the constant a practitioner tuned on the nominal twin
  * best     - the best constant for that d (an upper bound no calibration can beat)
  * tau*     - the probe-calibrated threshold for that d (what PCS would use)
  * calib    - maxel with lead = tau* (same policy, calibrated threshold)

The interesting quantity is when fixed18 falls behind best/calib.
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
OUT = ROOT / "results" / "routeA_f1"
W = ["--w-rel", "0.7", "--w-lat", "0.1", "--w-pow", "0.2"]
DRIFTS = [1.2, 3.2, 4.4, 5.6, 6.8]  # acquisition signalling time (nominal 1.2)
LEADS = [16, 18, 20, 22, 24, 26]


def run(cmd: list[str]) -> str:
    with LOG.open("a", encoding="utf-8") as fh:
        fh.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] [F1b] {' '.join(cmd)}\n")
    r = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    if r.returncode != 0:
        raise SystemExit(f"failed: {' '.join(cmd)}\n{r.stdout}\n{r.stderr}")
    return r.stdout


def eval_lead(lead: int, acq: float, tag: str) -> float:
    path = OUT / f"f1b_{tag}_lead{lead}_acq{acq}.json"
    cmd = [PY, "scripts/eval_shield.py", "--policy", "maxel", "--lead", str(lead),
           "--acq-signaling", str(acq), "--seed", "0", *W,
           "--label", tag, "--out", str(path)]
    run(cmd)
    rec = json.load(open(path, encoding="utf-8"))[-1]
    return 100 * rec["arctic"][0]


def probe_tau(acq: float) -> float:
    path = OUT / f"f1b_probe_acq{acq}.json"
    cmd = [PY, "scripts/probe_feasibility.py", "--run", "results/campaign_1023/almond_seed0",
           "--regime", "polar", "--acq-signaling", str(acq), "--out", str(path)]
    run(cmd)
    d = json.load(open(path, encoding="utf-8"))
    return float(d["tau_late"])


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    rows = []
    for acq in DRIFTS:
        tau = probe_tau(acq)
        hsr = {L: eval_lead(L, acq, f"d{acq}") for L in LEADS}
        best_lead = max(hsr, key=hsr.get)
        # the calibrated threshold is clamped to the grid used by the policy
        tau_lead = min(LEADS, key=lambda L: abs(L - tau))
        rows.append(dict(acq=acq, drift=round(acq - 1.2, 1), tau_star=tau,
                         fixed18=hsr[18], best=hsr[best_lead], best_lead=best_lead,
                         calib=hsr[tau_lead], calib_lead=tau_lead, by_lead=hsr))
        print(f"drift +{acq - 1.2:4.1f}s  tau*={tau:5.1f}  fixed18={hsr[18]:5.1f}  "
              f"best={hsr[best_lead]:5.1f} (lead {best_lead})  calib={hsr[tau_lead]:5.1f}", flush=True)

    (ROOT / "results" / "routeA" / "f1b_drift_table.json").write_text(
        json.dumps(rows, indent=2), encoding="utf-8")
    print("\nwrote results/routeA/f1b_drift_table.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
