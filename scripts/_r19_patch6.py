"""R19 part 6: put 'Abstract—' on the abstract, and hunt down the stray frame."""
from __future__ import annotations

import re
import zipfile
from pathlib import Path

D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"

for name, prefix, first_words in (
    ("paper_en.md", "**Abstract—** ", "Handover reliability in low Earth orbit constellations"),
    ("paper_zh.md", "**摘要——** ", "低轨星座的切换可靠性"),
):
    p = D / name
    t = p.read_text(encoding="utf-8")
    # remove the misplaced prefix
    t = t.replace(prefix + "*Bands.*", "*Bands.*")
    t = t.replace(prefix + "*纬度带。*", "*纬度带。*")
    # put it on the abstract paragraph
    if prefix not in t.split("## Nomenclature")[0] if name == "paper_en.md" else True:
        i = t.find(first_words)
        if i > 0:
            t = t[:i] + prefix + t[i:]
            print(name, "abstract prefix placed")
    p.write_text(t, encoding="utf-8")

# look for borders in the built docx
p = D / "_ieee_test.docx"
z = zipfile.ZipFile(p)
xml = z.read("word/document.xml").decode("utf-8")
print("pBdr:", xml.count("<w:pBdr>"), "| tblBorders:", xml.count("tblBorders"), "| framePr:", xml.count("framePr"))
for tag in ("<w:pBdr>", "framePr"):
    i = xml.find(tag)
    if i > 0:
        print(tag, "->", xml[max(0, i - 200):i + 200].replace("><", ">\n<")[:500])
