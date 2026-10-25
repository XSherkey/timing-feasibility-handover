"""R4 (v22): rebuild Tables II and III and rewrite Sections VI-B/VI-C on the unified protocol."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "almond-repro"
D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"
d = json.loads((ROOT / "results" / "routeA_r3" / "headline_consistent" / "summary.json").read_text(encoding="utf-8"))
A = d["arms"]


def m(k):
    return A[k]["summary"]["mean"]


def s(k):
    return A[k]["summary"]["sd"]


def c(k, key):
    return 100.0 * A[k]["causes"].get(key, 0.0)


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


# ---------------------------------------------------------------- Table II
start = t.find("**Table II. Failure attribution")
end = t.find("\n\n", t.find("| full", start) if t.find("| full", start) > 0 else t.find("|", start))
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

# ---------------------------------------------------------------- Table III
start = t.find("**Table III. Penalty dose-response")
end = t.find("\n\n", t.find("| S |", start))
lams = ["0.3", "0.5", "2", "8", "16", "32", "64"]
hdr = "| λ | " + " | ".join(lams) + " | shield (deployed) |"
sep = "|" + "---|" * (len(lams) + 2)
row_h = "| HSR | " + " | ".join(f"{m('lam'+k):.1f}" for k in lams) + f" | **{m('almond_rule18'):.2f}** |"
row_sd = "| sd | " + " | ".join(f"{s('lam'+k):.1f}" for k in lams) + f" | {s('almond_rule18'):.2f} |"
row_s = "| S | " + " | ".join(f"{A['lam'+k]['satisfaction_mean']:.1f}" for k in lams) + \
        f" | {A['almond_rule18']['satisfaction_mean']:.1f} |"
T3 = ("**Table III. Penalty dose-response (polar HSR and satisfaction S, mean ± sd, n = 10; polar band "
      "|lat| ≥ 70°, campaign policies, traffic seed 0; the shield column is the deployed probe-calibrated "
      "algorithm of Table VIII).**\n\n" + "\n".join([hdr, sep, row_h, row_sd, row_s]) + "\n")
if start < 0 or end < 0:
    raise SystemExit("Table III not found")
t = t[:start] + T3 + t[end:]
done.append("table3")

# ---------------------------------------------------------------- VI-B prose
i = t.find("Fig. 5 decomposes the gap")
j = t.find("\n\n", t.find("is the controlled version of the same accounting.", i))
VI_B = (
    f"Fig. 5 decomposes the gap between a literature-style baseline and the deployed pipeline. Every bar is "
    f"measured under one protocol—campaign policies, traffic seed 0, identical episodes, ten policy seeds—so "
    f"the bars are directly comparable to Table II and to the evaluation row of Table VIII. The hand-crafted "
    f"PPO-MLP baseline (reward only) reaches {m('ppomlp_none'):.1f}% ± {s('ppomlp_none'):.1f}% polar success. "
    f"Injecting the same knowledge as a reward penalty, at its best coefficient λ = 8, reaches "
    f"{m('lam8'):.1f}% ± {s('lam8'):.1f}%. Injecting the same knowledge as a decision shield on the *baseline's* "
    f"policies reaches {m('ppomlp_rule16'):.1f}% ± {s('ppomlp_rule16'):.1f}%. The **mined-rule campaign arm** "
    f"(the full-system policies with the mined 16 s rule and no margin) reaches {m('almond_rule16'):.1f}% ± "
    f"{s('almond_rule16'):.2f}%, and the **tuned constant** with no learning at all (highest-elevation "
    f"candidate, fixed 18 s lead) reaches {m('maxel18'):.1f}%. For reference the deployed probe-calibrated "
    f"algorithm (τ_used = 18 s) is {m('almond_rule18'):.2f}% ± {s('almond_rule18'):.2f}%.\n\n"
    f"The decomposition is then arithmetic within a single protocol: the total gap from the reward-only "
    f"baseline to the mined-rule arm is {m('almond_rule16') - m('ppomlp_none'):.1f} pp, and "
    f"{m('ppomlp_rule16') - m('ppomlp_none'):.1f} pp of it is recovered by applying the constraint as a shield "
    f"to the *baseline's own* policies—leaving {m('almond_rule16') - m('ppomlp_rule16'):.1f} pp for everything "
    f"the full-system training adds beyond a shielded baseline. The constraint, not the learner, carries the "
    f"gap; the learner contributes selection quality worth about half a point.\n\n"
    f"The failure attribution confirms the mechanism (Table II). Late handovers are the only failure class "
    f"that moves materially across arms: {c('ppomlp_none','late_handover'):.1f}% of polar attempts for the "
    f"reward-only baseline, {c('noforensics_none','late_handover'):.1f}% for an identical-architecture "
    f"ablation that never mines knowledge, {c('almond_rule16','late_handover'):.1f}% for the mined-rule arm. "
    f"Window and route failures barely move ({c('almond_rule16','window_exceeded'):.1f}% and "
    f"{c('almond_rule16','no_route'):.1f}% under the shield against "
    f"{c('ppomlp_none','window_exceeded'):.1f}% and {c('ppomlp_none','no_route'):.1f}% without it); the shield "
    f"trades a fraction of window violations for the late handovers it removes, exactly as Eq. (3) predicts.")
if i < 0 or j < 0:
    raise SystemExit("VI-B block not found")
t = t[:i] + VI_B + t[j:]
done.append("viB")

p.write_text(t, encoding="utf-8")
print("applied:", done)
print("decomposition:", round(m('almond_rule16') - m('ppomlp_none'), 2),
      round(m('ppomlp_rule16') - m('ppomlp_none'), 2),
      round(m('almond_rule16') - m('ppomlp_rule16'), 2))
