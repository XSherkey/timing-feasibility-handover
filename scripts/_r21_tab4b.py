"""R21 part 6: move Table IV with the right anchors, and shrink figures to 3.0 in."""
from __future__ import annotations

import re
from pathlib import Path

D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"
p = D / "paper_en.md"
supp_path = D / "supplementary" / "supp_en.md"
t = p.read_text(encoding="utf-8")
supp = supp_path.read_text(encoding="utf-8")

before = len(re.findall(r"^\*\*Table ", t, flags=re.M))
i = t.find("**Table IV.")
j = t.find("\n\n", t.find("| S |", i))
if i > 0 and j > i:
    block = t[i:j]
    t = t[:i] + "*Grid.* The full λ grid behind Fig. 4 is Table M1 of the supplementary material.\n" + t[j:]
    supp = supp.rstrip() + "\n\n## Appendix M. Dose-response grid\n\n" + block.replace("**Table IV.", "**Table M1.") + "\n"
    print("Table IV moved")
after = len(re.findall(r"^\*\*Table ", t, flags=re.M))
print("main tables:", before, "->", after)

p.write_text(re.sub(r"\n{3,}", "\n\n", t), encoding="utf-8")
supp_path.write_text(supp, encoding="utf-8")

b = D / "build_paper_docx.js"
s = b.read_text(encoding="utf-8")
old = "const widthTwips = IEEE ? COL_WIDTH - 400 : 5800;"
new = "const widthTwips = IEEE ? COL_WIDTH - 620 : 5800;"
if old in s:
    s = s.replace(old, new, 1)
    b.write_text(s, encoding="utf-8")
    print("figures set to ~3.0 in")
