"""R4 (v25) final: threshold ledger values, Table II note, and the stale plateau/margin citations."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "almond-repro"
D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"
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


# ledger: three arm descriptions
rep(f"**deployed probe-calibrated algorithm** (τ_used = 18 s; 93.31% at nominal physics), **tuned constant** (18 s lead, no learning; 94.0%) and **oracle shield** (per-attempt realized requirement; 93.31%).",
    f"**deployed probe-calibrated algorithm** (τ_used = 18 s; {m('almond_rule18'):.2f}% at nominal physics), "
    f"**tuned constant** (18 s lead, no learning; {m('maxel18'):.2f}%) and **oracle shield** (per-attempt "
    f"realized requirement; {m('oracle'):.2f}%).", "ledger-names")
rep("| Tuned constant 94.0% (Fig. 5, bar 5) |",
    f"| Tuned constant {m('maxel18'):.2f}% (Fig. 5, bar 5) |", "ledger-row")

# Table II note -> unified-protocol note
old_note_start = t.find("*Note.* The 0.6% late share here")
if old_note_start > 0:
    old_note_end = t.find("\n\n", old_note_start)
    new_note = ("*Note.* These shares and the HSR column come from the same ten runs as Fig. 5 and the "
                "evaluation row of Table VIII: campaign policies, traffic seed 0, identical episodes. The "
                "late-handover share is the class the constraint removes; window and route failures move by "
                "less than a point between the best and worst arm.")
    t = t[:old_note_start] + new_note + t[old_note_end:]
    done.append("table2-note")

# factorial-labelled sentences: make the protocol explicit
rep("Measured, the deployed τ = 18 s arm reaches 93.31% ± 0.26 (per-seed span 1.07 pp, late-handover share 0.00%, n = 10)",
    "Measured on the frozen-policy factorial, the deployed τ = 18 s arm reaches 93.31% ± 0.26 (per-seed span "
    "1.07 pp, late-handover share 0.00%, n = 10)", "factorial-label-1")
rep("The deployed τ = 18 s arm reaches 93.31 ± 0.26 with late share 0.00%, and it sits *above*",
    "The deployed τ = 18 s arm reaches 93.31 ± 0.26 (factorial) with late share 0.00%, and it sits *above*",
    "factorial-label-2")

p.write_text(t, encoding="utf-8")
print("applied:", done)
