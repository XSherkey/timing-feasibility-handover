"""R5: rebuild Tables C1-C3 and Fig. 2 on the unified factorial, and update every dependent number."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2] / "almond-repro"
D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"
fc = json.loads((ROOT / "results" / "routeA_r3" / "factorial_consistent" / "summary.json").read_text(encoding="utf-8"))
dm = json.loads((ROOT / "results" / "routeA_r3" / "drift_margin" / "summary.json").read_text(encoding="utf-8"))
A = fc["arms"]

p = D / "paper_en.md"
t = p.read_text(encoding="utf-8")
done = []


def rep(old, new, label):
    global t
    n = t.count(old)
    if n != 1:
        print(f"  MISS [{label}] {n}: {old[:70]}")
        return
    t = t.replace(old, new, 1)
    done.append(label)


def row(seed_vals, fmt="%.1f"):
    return " | ".join(fmt % v for v in seed_vals)


# ---------------------------------------------------------------- Table C1
i = t.find("**Table C1. Frozen-policy factorial")
j = t.find("\n\n", t.find("| late-handover share", i))
if i < 0:
    raise SystemExit("C1 not found")
rows = ["| seed | no shield | τ = 16 s (mined τ∗) | τ = 20 s (ablation) |", "|---|---|---|---|"]
for k in range(10):
    rows.append(f"| {k} | {A['none']['polar'][k]:.1f} | {A['rule16']['polar'][k]:.1f} | {A['rule20']['polar'][k]:.1f} |")
rows.append(f"| mean ± sd | {A['none']['summary']['mean']:.1f} ± {A['none']['summary']['sd']:.1f} | "
            f"{A['rule16']['summary']['mean']:.2f} ± {A['rule16']['summary']['sd']:.2f} | "
            f"{A['rule20']['summary']['mean']:.2f} ± {A['rule20']['summary']['sd']:.2f} |")
rows.append(f"| late-handover share | {min(A['none']['late']):.1f}–{max(A['none']['late']):.1f}% "
            f"(mean {np.mean(A['none']['late']):.1f}%) | "
            f"{min(A['rule16']['late']):.2f}–{max(A['rule16']['late']):.2f}% (mean {np.mean(A['rule16']['late']):.2f}%) | — |")
C1 = ("**Table C1. Frozen-policy factorial, campaign checkpoints, polar HSR (%) per seed (|lat| ≥ 70°, "
      "traffic seed 0, common episodes).**\n\n" + "\n".join(rows) + "\n")
t = t[:i] + C1 + t[j:]
done.append("C1")

# ---------------------------------------------------------------- Table C2
i = t.find("**Table C2. Deployed-threshold completion")
j = t.find("\n\n", t.find("| late-handover share", i))
rows = ["| seed | τ = 16 s | **τ = 18 s (deployed τ_used)** | τ = 20 s | oracle |", "|---|---|---|---|---|"]
for k in range(10):
    rows.append(f"| {k} | {A['rule16']['polar'][k]:.1f} | {A['rule18']['polar'][k]:.1f} | "
                f"{A['rule20']['polar'][k]:.1f} | {A['oracle']['polar'][k]:.1f} |")
rows.append(f"| mean ± sd | {A['rule16']['summary']['mean']:.2f} ± {A['rule16']['summary']['sd']:.2f} | "
            f"**{A['rule18']['summary']['mean']:.2f} ± {A['rule18']['summary']['sd']:.2f}** | "
            f"{A['rule20']['summary']['mean']:.2f} ± {A['rule20']['summary']['sd']:.2f} | "
            f"{A['oracle']['summary']['mean']:.2f} ± {A['oracle']['summary']['sd']:.2f} |")
rows.append(f"| late-handover share | {np.mean(A['rule16']['late']):.2f}% | **0.00%** | 0.00% | 0.00% |")
C2 = ("**Table C2. Deployed-threshold completion and oracle reference, polar HSR (%) per seed (|lat| ≥ 70°, "
      "traffic seed 0, common episodes).**\n\n" + "\n".join(rows) + "\n")
t = t[:i] + C2 + t[j:]
done.append("C2")

# ---------------------------------------------------------------- Table C3
regs = ["1.2", "3.2", "4.4", "5.6"]
i = t.find("**Table C3. Drift response per seed")
j = t.find("\n\n", t.find("| calibrated |", i))
if i < 0 or j < 0:
    raise SystemExit("C3 not found")
rows = ["| seed | δ = 0 | δ = +2 s | δ = +3.2 s | δ = +4.4 s |", "|---|---|---|---|---|"]
for k in range(5):
    cells = []
    for r in regs:
        cf = dm["regimes"][r]["arms"]["const_fixed18"]["polar"][k]
        cp = dm["regimes"][r]["arms"]["const_probed"]["polar"][k]
        tau = dm["regimes"][r]["tau_mode"] + 2
        cells.append(f"{cf:.1f} / {cp:.1f} ({tau:.0f})")
    rows.append(f"| {k} | " + " | ".join(cells) + " |")
def stat(arm, key, fn):
    return fn([dm["regimes"][r]["arms"][arm]["summary"][key] for r in regs])
rows.append("| mean ± sd (fixed 18 s) | " + " | ".join(f"{dm['regimes'][r]['arms']['const_fixed18']['summary']['mean']:.1f} ± {dm['regimes'][r]['arms']['const_fixed18']['summary']['sd']:.1f}" for r in regs) + " |")
rows.append("| mean ± sd (re-probed) | " + " | ".join(f"{dm['regimes'][r]['arms']['const_probed']['summary']['mean']:.1f} ± {dm['regimes'][r]['arms']['const_probed']['summary']['sd']:.1f}" for r in regs) + " |")
C3 = ("**Table C3. Drift response per seed, polar HSR (%) at |lat| ≥ 70°: fixed 18 s constant / "
      "probe-calibrated (re-probed threshold in parentheses), campaign policies, traffic seed 0, "
      "five policy seeds.**\n\n" + "\n".join(rows) + "\n")
t = t[:i] + C3 + t[j:]
done.append("C3")

p.write_text(t, encoding="utf-8")
print("applied:", done)
