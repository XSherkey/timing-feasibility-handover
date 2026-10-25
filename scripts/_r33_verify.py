"""Verification sweep for v87."""
from __future__ import annotations

import re
import zipfile
from pathlib import Path

from docx import Document

D = Path(r"../From Human Intent to In-Orbit Action/IEEE_Trans_新版本")
t = (D / "paper_en.md").read_text(encoding="utf-8")
s = (D / "supplementary/supp_en.md").read_text(encoding="utf-8")

print("=== structure ===")
caps = re.findall(r"\*\*Table ([IVX]+)\.", t)
print("tables:", caps)
print("figures:", re.findall(r"\*\*Fig\. (\d)\.\*\*", t))
print("equations:", re.findall(r"\((\d)\)\s*$", t, flags=re.M))
print("unresolved table refs:", [m.group(1) for m in re.finditer(r"Tables? ([IVX]+)(?![A-Za-z])", t) if m.group(1) not in caps])
print("supp tables:", re.findall(r"\*\*Table ([A-Z]\d+[A-Z]?)\.", s))

print("\n=== review-26 items ===")
checks = {
    "abs 'not recoverable' gone": t.count("is therefore not recoverable") == 0,
    "precision-qualified intro": t.count("to the precision a deployment needs") >= 1,
    "remark budget-qualified": t.count("at the budgets we test") == 1,
    "stage-1 precision": t.count("cannot localize the crossing to the 2 s precision") == 1,
    "abstract 'designed to lift'": t.count("designed to lift") == 1,
    "prop1 conditional": t.count("The proposition is a conditional statement") == 1,
    "prop1 no 'corollary applies'": t.count("The corollary applies") == 0,
    "prop4 aligned claim": t.count("It is *not* the unconditional observed late rate") == 1,
    "KM competing scope": t.count("conditional on no competing failure") == 1,
    "cluster sentence": t.count("20 clusters") == 1,
    "attribution in contributions": t.count("and the 16 s mined-rule arm without the margin") >= 1,
    "conclusion attribution": t.count("between the reward-only baseline and the 16 s mined-rule arm") >= 1,
    "eval-window column (no 'row')": t.count("evaluation row") == 0,
    "supp proof conditioned": s.count("Condition on the protected scope A_Π") == 1,
    "supp G2/G3 present": s.count("Table G2.") == 1 and s.count("Table G3.") == 1,
}
for k, v in checks.items():
    print(f"  {'OK ' if v else 'FAIL'}  {k}")

print("\n=== docx sanity ===")
for f in ("Paper_EN_IEEE_v87.docx", "supplementary/supp_en.docx"):
    xml = zipfile.ZipFile(D / f).read("word/document.xml").decode("utf-8")
    txt = re.sub(r"<[^>]+>", "", xml)
    print(f"  {f}: '**' {txt.count('**')}, 'Table IX' {txt.count('Table IX')}, title {(Document(str(D / f)).core_properties.title or '')[:50]}")
