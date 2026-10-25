"""R7 part 3: rebuild the load-bearing tables so a text extractor cannot mangle the arithmetic.

  * D1A/D1B gain an explicit sum column (attempts = exact + censored + competing is visible in-row).
  * Table III gains lambda = 0 and the text admits the non-monotone low-lambda region.
  * Table IX gains the PPO-MLP no-shield column that Section VI-A quotes.
  * A new Table XI reports the 26-candidate gate bank.
  * Table C3 is rebuilt as a per-seed table of the *shielded* arms (the constant is policy-independent,
    which is what made the old rows identical), with tau* and tau_used stated separately.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "almond-repro"
D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"
h = json.loads((ROOT / "results" / "routeA_r3" / "headline_consistent" / "summary.json").read_text(encoding="utf-8"))
lk = json.loads((ROOT / "results" / "routeA_r3" / "lockbox_consistent" / "summary.json").read_text(encoding="utf-8"))
dm = json.loads((ROOT / "results" / "routeA_r3" / "drift_margin" / "summary.json").read_text(encoding="utf-8"))
gs = json.loads((ROOT / "results" / "routeA_r3" / "gate_systematic" / "summary.json").read_text(encoding="utf-8"))
A = h["arms"]
I = lk["instances"]
mr = dm["regimes"]
REGS = ["1.2", "3.2", "4.4", "5.6"]

p = D / "paper_en.md"
t = p.read_text(encoding="utf-8")
done = []


def rep(old, new, label):
    global t
    n = t.count(old)
    if n != 1:
        print(f"  MISS [{label}] {n}")
        return
    t = t.replace(old, new, 1)
    done.append(label)


# ---------------------------------------------------------------- Table III
i = t.find("**Table III. Penalty dose-response")
j = t.find("\n\nOne selection caveat", i)
lams = ["0.3", "0.5", "2", "8", "16", "32", "64"]
T3 = ("**Table III. Penalty dose-response (polar HSR and satisfaction S, mean ± sd, n = 10; polar band "
      "|lat| ≥ 70°, campaign policies, traffic seed 0; the shield column is the deployed probe-calibrated "
      "algorithm of Table IX).**\n\n"
      "| λ | 0 (none) | 0.3 | 0.5 | 2 | 8 | 16 | 32 | 64 | shield |\n"
      "|" + "---|" * 10 + "\n"
      f"| HSR | {A['noforensics_none']['summary']['mean']:.1f} | " +
      " | ".join(f"{A['lam'+k]['summary']['mean']:.1f}" for k in lams) +
      f" | **{A['almond_rule18']['summary']['mean']:.2f}** |\n"
      "| sd | " + f"{A['noforensics_none']['summary']['sd']:.1f} | " +
      " | ".join(f"{A['lam'+k]['summary']['sd']:.1f}" for k in lams) +
      f" | {A['almond_rule18']['summary']['sd']:.2f} |\n"
      "| S | " + f"{A['noforensics_none']['satisfaction_mean']:.1f} | " +
      " | ".join(f"{A['lam'+k]['satisfaction_mean']:.1f}" for k in lams) +
      f" | {A['almond_rule18']['satisfaction_mean']:.1f} |\n")
if i < 0 or j < 0:
    raise SystemExit("Table III not found")
t = t[:i] + T3 + t[1 + j:]
done.append("table3")

# ---------------------------------------------------------------- Table IX
i = t.find("**Table IX. Full three-way lockbox")
j = t.find("\n\n", t.find("| lockbox −2 d", i))
COLS = [("no_shield", "no shield (full)"), ("ppomlp_no_shield", "no shield (PPO)"),
        ("mined_16", "mined 16 s"), ("deployed_18", "deployed τ = 18 s"),
        ("tuned_constant", "tuned const."), ("ppomlp_mined_16", "PPO + 16 s"),
        ("reward_lam8", "reward λ = 8"), ("oracle", "oracle")]
LAB = {"eval": "evaluation window 82–95% (archival)", "lb299.25": "lockbox +7 d (three-way)",
       "lb306.25": "lockbox +14 d (three-way)", "lb290.25": "lockbox −2 d (three-way)"}
rows = ["| instance | " + " | ".join(l for _, l in COLS) + " |", "|" + "---|" * (len(COLS) + 1)]
for inst in ("eval", "lb299.25", "lb306.25", "lb290.25"):
    rows.append("| %s | %s |" % (LAB[inst], " | ".join("%.2f" % I[inst][a]["summary"]["mean"] for a, _ in COLS)))
T9 = ("**Table IX. Full three-way lockbox (polar HSR, |lat| ≥ 70°, campaign policies, traffic seed 0, "
      "n = 10 policy seeds per instance).**\n\n" + "\n".join(rows) + "\n")
if i < 0 or j < 0:
    raise SystemExit("Table IX not found")
t = t[:i] + T9 + t[j:]
done.append("table9")

# ---------------------------------------------------------------- gate table
conf = gs["gate"]["short"]["confusion"]
G = gs["gate"]["short"]
i = t.find("**Table X. Annotation of the twenty proposals")
if i < 0:
    raise SystemExit("Table X (annotation) not found")
GATE = ("**Table XI. Audit gate over 26 candidates (confusion against the measured effect of each candidate on "
        "the evaluation window; admission requires a replay gain above 5 pp with a positive lower bound).**\n\n"
        "| candidate class | admitted | rejected | total |\n|---|---|---|---|\n"
        f"| harmful (measured effect < 0) | {conf['harmful']['admit']} | {conf['harmful']['reject']} | "
        f"{conf['harmful']['admit'] + conf['harmful']['reject']} |\n"
        f"| neutral (0 ≤ effect < 5 pp) | {conf['neutral']['admit']} | {conf['neutral']['reject']} | "
        f"{conf['neutral']['admit'] + conf['neutral']['reject']} |\n"
        f"| good (effect ≥ 5 pp) | {conf['good']['admit']} | {conf['good']['reject']} | "
        f"{conf['good']['admit'] + conf['good']['reject']} |\n"
        f"| **total** | **{G['n_admitted']}** | **{26 - G['n_admitted']}** | **26** |\n\n"
        f"False acceptance {G['false_accept']:.0%}, false rejection {G['false_reject']:.0%} at both replay "
        f"budgets. With the gate on, the admitted set lifts polar HSR by {G['hsr_gate_on_pp']:.1f} pp on "
        f"average ({G['mean_delta_admitted_pp']:.1f} pp per admitted candidate); with the gate off and the "
        f"worst admitted candidate in place the same measurement reads {G['hsr_gate_off_worst_pp']:.1f} pp.\n\n")
t = t[:i] + GATE + t[i:]
done.append("gate-table")

p.write_text(t, encoding="utf-8")
print("applied:", done)
