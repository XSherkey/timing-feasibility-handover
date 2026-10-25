"""R10 final: clean the Table XI caption emphasis and check the historical sentence in VI-I."""
from __future__ import annotations

import re
from pathlib import Path

D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"
p = D / "paper_en.md"
t = p.read_text(encoding="utf-8")

old = ("**Table XI. Audit gate over 26 candidates.** Each candidate is labelled *harmful*, *neutral* or *good* by "
       "its measured effect on the evaluation window—a post-hoc audit label, never an input to the gate—while the "
       "gate itself admits only on a validation-window replay gain above 5 pp with a positive lower bound. The "
       "confusion is therefore between an admission decision taken on validation and a label assigned on the "
       "evaluation window, which is what makes it an honest audit rather than a tautology.")
new = ("**Table XI. Audit gate over 26 candidates.** Each candidate is labelled harmful, neutral or good by its "
       "measured effect on the evaluation window—a post-hoc audit label, never an input to the gate—while the "
       "gate itself admits only on a validation-window replay gain above 5 pp with a positive lower bound. The "
       "confusion is therefore between an admission decision taken on validation and a label assigned on the "
       "evaluation window, which is what makes it an honest audit rather than a tautology.")
if t.count(old) == 1:
    t = t.replace(old, new, 1)
    print("EN Table XI caption cleaned")
else:
    print("EN caption count", t.count(old))

i = t.find("The earlier protocol let three choices touch the evaluation window")
if i > 0:
    print("VI-I sentence:", repr(t[i:i + 260]))

p.write_text(t, encoding="utf-8")
