"""R20 part 2: move the proof sketch, and tighten the IEEE typography."""
from __future__ import annotations

import re
from pathlib import Path

D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"
SUPP = D / "supplementary"

main = D / "paper_en.md"
supp = SUPP / "supp_en.md"
t = main.read_text(encoding="utf-8")
s = supp.read_text(encoding="utf-8")

# ---- 1. the proof sketch that ends with the orphan box -------------------
i = t.find("*Proof sketch.*")
if i > 0:
    j = t.find("□", i)
    k = t.find("\n\n", j)
    block = t[i:k if k > 0 else len(t)]
    t = t[:i] + t[k if k > 0 else len(t):]
    s = s.rstrip() + "\n\n" + block.strip() + "\n"
    print("proof sketch moved")
t = re.sub(r"\n{3,}", "\n\n", t)

# ---- 2. IEEE typography: tighter spacing, smaller table text -------------
b = D / "build_paper_docx.js"
js = b.read_text(encoding="utf-8")

js = js.replace('const para = (children, options = {}) =>\n  new Paragraph({\n    spacing: { after: 120, line: 276 },',
                'const para = (children, options = {}) =>\n  new Paragraph({\n    spacing: IEEE ? { after: 40, line: 236 } : { after: 120, line: 276 },', 1)

# table cell text: 7 pt in IEEE mode
js = js.replace("children: inlineRuns(text, { size: SMALL_SIZE, bold: isHeader }),",
                "children: inlineRuns(text, { size: IEEE ? 14 : SMALL_SIZE, bold: isHeader }),", 1)
# tighter cell margins
js = js.replace("margins: { top: 60, bottom: 60, left: 80, right: 80 },",
                "margins: IEEE ? { top: 25, bottom: 25, left: 55, right: 55 } : { top: 60, bottom: 60, left: 80, right: 80 },", 1)

b.write_text(js, encoding="utf-8")
main.write_text(t, encoding="utf-8")
supp.write_text(s, encoding="utf-8")
print("typography tightened")
