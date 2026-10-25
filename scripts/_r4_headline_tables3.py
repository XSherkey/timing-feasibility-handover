"""R4 (v22) retry 2: correct end markers for Tables II and III."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "almond-repro"
D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"
d = json.loads((ROOT / "results" / "routeA_r3" / "headline_consistent" / "summary.json").read_text(encoding="utf-8"))
A = d["arms"]
m = lambda k: A[k]["summary"]["mean"]
s = lambda k: A[k]["summary"]["sd"]
c = lambda k, key: 100.0 * A[k]["causes"].get(key, 0.0)

p = D / "paper_en.md"
t = p.read_text(encoding="utf-8")
done = []

# ---- Table II: replace from caption to the note that follows the table ----
start = t.find("**Table II. Failure attribution")
note = t.find("*Note.* The 0.6% late share here", start)
if start < 0 or note < 0:
    raise SystemExit("Table II block not found")
T2 = ("**Table II. Failure attribution, polar band (share of attempts; site |lat| ≥ 70°, campaign policies, "
      "traffic seed 0, common episodes, n = 10).**\n\n"
      "| arm | late_handover (%) | window_exceeded (%) | no_route (%) | polar HSR (%) |\n"
      "|---|---|---|---|---|\n"
      f"| PPO-MLP (reward only) | {c('ppomlp_none','late_handover'):.1f} | "
      f"{c('ppomlp_none','window_exceeded'):.1f} | {c('ppomlp_none','no_route'):.1f} | "
      f"{m('ppomlp_none'):.1f} ± {s('ppomlp_none'):.1f} |\n"
      f"| same architecture, no mining | {c('noforensics_none','late_handover'):.1f} | "
      f"{c('noforensics_none','window_exceeded'):.1f} | {c('noforensics_none','no_route'):.1f} | "
      f"{m('noforensics_none'):.1f} ± {s('noforensics_none'):.1f} |\n"
      f"| **mined-rule campaign arm (16 s)** | **{c('almond_rule16','late_handover'):.1f}** | "
      f"{c('almond_rule16','window_exceeded'):.1f} | {c('almond_rule16','no_route'):.1f} | "
      f"**{m('almond_rule16'):.1f} ± {s('almond_rule16'):.2f}** |\n\n"
      "Every row is measured on the same episodes with the same traffic seed; the late-handover share is the "
      "failure class the constraint removes, and the other two classes move by less than a point.\n\n")
t = t[:start] + T2 + t[note:]
done.append("table2")

# ---- Table III -----------------------------------------------------------
start = t.find("**Table III. Penalty dose-response")
end = t.find("\n\nOne selection caveat", start)
if start < 0 or end < 0:
    raise SystemExit("Table III block not found")
lams = ["0.3", "0.5", "2", "8", "16", "32", "64"]
T3 = ("**Table III. Penalty dose-response (polar HSR and satisfaction S, mean ± sd, n = 10; polar band "
      "|lat| ≥ 70°, campaign policies, traffic seed 0; the shield column is the deployed probe-calibrated "
      "algorithm of Table VIII).**\n\n"
      "| λ | " + " | ".join(lams) + " | shield (deployed) |\n"
      "|" + "---|" * (len(lams) + 2) + "\n"
      "| HSR | " + " | ".join(f"{m('lam'+k):.1f}" for k in lams) + f" | **{m('almond_rule18'):.2f}** |\n"
      "| sd | " + " | ".join(f"{s('lam'+k):.1f}" for k in lams) + f" | {s('almond_rule18'):.2f} |\n"
      "| S | " + " | ".join(f"{A['lam'+k]['satisfaction_mean']:.1f}" for k in lams) +
      f" | {A['almond_rule18']['satisfaction_mean']:.1f} |\n")
t = t[:start] + T3 + "\n" + t[end:]
done.append("table3")

p.write_text(t, encoding="utf-8")
print("applied:", done)
