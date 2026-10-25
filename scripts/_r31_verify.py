"""Final pre-submission verification of v85 (main + supplement)."""
from __future__ import annotations

import re
import zipfile
from pathlib import Path

D = Path(r"../From Human Intent to In-Orbit Action/IEEE_Trans_新版本")
t = (D / "paper_en.md").read_text(encoding="utf-8")
s = (D / "supplementary/supp_en.md").read_text(encoding="utf-8")

print("=== main structure ===")
print("tables:", re.findall(r"\*\*Table ([IVX]+)\.", t))
print("figures:", re.findall(r"\*\*Fig\. (\d)\.\*\*", t))
print("equations:", re.findall(r"\((\d)\)\s*$", t, flags=re.M))
inside = t[t.find("## VI."):t.find("## VII.")]
print("VI subsections:", " ".join(re.findall(r"^### ([A-O])\.", inside, flags=re.M)))

caps = re.findall(r"\*\*Table ([IVX]+)\.", t)
bad = [m.group(1) for m in re.finditer(r"Tables? ([IVX]+)(?![A-Za-z])", t) if m.group(1) not in caps]
print("unresolved table refs:", bad)

print("\n=== caption asterisks (must be 4 each) ===")
for name, txt, start in (("V", t, "**Table V."), ("VIII", t, "**Table VIII."),
                         ("H2", s, "**Table H2."), ("J1", s, "**Table J1."),
                         ("D2", s, "**Table D2."), ("M1", s, "**Table M1.")):
    i = txt.find(start)
    j = txt.find("\n\n", i)
    print(f"  {name}: {txt[i:j].count('*')} asterisks")

print("\n=== VI-A protocol paragraph ===")
i = t.find("Tables II and III report archival results")
print(t[i:i + 700])

print("\n=== supplement refs ===")
for pat in ("Tables V and Fig. 8", "of Table X)", "Table V,", "Table IV,"):
    print(f"  {pat!r}: {s.count(pat)}")
print("  AppJ new text:", s.count("Table III, Fig. 8, and Table K1"))
print("  M1 new text:", s.count("arm A0 in Table IV of the main text"))

print("\n=== docx sanity ===")
for f in ("Paper_EN_IEEE_v85.docx", "supplementary/supp_en.docx"):
    doc = zipfile.ZipFile(D / f).read("word/document.xml").decode("utf-8")
    text = re.sub(r"<[^>]+>", "", doc)
    print(f"  {f}: '**' occurrences {text.count('**')}, 'Table X ' {text.count('Table X ')}, 'Table IX' {text.count('Table IX')}")
