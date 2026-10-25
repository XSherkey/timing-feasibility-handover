"""R5 part 3: the last spread numbers, Fig. 2/3 captions, and the strengthened drift conclusion."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "almond-repro"
D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"
fc = json.loads((ROOT / "results" / "routeA_r3" / "factorial_consistent" / "summary.json").read_text(encoding="utf-8"))
lad = json.loads((ROOT / "results" / "routeA_r3" / "ladder_consistent" / "summary.json").read_text(encoding="utf-8"))
A = fc["arms"]
R = lad["regimes"]
mn = lambda reg, arm: R[reg][arm]["summary"]["mean"]
sp = lambda k: (min(A[k]["polar"]), max(A[k]["polar"]))

p = D / "paper_en.md"
t = p.read_text(encoding="utf-8")
done = []


def rep(old, new, label):
    global t
    n = t.count(old)
    if n != 1:
        print(f"  MISS [{label}] {n}: {old[:70]}")
        return
    t = t.replace(old, new, 1)
    done.append(label)


# Fig. 2 caption (figure captions section)
i = t.find("**Fig. 2.** The shield absorbs the timing factor.")
if i > 0:
    j = t.find("\n\n", i)
    CAP = (f"**Fig. 2.** The shield absorbs the timing factor. Ten campaign checkpoints on common episodes, "
           f"traffic seed 0: without the shield they span {sp('none')[0]:.1f}–{sp('none')[1]:.1f}% "
           f"(sd {A['none']['summary']['sd']:.1f}); with τ = 16 s they compress to {sp('rule16')[0]:.1f}–"
           f"{sp('rule16')[1]:.1f}% (sd {A['rule16']['summary']['sd']:.2f}); the deployed τ = 18 s arm spans "
           f"{sp('rule18')[0]:.1f}–{sp('rule18')[1]:.1f}% (sd {A['rule18']['summary']['sd']:.2f}) and sits above "
           f"the τ = 20 s ablation ({sp('rule20')[0]:.1f}–{sp('rule20')[1]:.1f}%, sd "
           f"{A['rule20']['summary']['sd']:.2f}); the per-attempt oracle coincides with τ = 18 s on every seed. "
           f"The per-seed spread collapses from ±{A['none']['summary']['sd']:.1f} to "
           f"±{A['rule18']['summary']['sd']:.2f} pp.")
    t = t[:i] + CAP + t[j:]
    done.append("fig2-caption")

# the in-text sentence with the old spans
rep("across ten checkpoints on identical episodes, and the per-seed spread collapses from 49.8–90.0% to 92.7–93.7% (Fig. 2)",
    f"across ten checkpoints on identical episodes, and the per-seed spread collapses from "
    f"{sp('none')[0]:.1f}–{sp('none')[1]:.1f}% to {sp('rule18')[0]:.1f}–{sp('rule18')[1]:.1f}% (Fig. 2)",
    "intro-spans")

rep("The per-seed spread collapses from ±13.2 to ±0.26 pp.",
    f"The per-seed spread collapses from ±{A['none']['summary']['sd']:.1f} to "
    f"±{A['rule18']['summary']['sd']:.2f} pp.", "spread")

# ---- strengthened conclusion in the abstract ------------------------------
old = ("What does matter is calibration and admission: under 3.2 s of acquisition drift the re-probed "
       "threshold holds 93.2% against 86.0% for a tuned constant")
new = (f"What does matter is calibration and admission: under 2 s of acquisition drift a reward penalty falls "
       f"*below* having no knowledge at all ({mn('plus2s','reward_lam8'):.1f}% against "
       f"{mn('plus2s','no_knowledge'):.1f}%), while under 3.2 s of drift the re-probed threshold holds 93.2% "
       f"against 86.0% for a tuned constant")
if t.count(old) != 1:
    print("  abstract-strengthen MISS", t.count(old))
else:
    t = t.replace(old, new, 1)
    done.append("abstract-strengthen")

# ---- conclusion -----------------------------------------------------------
old = ("What remains—and what this paper contributes—is the machinery around the constraint")
new = ("Two measurements sharpen the point. A reward penalty trained on the nominal requirement does not merely "
       "fail to transfer: under 2 s of drift it lands *below* the no-knowledge policies it was meant to beat, "
       "because it spends its capacity on a bound that has moved. And the audit gate, not the model, is what "
       "keeps a wrong candidate off the network. What remains—and what this paper contributes—is the machinery "
       "around the constraint")
if t.count(old) == 1:
    t = t.replace(old, new, 1)
    done.append("conclusion-strengthen")
else:
    print("  conclusion MISS", t.count(old))

p.write_text(t, encoding="utf-8")
print("applied:", done)
