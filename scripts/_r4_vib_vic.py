"""R4 (v22) part 2: rewrite the VI-B lead paragraphs and the VI-C lambda numbers."""
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

# ---------------- VI-B: replace the opening + the protocol paragraph -------
i = t.find("Fig. 5 decomposes the gap")
j = t.find("\n\n", t.find("hold it while reading the rest.", i))
if i < 0 or j < 0:
    raise SystemExit("VI-B block not found")
VI_B = (
    f"Fig. 5 decomposes the gap between a literature-style baseline and the deployed pipeline. Every bar is "
    f"measured under one protocol—campaign policies, traffic seed 0, identical episodes, ten policy seeds—so "
    f"the bars are directly comparable to Table II and to the evaluation row of Table VIII.\n\n"
    f"The hand-crafted PPO-MLP baseline (reward only) reaches {m('ppomlp_none'):.1f}% ± {s('ppomlp_none'):.1f}% "
    f"polar success. Injecting the same knowledge as a reward penalty, at its best coefficient λ = 8, reaches "
    f"{m('lam8'):.1f}% ± {s('lam8'):.1f}%. Injecting the same knowledge as a decision shield on the *baseline's* "
    f"policies reaches {m('ppomlp_rule16'):.1f}% ± {s('ppomlp_rule16'):.1f}%. The **mined-rule campaign arm** "
    f"(the full-system policies with the mined 16 s rule and no margin) reaches {m('almond_rule16'):.1f}% ± "
    f"{s('almond_rule16'):.2f}%, and the **tuned constant** with no learning at all (highest-elevation "
    f"candidate, fixed 18 s lead) reaches {m('maxel18'):.1f}%. For reference the deployed probe-calibrated "
    f"algorithm (τ_used = 18 s) is {m('almond_rule18'):.2f}% ± {s('almond_rule18'):.2f}%. These four "
    f"names—mined-rule campaign arm, deployed probe-calibrated algorithm, tuned constant, oracle "
    f"shield—are used consistently for the rest of the paper (threshold ledger, Section V-D).\n\n"
    f"The decomposition is arithmetic within a single protocol. The total gap from the reward-only baseline "
    f"to the mined-rule arm is {m('almond_rule16') - m('ppomlp_none'):.1f} pp; "
    f"{m('ppomlp_rule16') - m('ppomlp_none'):.1f} pp of it is recovered by applying the constraint as a shield "
    f"to the *baseline's own* policies, leaving {m('almond_rule16') - m('ppomlp_rule16'):.1f} pp for everything "
    f"the full-system training adds beyond a shielded baseline. The constraint, not the learner, carries the "
    f"gap. Because every number in this subsection now comes from the same runs as Tables II, III and VIII, "
    f"the earlier caveat about mixing the campaign protocol with the common-episode factorial is discharged: "
    f"there is only one protocol left to reconcile with, and it is the one this paragraph uses.")
t = t[:i] + VI_B + t[j:]
done.append("viB")

# ---------------- VI-C: lambda numbers ------------------------------------
pairs = [
    ("performance climbs from the no-knowledge level of the same trained-policy family (67.5% ± 13.2% on the frozen factorial's no-shield arm, Table C1; 78.9% ± 11.0% for the no-mining campaign arm, Table II) to 84.4% ± 6.8% at λ = 8—and then *reverses*: 81.8% (λ = 16), 81.2% (λ = 32), 74.5% ± 17.0% (λ = 64).",
     f"performance climbs from the no-knowledge level of the same trained-policy family "
     f"({m('noforensics_none'):.1f}% ± {s('noforensics_none'):.1f}%, Table II) to {m('lam8'):.1f}% ± {s('lam8'):.1f}% "
     f"at λ = 8—and then *reverses*: {m('lam16'):.1f}% (λ = 16), {m('lam32'):.1f}% (λ = 32), "
     f"{m('lam64'):.1f}% ± {s('lam64'):.1f}% (λ = 64)."),
    ("The shield sits at 93.6% ± 0.7% (campaign; 93.3% ± 0.3% on the frozen factorial), 9.2 pp above the best penalty point, with an order of magnitude less variance.",
     f"The deployed shield sits at {m('almond_rule18'):.2f}% ± {s('almond_rule18'):.2f}%, "
     f"{m('almond_rule18') - m('lam8'):.1f} pp above the best penalty point, with two orders of magnitude less "
     f"variance ({s('almond_rule18'):.2f} against {s('lam8'):.1f} pp)."),
    ("it is simultaneously higher in reliability (93.6 vs 84.4) and in arctic-band satisfaction (80.7 vs 68.8)",
     f"it is simultaneously higher in reliability ({m('almond_rule18'):.2f} vs {m('lam8'):.1f}) and in "
     f"arctic-band satisfaction ({A['almond_rule18']['satisfaction_mean']:.1f} vs {A['lam8']['satisfaction_mean']:.1f})"),
    ("so 84.4% is an optimistic estimate of the reward channel's ceiling. The comparison it supports is an upper-bound comparison, and the conclusion survives the optimism: even the best of seven penalty settings stays 9.2 pp below the shield.",
     f"so {m('lam8'):.1f}% is an optimistic estimate of the reward channel's ceiling. The comparison it supports "
     f"is an upper-bound comparison, and the conclusion survives the optimism: even the best of seven penalty "
     f"settings stays {m('almond_rule18') - m('lam8'):.1f} pp below the shield."),
]
for old, new in pairs:
    if t.count(old) != 1:
        print("  MISS:", t.count(old), old[:60])
        continue
    t = t.replace(old, new, 1)
    done.append(old[:24])

p.write_text(t, encoding="utf-8")
print("applied:", done)
