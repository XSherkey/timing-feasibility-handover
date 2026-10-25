"""F1 driver: does a tuned constant survive a physics shift?

Runs the matrix A-D of ROUTE_A_EXPERIMENT_PLAN.md through eval_shield, logs every
command to results/routeA/commands.log, and writes results/routeA/f1_table.json.

A: maxel, lead 18, nominal physics      (must reproduce E12, 92.5-94.0)
B: maxel, lead 18, acq_signaling 3.2    (must drop >= 2 pp if the story holds)
C: maxel, lead 20, perturbed            (re-tuning after the shift)
D: maxel, lead 22, perturbed            (wider re-tuning)
E: PCS on perturbed physics             (copied from campaign_pcs3_sig32)
F: learned policy + mined 16 s shield   (copied from campaign_sig32, seeds 0-2)
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
TABLE = ROOT / "results" / "routeA" / "f1_table.json"
W = ["--w-rel", "0.7", "--w-lat", "0.1", "--w-pow", "0.2"]


def run(cmd: list[str]) -> None:
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a", encoding="utf-8") as fh:
        fh.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] [F1] {' '.join(cmd)}\n")
    r = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit(f"command failed: {' '.join(cmd)}\n{r.stdout}\n{r.stderr}")


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    arms = [
        ("A_maxel18_ref", 18, None),
        ("B_maxel18_sig32", 18, 3.2),
        ("C_maxel20_sig32", 20, 3.2),
        ("D_maxel22_sig32", 22, 3.2),
    ]
    for name, lead, acq in arms:
        for seed in range(5):
            path = OUT / f"{name}_s{seed}.json"
            cmd = [PY, "scripts/eval_shield.py", "--policy", "maxel", "--lead", str(lead),
                   "--seed", str(seed), *W, "--label", f"{name}_s{seed}", "--out", str(path)]
            if acq is not None:
                cmd += ["--acq-signaling", str(acq)]
            run(cmd)

    # collect
    table = {"A": [], "B": [], "C": [], "D": [], "E": [], "F": []}
    for name, lead, acq in arms:
        key = name[0]
        for seed in range(5):
            rec = json.load(open(OUT / f"{name}_s{seed}.json", encoding="utf-8"))[-1]
            table[key].append(dict(seed=seed, arctic=100 * rec["arctic"][0],
                                   mid=100 * rec["midlat"][0], S=rec["satisfaction"]))

    # E: PCS on perturbed physics
    pcs = ROOT / "results" / "campaign_pcs3_sig32"
    for sd in range(5):
        d = json.load(open(pcs / f"almond_seed{sd}" / "run_summary.json", encoding="utf-8"))
        table["E"].append(dict(seed=sd, arctic=100 * d["final"]["arctic"]["hsr"],
                               S=d["final"]["satisfaction"],
                               tau=(d["events"] and [e["tau"] for e in d["events"] if e["event"] == "probe_tau"] or [None])[0]))
    # F: learned policy + mined 16 s shield on the perturbed physics (seeds 0-2 only)
    sig = ROOT / "results" / "campaign_sig32"
    for sd in range(3):
        d = json.load(open(sig / f"almond_seed{sd}" / "run_summary.json", encoding="utf-8"))
        table["F"].append(dict(seed=sd, arctic=100 * d["final"]["arctic"]["hsr"],
                               S=d["final"]["satisfaction"]))

    TABLE.write_text(json.dumps(table, indent=2), encoding="utf-8")

    def stat(rows):
        import statistics as st
        v = [r["arctic"] for r in rows]
        return sum(v) / len(v), (st.stdev(v) if len(v) > 1 else 0.0)

    print(f"{'arm':<6}{'n':>3}{'arctic mean':>13}{'sd':>7}")
    for k in "ABCDEF":
        m, s = stat(table[k])
        print(f"{k:<6}{len(table[k]):>3}{m:>12.1f}%{s:>7.2f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
