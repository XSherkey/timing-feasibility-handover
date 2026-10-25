"""R27 part 3: monotone table numbering for the new tables, and move Table V to the supplement."""
from __future__ import annotations

import re
from pathlib import Path

D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"
p = D / "paper_en.md"
supp_path = D / "supplementary" / "supp_en.md"
t = p.read_text(encoding="utf-8")
supp = supp_path.read_text(encoding="utf-8")

# ---- 1. rename the three new tables so numbering follows document order ----
for old, new in (("Table Vb", "Table IXb"), ("Table Vc", "Table IXc"), ("Table Vd", "Table Xb")):
    n = t.count(old)
    t = t.replace(old, new)
    print(f"{old} -> {new}: {n}")

# ---- 2. move Table V (drift response) to the supplement --------------------
i = t.find("**Table V. Drift response")
if i > 0:
    j = t.find("\n\n", t.find("| shielded, τ_used = 18 s", i))
    if j < 0:
        j = t.find("\n\n", t.find("|", t.find("|", i) + 2))
    block = t[i:j]
    t = t[:i] + ("*Drift table.* The per-regime numbers plotted in Fig. 7, with the probe study and its bootstrap, "
                 "are Table H2 of the supplementary material.\n") + t[j:]
    supp = supp.rstrip() + "\n\n## Appendix H2. Drift response\n\n" + block.replace("**Table V.", "**Table H2.") + "\n"
    print("Table V moved to supplement")

t = re.sub(r"\n{3,}", "\n\n", t)
p.write_text(t, encoding="utf-8")
supp_path.write_text(supp, encoding="utf-8")
print("refs to Table V left:", len(re.findall(r"Table V(?![I])", t)))
