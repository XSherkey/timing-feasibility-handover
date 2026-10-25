"""R4 (v22) part 6: fix the VI-B values/format and replace the stale failure-attribution paragraph."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "almond-repro"
D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"
h = json.loads((ROOT / "results" / "routeA_r3" / "headline_consistent" / "summary.json").read_text(encoding="utf-8"))
A = h["arms"]
m = lambda k: A[k]["summary"]["mean"]
s = lambda k: A[k]["summary"]["sd"]
c = lambda k, key: 100.0 * A[k]["causes"].get(key, 0.0)

p = D / "paper_en.md"
t = p.read_text(encoding="utf-8")
done = []

# ---- waterfall sentence, two-decimal for the shielded arms ---------------
old = ("The hand-crafted PPO-MLP baseline (reward only) reaches 68.4% ± 17.6% polar success. Injecting the same "
       "knowledge as a reward penalty, at its best coefficient λ = 8, reaches 82.9% ± 6.5%. Injecting the same "
       "knowledge as a decision shield on the *baseline's* policies reaches 91.8% ± 1.1%. The **mined-rule "
       "campaign arm** (the full-system policies with the mined 16 s rule and no margin) reaches 92.4% ± 0.07%, "
       "and the **tuned constant** with no learning at all (highest-elevation candidate, fixed 18 s lead) "
       "reaches 93.3%. For reference the deployed probe-calibrated algorithm (τ_used = 18 s) is 93.36% ± 0.05%.")
new = (f"The hand-crafted PPO-MLP baseline (reward only) reaches {m('ppomlp_none'):.1f}% ± {s('ppomlp_none'):.1f}% "
       f"polar success. Injecting the same knowledge as a reward penalty, at its best coefficient λ = 8, reaches "
       f"{m('lam8'):.1f}% ± {s('lam8'):.1f}%. Injecting the same knowledge as a decision shield on the "
       f"*baseline's* policies reaches {m('ppomlp_rule16'):.2f}% ± {s('ppomlp_rule16'):.2f}%. The **mined-rule "
       f"campaign arm** (the full-system policies with the mined 16 s rule and no margin) reaches "
       f"{m('almond_rule16'):.2f}% ± {s('almond_rule16'):.2f}%, and the **tuned constant** with no learning at "
       f"all (highest-elevation candidate, fixed 18 s lead) reaches {m('maxel18'):.2f}%. For reference the "
       f"deployed probe-calibrated algorithm (τ_used = 18 s) is {m('almond_rule18'):.2f}% ± {s('almond_rule18'):.2f}%.")
if t.count(old) != 1:
    raise SystemExit(f"waterfall sentence found {t.count(old)}")
t = t.replace(old, new, 1)
done.append("waterfall")

# ---- failure attribution --------------------------------------------------
old = ("The failure attribution confirms the mechanism (Table II). Late handovers are the only failure class that "
       "moves materially across arms: 22.1% of polar attempts for the reward-only baseline, 14.8% for an "
       "identical-architecture ablation that never mines knowledge, 0.6% for the mined-rule campaign arm. Window "
       "and route failures barely move (≈2–4% throughout); the shield trades a fraction of window violations for "
       "the late handovers it removes, exactly as Eq. (3) predicts.")
new = (f"The failure attribution confirms the mechanism (Table II). Late handovers are the only failure class that "
       f"moves materially across arms: {c('ppomlp_none','late_handover'):.1f}% of polar attempts for the "
       f"reward-only baseline, {c('noforensics_none','late_handover'):.1f}% for an identical-architecture "
       f"ablation that never mines knowledge, {c('almond_rule16','late_handover'):.1f}% for the mined-rule "
       f"campaign arm. Window and route failures stay within "
       f"{c('almond_rule16','window_exceeded'):.1f}–{c('ppomlp_none','no_route'):.1f}% in every row; the shield "
       f"trades a fraction of window violations ({c('ppomlp_none','window_exceeded'):.1f}% → "
       f"{c('almond_rule16','window_exceeded'):.1f}%) for the late handovers it removes, exactly as Eq. (3) "
       f"predicts.")
if t.count(old) != 1:
    raise SystemExit(f"failure paragraph found {t.count(old)}")
t = t.replace(old, new, 1)
done.append("failure")

# ---- threshold ledger: the 93.6% label -----------------------------------
old = "**mined-rule campaign arm** (τ∗ = 16 s, no margin; the 93.6% figure)"
new = f"**mined-rule campaign arm** (τ∗ = 16 s, no margin; the {m('almond_rule16'):.2f}% figure)"
if t.count(old) == 1:
    t = t.replace(old, new, 1)
    done.append("ledger-label")

p.write_text(t, encoding="utf-8")
print("applied:", done)
