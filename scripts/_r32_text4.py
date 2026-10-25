"""R32 pass 4: plain-text-safe scoped equation, plus the traffic-seed lockbox sentence."""
from __future__ import annotations

import re
from pathlib import Path

D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"
p = D / "paper_en.md"
t = p.read_text(encoding="utf-8")
done = []

# 1. the scoped equation must not carry LaTeX-style subscripts (they would print literally)
old_eq = """P_{D_Π}( late under Π_τ ) = P_{D_Π}( T_z > max(a, τ) )
                      ≤ P_{D_Π}( T_z > τ ) ≤ ε.                              (4)"""
new_eq = """P( late under Π_τ | A_Π ) = P( T_z > max(a, τ) | A_Π )
                        ≤ P( T_z > τ | A_Π ) ≤ ε.                        (4)"""
print("eq block found:", t.count(old_eq))
t = t.replace(old_eq, new_eq, 1)
if t.count("P_{D_Π}") == 0:
    done.append("eq4 plain text")

# 2. traffic-seed lockbox sentence
anchor = "The lockbox supports the *ordering* claims under frozen selection,"
i = t.find(anchor)
if i < 0:
    print("  MISS lockbox anchor")
else:
    ADD = ("The three lockbox instances shift the twin epoch but keep traffic seed 0, so they test time-phase "
           "generalisation rather than traffic generalisation. Repeating the two load-bearing contrasts at traffic "
           "seeds 0, 1 and 2 gives six (instance, traffic) cells in which the deployed arm beats no shield by "
           "25.6–28.2 pp and ties the tuned constant to within 0.03 pp; Table VIII reports the traffic-seed variance "
           "for the evaluation window. What the lockbox does not establish is independence across traffic arrivals or "
           "site mixes, and we do not claim it.\n\n")
    t = t[:i] + ADD + t[i:]
    done.append("traffic lockbox sentence")

t = re.sub(r"\n{3,}", "\n\n", t)
p.write_text(t, encoding="utf-8")
print("edits:", done)
