"""R32 pass 6: the last two ambiguous spots (intro sentence and a leftover subscript)."""
from __future__ import annotations

import re
from pathlib import Path

p = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本" / "paper_en.md"
t = p.read_text(encoding="utf-8")

# show the intro sentence first
i = t.find("It does, and the reason is Proposition 3")
print("context:", repr(t[max(0, i - 220):i + 330]))

old = "and the reason is Proposition 3: the constraint enforces feasibility, and feasibility is intent-independent"
new = ("and the reason is that the constraint removes one failure class whatever the objective is; Proposition 3 bounds "
       "that channel under a single deployment distribution, so the cross-intent part is something we test (Section "
       "VI-F) rather than something the bound grants")
print("found:", t.count(old))
t = t.replace(old, new, 1)

t = t.replace("i.e., P_{D_Π}(T_z ≤ τ) ≥ 1 − ε", "i.e., P(T_z ≤ τ | A_Π) ≥ 1 − ε", 1)

t = re.sub(r"\n{3,}", "\n\n", t)
p.write_text(t, encoding="utf-8")
print("intent-independent left:", t.count("intent-independent"))
print("P_{D_Π} left:", t.count("P_{D_Π}"))
