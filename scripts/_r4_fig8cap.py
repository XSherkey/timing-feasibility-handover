"""R4 (v22) part 4: Fig. 8 caption and the ladder sentence in VI-C."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "almond-repro"
D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"
lad = json.loads((ROOT / "results" / "routeA_r3" / "ladder_consistent" / "summary.json").read_text(encoding="utf-8"))
R = lad["regimes"]
mn = lambda reg, arm: R[reg][arm]["summary"]["mean"]

p = D / "paper_en.md"
t = p.read_text(encoding="utf-8")
done = []

# ---- Fig. 8 caption ------------------------------------------------------
i = t.find("**Fig. 8.** Six references on one axis")
if i < 0:
    raise SystemExit("Fig. 8 caption not found")
j = t.find("\n\n", i)
CAP = (f"**Fig. 8.** Six references on one axis at nominal physics and at +2 s of acquisition drift "
       f"(campaign policies, traffic seed 0, identical episodes, n = 10 policy seeds, error bars ±sd): "
       f"no knowledge ({mn('nominal','no_knowledge'):.1f} → {mn('plus2s','no_knowledge'):.1f}), reward λ = 8 "
       f"({mn('nominal','reward_lam8'):.1f} → {mn('plus2s','reward_lam8'):.1f}), the narrative-inferred 16 s "
       f"rule ({mn('nominal','narrative_16s_rule'):.1f} → {mn('plus2s','narrative_16s_rule'):.1f}), the tuned "
       f"18 s constant ({mn('nominal','tuned_constant_18'):.1f} → {mn('plus2s','tuned_constant_18'):.1f}), the "
       f"deployed probe-calibrated shield ({mn('nominal','deployed_probe_shield'):.1f} → "
       f"{mn('plus2s','deployed_probe_shield'):.1f}), and the per-attempt oracle "
       f"({mn('nominal','oracle'):.1f} → {mn('plus2s','oracle'):.1f}). Reward injection ends up *below* no "
       f"knowledge, the narrative rule loses {mn('nominal','narrative_16s_rule') - mn('plus2s','narrative_16s_rule'):.1f} pp, and only the "
       f"re-measurable references stay where they started.")
t = t[:i] + CAP + t[j:]
done.append("fig8-caption")

# ---- VI-C ladder sentence ------------------------------------------------
old = ("Under +2 s of acquisition drift, the λ = 8 policies fall from 84.4% to 55.4%—to the level of policies "
       "with no knowledge at all on the identical drift ladder (54.6%; Section VI-D and Fig. 8).")
new = (f"Under +2 s of acquisition drift, the λ = 8 policies fall from {mn('nominal','reward_lam8'):.1f}% to "
       f"{mn('plus2s','reward_lam8'):.1f}%—*below* the level of policies with no knowledge at all on the "
       f"identical ladder ({mn('plus2s','no_knowledge'):.1f}%; Section VI-D and Fig. 8). A penalty trained on "
       f"the nominal requirement actively hurts once the requirement moves.")
if t.count(old) != 1:
    raise SystemExit(f"ladder sentence found {t.count(old)}")
t = t.replace(old, new, 1)
done.append("ladder-sentence")

p.write_text(t, encoding="utf-8")
print("applied:", done)
