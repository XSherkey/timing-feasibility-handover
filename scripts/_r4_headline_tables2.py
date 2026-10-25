"""R4 (v22) retry: Table III block uses '| S |' as its last row, adjust the end marker."""
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


def rep(old, new, label):
    global t
    n = t.count(old)
    if n != 1:
        raise SystemExit(f"[{label}] found {n}")
    t = t.replace(old, new, 1)
    done.append(label)


# ---- Table II ------------------------------------------------------------
start = t.find("**Table II. Failure attribution")
end = t.find("\n\n", t.find("| **full system", start)) if t.find("| **full system", start) > 0 else t.find("\n\n", t.find("| full system", start))
T2 = ("**Table II. Failure attribution, polar band (share of attempts; site |lat| ≥ 70°, campaign policies, "
      "traffic seed 0, common episodes, n = 10).**\n\n"
      "| arm | late_handover (%) | window_exceeded (%) | no_route (%) | polar HSR (%) |\n"
      "|---|---|---|---|---|\n"
      f"| PPO-MLP (reward only) | {c('ppomlp_none','late_handover'):.1f} | {c('ppomlp_none','window_exceeded'):.1f} | "
      f"{c('ppomlp_none','no_route'):.1f} | {m('ppomlp_none'):.1f} ± {s('ppomlp_none'):.1f} |\n"
      f"| same architecture, no mining | {c('noforensics_none','late_handover'):.1f} | "
      f"{c('noforensics_none','window_exceeded'):.1f} | {c('noforensics_none','no_route'):.1f} | "
      f"{m('noforensics_none'):.1f} ± {s('noforensics_none'):.1f} |\n"
      f"| **mined-rule campaign arm (16 s)** | **{c('almond_rule16','late_handover'):.1f}** | "
      f"{c('almond_rule16','window_exceeded'):.1f} | {c('almond_rule16','no_route'):.1f} | "
      f"**{m('almond_rule16'):.1f} ± {s('almond_rule16'):.2f}** |\n")
if start < 0:
    raise SystemExit("Table II not found")
t = t[:start] + T2 + t[end:]
done.append("table2")

# ---- Table III -----------------------------------------------------------
start = t.find("**Table III. Penalty dose-response")
end = t.find("\n\n", t.find("| S |", start))
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
if start < 0 or end < 0:
    raise SystemExit("Table III not found")
t = t[:start] + T3 + t[end:]
done.append("table3")

p.write_text(t, encoding="utf-8")
print("applied:", done)
