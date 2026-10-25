"""Reproduce the reviewer's extraction path: docx -> PDF (Word) -> text (Word), then look for artifacts."""
from __future__ import annotations

import re
import sys
from pathlib import Path

import win32com.client as win32  # type: ignore

D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"
src = D / (sys.argv[1] if len(sys.argv) > 1 else "Paper_EN_v55.docx")
pdf = D / "_word.pdf"
txt = D / "_word_text.txt"

word = win32.DispatchEx("Word.Application")
word.Visible = False
word.DisplayAlerts = 0
try:
    doc = word.Documents.Open(str(src), ReadOnly=True)
    doc.SaveAs(str(pdf), FileFormat=17)  # wdFormatPDF
    doc.Close(False)

    back = word.Documents.Open(str(pdf), ReadOnly=True)
    text = back.Content.Text
    back.Close(False)
finally:
    word.Quit()

txt.write_text(text, encoding="utf-8")
print("extracted chars:", len(text))
checks = ["mmes", "mtimes", "harmf", "harmful", "utes", "uses", "intetr", "intent",
          "&lt;", "&amp;", "a^{*}", "0/+2/+3", "$", "\\Delta", "\\tau"]
for k in checks:
    print(f"{k!r}: {len(re.findall(re.escape(k), text))}")
print()
for pat in ("mmes", "harmf", "intetr", "&lt;", "\\Delta"):
    for m in list(re.finditer(re.escape(pat), text))[:2]:
        print(f"[{pat}]", repr(text[max(0, m.start() - 80):m.start() + 60]))
