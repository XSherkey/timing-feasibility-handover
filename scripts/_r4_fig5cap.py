"""R4 (v22) part 3: Fig. 5 caption from the unified numbers."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "almond-repro"
D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"
d = json.loads((ROOT / "results" / "routeA_r3" / "headline_consistent" / "summary.json").read_text(encoding="utf-8"))
A = d["arms"]
m = lambda k: A[k]["summary"]["mean"]
s = lambda k: A[k]["summary"]["sd"]

p = D / "paper_en.md"
t = p.read_text(encoding="utf-8")
i = t.find("**Fig. 5.** Where the gap comes from.")
if i < 0:
    raise SystemExit("Fig. 5 caption not found")
j = t.find("\n\n", i)
CAP = (f"**Fig. 5.** Where the gap comes from. Polar HSR at |lat| ≥ 70°, campaign policies, traffic seed 0, "
       f"identical episodes, n = 10 policy seeds, error bars ±sd: reward-only PPO-MLP {m('ppomlp_none'):.1f}; "
       f"the same knowledge as a reward penalty at its best coefficient (λ = 8) {m('lam8'):.1f}; the same "
       f"knowledge as a decision shield on the baseline's own policies {m('ppomlp_rule16'):.1f}; the "
       f"mined-rule campaign arm (16 s shield, no margin) {m('almond_rule16'):.1f}; the tuned constant "
       f"(18 s lead, no learning) {m('maxel18'):.1f}. The deployed probe-calibrated algorithm (τ_used = 18 s) "
       f"is {m('almond_rule18'):.2f} ± {s('almond_rule18'):.2f}. All five bars come from one protocol, so the "
       f"differences between them are protocol-free; the decomposition (23.4 of 24.1 pp from the constraint) "
       f"is given in Section VI-B.")
t = t[:i] + CAP + t[j:]
p.write_text(t, encoding="utf-8")
print("Fig. 5 caption updated")
print(CAP[:200])
