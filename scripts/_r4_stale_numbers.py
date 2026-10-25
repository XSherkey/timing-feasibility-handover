"""R4 (v22) part 5: purge the remaining stale headline numbers and point them at the unified run."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "almond-repro"
D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"
h = json.loads((ROOT / "results" / "routeA_r3" / "headline_consistent" / "summary.json").read_text(encoding="utf-8"))
lad = json.loads((ROOT / "results" / "routeA_r3" / "ladder_consistent" / "summary.json").read_text(encoding="utf-8"))
A = h["arms"]
m = lambda k: A[k]["summary"]["mean"]
s = lambda k: A[k]["summary"]["sd"]
c = lambda k, key: 100.0 * A[k]["causes"].get(key, 0.0)
R = lad["regimes"]
mn = lambda reg, arm: R[reg][arm]["summary"]["mean"]

p = D / "paper_en.md"
t = p.read_text(encoding="utf-8")
done = []


def rep(old, new, label):
    global t
    n = t.count(old)
    if n != 1:
        print(f"  MISS [{label}] count={n}: {old[:70]}")
        return
    t = t.replace(old, new, 1)
    done.append(label)


# 1. the Fig. 8 ladder sentence inside VI-D
rep("no knowledge (74.5 → 54.6), reward λ = 8 (84.4 → 55.4), the LLM's narrative-inferred 16 s rule (92.5 → 85.1, because its magnitude does not track), the tuned 18 s constant (93.3 → 92.4), the deployed probe-calibrated τ_used = 18 s shield (93.4 → 92.5), and the per-attempt oracle (93.4 → 93.4).",
    f"no knowledge ({mn('nominal','no_knowledge'):.1f} → {mn('plus2s','no_knowledge'):.1f}), reward λ = 8 "
    f"({mn('nominal','reward_lam8'):.1f} → {mn('plus2s','reward_lam8'):.1f}), the narrative-inferred 16 s rule "
    f"({mn('nominal','narrative_16s_rule'):.1f} → {mn('plus2s','narrative_16s_rule'):.1f}, because its magnitude "
    f"does not track), the tuned 18 s constant ({mn('nominal','tuned_constant_18'):.1f} → "
    f"{mn('plus2s','tuned_constant_18'):.1f}), the deployed probe-calibrated τ_used = 18 s shield "
    f"({mn('nominal','deployed_probe_shield'):.1f} → {mn('plus2s','deployed_probe_shield'):.1f}), and the "
    f"per-attempt oracle ({mn('nominal','oracle'):.1f} → {mn('plus2s','oracle'):.1f}).",
    "ladder")

# 2. nomenclature values
rep("**mined-rule campaign arm** is the 16 s rule with no margin (the 93.6% campaign figure).",
    f"**mined-rule campaign arm** is the 16 s rule with no margin ({m('almond_rule16'):.1f}% at |lat| ≥ 70°).",
    "nom-mined")
rep("**deployed probe-calibrated algorithm** is the same rule at τ_used = 18 s (93.31% on common episodes).",
    f"**deployed probe-calibrated algorithm** is the same rule at τ_used = 18 s ({m('almond_rule18'):.2f}% at "
    f"|lat| ≥ 70°).", "nom-deployed")
rep("**tuned constant** is the highest-elevation controller with a fixed 18 s lead and no learning (94.0%).",
    f"**tuned constant** is the highest-elevation controller with a fixed 18 s lead and no learning "
    f"({m('maxel18'):.1f}%).", "nom-const")
rep("**oracle shield** clamps each attempt to its realised requirement (upper reference, 93.31%).",
    f"**oracle shield** clamps each attempt to its realised requirement (upper reference, "
    f"{m('oracle'):.2f}%).", "nom-oracle")

# 3. intro end-to-end figure
rep("The end-to-end campaign figure of the mined-rule campaign arm, 93.6% ± 0.7%, is reproduced separately and agrees with the frozen τ = 16 s arm within ≈1.2 pp",
    f"The end-to-end campaign figure of the mined-rule campaign arm, {m('almond_rule16'):.1f}% ± "
    f"{s('almond_rule16'):.2f}%, sits within ≈1.2 pp of the frozen τ = 16 s arm",
    "intro-93.6")

# 4. the constant-vs-arm comparison
rep("matches the mined-rule campaign arm at nominal physics (94.0% vs 93.6%)",
    f"matches the mined-rule campaign arm at nominal physics ({m('maxel18'):.1f}% vs {m('almond_rule16'):.1f}%)",
    "const-vs-arm")

# 5. failure-class range in IV-A
rep("moves from 22.1% to 0.6% between the reward-only campaign arm and the mined-rule campaign arm",
    f"moves from {c('ppomlp_none','late_handover'):.1f}% to {c('almond_rule16','late_handover'):.1f}% between "
    f"the reward-only campaign arm and the mined-rule campaign arm", "iv-a-range")

# 6. epsilon-tail example
rep("the realized post-shield late-handover share is 0.6% against ε = 5%",
    f"the realized post-shield late-handover share is {c('almond_rule16','late_handover'):.1f}% against ε = 5%",
    "eps-tail")

p.write_text(t, encoding="utf-8")
print("applied:", done)
