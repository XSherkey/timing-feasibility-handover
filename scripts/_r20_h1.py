"""R20 part 6: put the drift-ladder table back into the supplementary (it was dropped), and audit both files."""
from __future__ import annotations

import re
from pathlib import Path

D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"
supp = D / "supplementary" / "supp_en.md"
s = supp.read_text(encoding="utf-8")

if "Table H1" not in s:
    H1 = """**Table H1. Drift ladder (polar HSR, |lat| ≥ 70°, campaign policies, traffic seed 0, identical episodes, n = 10; the numbers plotted in Fig. 7).** Protocol: three-way, τ re-probed per regime.

| δ | oracle | τ = 18 s (fixed) | 16 s rule (as a shield) | tuned 18 s constant | reward λ = 8 | no knowledge |
|---|---|---|---|---|---|---|
| 0 | 93.36 | 93.36 | 91.60 | 93.33 | 82.93 | 76.31 |
| +2.0 s | 93.36 | 92.42 | 84.79 | 92.39 | 52.00 | 54.64 |
| +3.2 s | 93.36 | 86.01 | 81.25 | 85.98 | 42.67 | 45.85 |
| +4.4 s | 93.36 | 83.47 | 77.49 | 83.56 | 21.02 | 24.16 |
"""
    s = s.rstrip() + "\n\n" + H1
    supp.write_text(s, encoding="utf-8")
    print("Table H1 restored in the supplement")

print("\n--- supplementary headings ---")
for line in s.splitlines():
    if line.startswith("## "):
        print(" ", line)
print("tables in supp:", len(re.findall(r"^\*\*Table ", s, flags=re.M)))
