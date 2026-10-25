"""Full pre-submission check of v86."""
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

print("\n=== new text present ===")
for probe in ("protected scope", "A_Π", "precision floor", "does not rerun whole episodes",
              "empirical transfer", "competing failure", "finite-sample statement",
              "25.6–28.2 pp", "not the mined-rule campaign arm"):
    print(f"  {t.count(probe):2d}  {probe}")

print("\n=== leftovers ===")
for bad in ("intent-independent", "P_{D_Π}", "Table IX", "Table X ", "recoverable from the passive log"):
    n = t.count(bad)
    if n:
        print(f"  !! {bad!r} x{n}")
print("  (none listed above = clean)")

print("\n=== docx metadata ===")
for f in ("Paper_EN_IEEE_v86.docx", "supplementary/supp_en.docx"):
    doc = Document(str(D / f))
    print(" ", f, "| title:", (doc.core_properties.title or "")[:70])

print("\n=== docx text sanity ===")
for f in ("Paper_EN_IEEE_v86.docx", "supplementary/supp_en.docx"):
    xml = zipfile.ZipFile(D / f).read("word/document.xml").decode("utf-8")
    txt = re.sub(r"<[^>]+>", "", xml)
    print(f"  {f}: '**' {txt.count('**')}, 'Table IX' {txt.count('Table IX')}, 'Table X ' {txt.count('Table X ')}")

print("\n=== equation block ===")
i = t.find("P( late under")
print(t[max(0, i - 120):i + 220])
