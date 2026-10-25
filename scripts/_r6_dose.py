"""R7 part 8: honest non-monotone dose-response in the text, plus the Fig. 3 caption."""
from __future__ import annotations

import json
from pathlib import Path

D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"
ROOT = Path(__file__).resolve().parents[2] / "almond-repro"
h = json.loads((ROOT / "results" / "routeA_r3" / "headline_consistent" / "summary.json").read_text(encoding="utf-8"))
A = h["arms"]
m = lambda k: A[k]["summary"]["mean"]
s = lambda k: A[k]["summary"]["sd"]

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


rep("performance climbs from the no-knowledge level of the same trained-policy family (76.3% ± 12.1%, Table II) to 82.9% ± 6.5% at λ = 8—and then *reverses*: 80.3% (λ = 16), 78.2% (λ = 32), 73.1% ± 17.3% (λ = 64).",
    f"the response is **not monotone, and a weak penalty actively hurts**: against the no-penalty arm of the "
    f"same architecture ({m('noforensics_none'):.1f}% ± {s('noforensics_none'):.1f}%), λ = 0.3 and λ = 0.5 "
    f"*lose* {m('noforensics_none') - m('lam0.3'):.1f} and {m('noforensics_none') - m('lam0.5'):.1f} pp "
    f"({m('lam0.3'):.1f}% and {m('lam0.5'):.1f}%). The curve crosses back above the no-penalty level only at "
    f"λ = 2 ({m('lam2'):.1f}%), peaks at λ = 8 ({m('lam8'):.1f}% ± {s('lam8'):.1f}%), and then reverses: "
    f"{m('lam16'):.1f}% (λ = 16), {m('lam32'):.1f}% (λ = 32), {m('lam64'):.1f}% ± {s('lam64'):.1f}% "
    f"(λ = 64).", "vic-nonmonotone")

rep("The deployed shield sits at 93.36% ± 0.05%, 10.4 pp above the best penalty point",
    f"The deployed shield sits at {m('almond_rule18'):.2f}% ± {s('almond_rule18'):.2f}%, "
    f"{m('almond_rule18') - m('lam8'):.1f} pp above the best penalty point", "vic-shield")

# Fig. 3 caption
i = t.find("**Fig. 3.** The constant's failure boundary")
if i > 0:
    j = t.find("\n\n", i)
    CAP = (f"**Fig. 3.** Reward injection is a dose-response, and the shield dominates it. Left: polar HSR against "
           f"the penalty coefficient λ over the eight-point scan (error bars ±sd over ten seeds); the dashed "
           f"line is the deployed shield ({m('almond_rule18'):.2f}%). The curve is not monotone: λ = 0.3 and "
           f"0.5 sit *below* the no-penalty arm, and the response only clears it at λ = 2. Right: the (HSR, S) "
           f"frontier; the shield (star; S = {A['almond_rule18']['satisfaction_mean']:.1f}) lies above and to the "
           f"right of every penalty point (best penalty point S = {A['lam8']['satisfaction_mean']:.1f} at λ = 8).")
    t = t[:i] + CAP + t[j:]
    done.append("fig3-caption")

p.write_text(t, encoding="utf-8")
print("applied:", done)
